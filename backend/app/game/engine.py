import random

from app.game.board import RESOURCE_BY_TERRAIN, Board, Terrain
from app.game.ids import TopologyIndex
from app.game.largest_army import recompute_largest_army
from app.game.longest_road import recompute_longest_road
from app.game.placement import (
    GameError,
    check_city,
    check_road,
    check_settlement,
    legal_road_spots,
    legal_settlement_spots,
    occupied_vertices,
)
from app.game.state import RESOURCES, GameState, Phase, PlayerState, TradeOffer

COSTS = {
    "road": {"wood": 1, "brick": 1},
    "settlement": {"wood": 1, "brick": 1, "wheat": 1, "sheep": 1},
    "city": {"wheat": 2, "ore": 3},
    "dev_card": {"wheat": 1, "sheep": 1, "ore": 1},
}

DEV_DECK_COMPOSITION = {
    "knight": 14,
    "victory_point": 5,
    "monopoly": 2,
    "road_building": 2,
    "year_of_plenty": 2,
}


def pay(player: PlayerState, cost: dict):
    for resource, amount in cost.items():
        if player.resources.get(resource, 0) < amount:
            raise GameError("insufficient_resources", f"not enough {resource}")
    for resource, amount in cost.items():
        player.resources[resource] -= amount


def _require_phase(state: GameState, *phases):
    if state.phase not in phases:
        raise GameError("wrong_phase", f"not allowed during {state.phase.value}")


def _require_actor(state: GameState, name: str):
    if state.current_player() != name:
        raise GameError("not_your_turn", "it's not your turn")


def new_game(board: Board, player_names: list, seed: int | None = None) -> GameState:
    rng = random.Random(seed)
    order = list(player_names)
    rng.shuffle(order)
    players = {name: PlayerState(name=name) for name in order}

    dev_deck = []
    for card, count in DEV_DECK_COMPOSITION.items():
        dev_deck.extend([card] * count)
    rng.shuffle(dev_deck)

    return GameState(order=order, players=players, rng=rng, dev_deck=dev_deck)


def _index(topology) -> TopologyIndex:
    return TopologyIndex(topology)


def _hex_by_coord(board: Board) -> dict:
    return {h.coord: h for h in board.hexes}


def _grant_setup_resources(board: Board, index: TopologyIndex, state: GameState, name: str, vid: str):
    hex_by_coord = _hex_by_coord(board)
    for hex_coord in (h for h in hex_by_coord if vid in index.hex_vertices.get(h, [])):
        hex_ = hex_by_coord[hex_coord]
        if hex_.terrain is Terrain.DESERT:
            continue
        state.players[name].resources[RESOURCE_BY_TERRAIN[hex_.terrain]] += 1


def setup_settlement(board: Board, topology, state: GameState, name: str, vid: str):
    _require_phase(state, Phase.SETUP_SETTLEMENT)
    _require_actor(state, name)
    index = _index(topology)
    check_settlement(index, state, name, vid, setup=True)

    state.players[name].settlements.add(vid)
    state.players[name].settlements_left -= 1
    state.setup_last_vertex = vid
    state.phase = Phase.SETUP_ROAD
    recompute_longest_road(index, state)


def setup_road(board: Board, topology, state: GameState, name: str, eid: str):
    _require_phase(state, Phase.SETUP_ROAD)
    _require_actor(state, name)
    index = _index(topology)
    check_road(index, state, name, eid, setup=True, required_vertex=state.setup_last_vertex)

    state.players[name].roads.add(eid)
    state.players[name].roads_left -= 1

    n = len(state.order)
    if state.setup_index >= n:
        _grant_setup_resources(board, index, state, name, state.setup_last_vertex)

    state.setup_index += 1
    state.setup_last_vertex = None

    if state.setup_index >= 2 * n:
        state.phase = Phase.ROLL
        state.current_index = 0
    else:
        state.phase = Phase.SETUP_SETTLEMENT

    recompute_longest_road(index, state)


def _distribute(board: Board, index: TopologyIndex, state: GameState, total: int):
    occ = occupied_vertices(state)
    hex_by_coord = _hex_by_coord(board)
    for hex_coord, vids in index.hex_vertices.items():
        hex_ = hex_by_coord[hex_coord]
        if hex_.number != total or hex_coord == board.robber:
            continue
        resource = RESOURCE_BY_TERRAIN[hex_.terrain]
        for vid in vids:
            owner = occ.get(vid)
            if owner is None:
                continue
            amount = 2 if vid in state.players[owner].cities else 1
            state.players[owner].resources[resource] += amount


def roll(board: Board, topology, state: GameState, name: str) -> tuple:
    _require_phase(state, Phase.ROLL)
    _require_actor(state, name)
    index = _index(topology)

    state.trade = None
    d1, d2 = state.rng.randint(1, 6), state.rng.randint(1, 6)
    state.last_roll = (d1, d2)
    total = d1 + d2

    if total == 7:
        state.pending_discards = {
            n: p.hand_size() // 2 for n, p in state.players.items() if p.hand_size() > 7
        }
        state.phase = Phase.DISCARD if state.pending_discards else Phase.MOVE_ROBBER
    else:
        _distribute(board, index, state, total)
        state.phase = Phase.BUILD

    return d1, d2


def discard(state: GameState, name: str, resources: dict):
    _require_phase(state, Phase.DISCARD)
    if name not in state.pending_discards:
        raise GameError("not_your_turn", "you have nothing to discard")

    required = state.pending_discards[name]
    total = sum(resources.values())
    if total != required:
        raise GameError("invalid_discard", f"must discard exactly {required} cards")

    player = state.players[name]
    for resource, amount in resources.items():
        if amount < 0 or player.resources.get(resource, 0) < amount:
            raise GameError("invalid_discard", f"you don't have {amount} {resource}")

    for resource, amount in resources.items():
        player.resources[resource] -= amount

    del state.pending_discards[name]
    if not state.pending_discards:
        state.phase = Phase.MOVE_ROBBER


def move_robber(board: Board, topology, state: GameState, name: str, hex_coord, steal_from: str | None):
    _require_phase(state, Phase.MOVE_ROBBER)
    _require_actor(state, name)
    index = _index(topology)

    board_hexes = {h.coord for h in board.hexes}
    if hex_coord not in board_hexes:
        raise GameError("invalid_hex", "unknown hex")
    if hex_coord == board.robber:
        raise GameError("illegal_placement", "the robber must move to a different hex")

    occ = occupied_vertices(state)
    candidates = {
        occ[vid]
        for vid in index.hex_vertices.get(hex_coord, [])
        if vid in occ and occ[vid] != name and state.players[occ[vid]].hand_size() > 0
    }

    if candidates:
        if steal_from not in candidates:
            raise GameError("invalid_target", "must steal from an adjacent player with cards")
    elif steal_from is not None:
        raise GameError("invalid_target", "no one to steal from")

    board.robber = hex_coord

    if steal_from:
        victim = state.players[steal_from]
        pool = [r for r, n in victim.resources.items() for _ in range(n)]
        stolen = state.rng.choice(pool)
        victim.resources[stolen] -= 1
        state.players[name].resources[stolen] += 1

    state.phase = Phase.BUILD


def build_settlement(board: Board, topology, state: GameState, name: str, vid: str):
    _require_phase(state, Phase.BUILD)
    _require_actor(state, name)
    index = _index(topology)
    check_settlement(index, state, name, vid, setup=False)

    player = state.players[name]
    if player.settlements_left <= 0:
        raise GameError("no_pieces_left", "no settlements left to place")

    pay(player, COSTS["settlement"])
    player.settlements.add(vid)
    player.settlements_left -= 1
    recompute_longest_road(index, state)


def build_road(board: Board, topology, state: GameState, name: str, eid: str):
    _require_phase(state, Phase.BUILD)
    _require_actor(state, name)
    index = _index(topology)
    check_road(index, state, name, eid, setup=False)

    player = state.players[name]
    if player.roads_left <= 0:
        raise GameError("no_pieces_left", "no roads left to place")

    pay(player, COSTS["road"])
    player.roads.add(eid)
    player.roads_left -= 1
    recompute_longest_road(index, state)


def build_city(board: Board, topology, state: GameState, name: str, vid: str):
    _require_phase(state, Phase.BUILD)
    _require_actor(state, name)
    index = _index(topology)
    check_city(index, state, name, vid)

    player = state.players[name]
    if player.cities_left <= 0:
        raise GameError("no_pieces_left", "no cities left to place")

    pay(player, COSTS["city"])
    player.settlements.discard(vid)
    player.settlements_left += 1
    player.cities.add(vid)
    player.cities_left -= 1


def end_turn(board: Board, topology, state: GameState, name: str):
    _require_phase(state, Phase.BUILD)
    _require_actor(state, name)

    player = state.players[name]
    for card, count in player.dev_new.items():
        if count:
            player.dev_cards[card] += count
            player.dev_new[card] = 0

    state.trade = None
    state.current_index = (state.current_index + 1) % len(state.order)
    state.turn_number += 1
    state.phase = Phase.ROLL


def port_ratios(board: Board, state: GameState, name: str) -> dict:
    ratios = {r: 4 for r in RESOURCES}
    owned = state.players[name].settlements | state.players[name].cities
    for port in board.ports:
        if not (set(port.vertices) & owned):
            continue
        if port.resource is None:
            for r in ratios:
                ratios[r] = min(ratios[r], 3)
        else:
            ratios[port.resource] = min(ratios[port.resource], 2)
    return ratios


def bank_trade(board: Board, topology, state: GameState, name: str, give: str, want: str, count: int = 1):
    _require_phase(state, Phase.BUILD)
    _require_actor(state, name)

    if give not in RESOURCES or want not in RESOURCES:
        raise GameError("invalid_resource", "unknown resource")
    if give == want:
        raise GameError("invalid_trade", "give and want must differ")
    if not isinstance(count, int) or count < 1:
        raise GameError("invalid_trade", "count must be a positive integer")

    ratio = port_ratios(board, state, name)[give]
    player = state.players[name]
    cost = ratio * count
    if player.resources.get(give, 0) < cost:
        raise GameError("insufficient_resources", f"not enough {give}")

    player.resources[give] -= cost
    player.resources[want] += count


def _validate_trade_sides(give: dict, want: dict):
    if not give or not want:
        raise GameError("invalid_trade", "give and want cannot be empty")
    for side in (give, want):
        for resource, amount in side.items():
            if resource not in RESOURCES:
                raise GameError("invalid_trade", "unknown resource")
            if not isinstance(amount, int) or amount < 1:
                raise GameError("invalid_trade", "amounts must be positive integers")
    if set(give) & set(want):
        raise GameError("invalid_trade", "a resource cannot be on both sides")


def _has_resources(player: PlayerState, side: dict) -> bool:
    return all(player.resources.get(r, 0) >= amount for r, amount in side.items())


def trade_propose(state: GameState, name: str, give: dict, want: dict, target: str | None = None):
    _require_phase(state, Phase.BUILD)
    _require_actor(state, name)
    _validate_trade_sides(give, want)

    if target is not None:
        if target == name:
            raise GameError("invalid_trade", "cannot trade with yourself")
        if target not in state.players:
            raise GameError("invalid_trade", "unknown target player")
    if not _has_resources(state.players[name], give):
        raise GameError("insufficient_resources", "you don't have the offered resources")

    state.trade = TradeOffer(
        offer_id=state.next_offer_id, proposer=name, give=dict(give), want=dict(want), target=target
    )
    state.next_offer_id += 1


def trade_counter(state: GameState, name: str, give: dict, want: dict):
    offer = state.trade
    if offer is None:
        raise GameError("no_active_trade", "there is no active trade offer")
    if name == offer.proposer:
        raise GameError("invalid_trade", "you cannot counter your own offer")
    if offer.target is not None and offer.target != name:
        raise GameError("not_eligible", "you are not part of this trade")
    _validate_trade_sides(give, want)
    if not _has_resources(state.players[name], give):
        raise GameError("insufficient_resources", "you don't have the offered resources")

    state.trade = TradeOffer(
        offer_id=state.next_offer_id, proposer=name, give=dict(give), want=dict(want), target=offer.proposer
    )
    state.next_offer_id += 1


def trade_accept(state: GameState, name: str):
    offer = state.trade
    if offer is None:
        raise GameError("no_active_trade", "there is no active trade offer")
    if name == offer.proposer:
        raise GameError("invalid_trade", "you cannot accept your own offer")
    if offer.target is not None and offer.target != name:
        raise GameError("not_eligible", "you are not the target of this trade")
    if offer.proposer != state.current_player() and name != state.current_player():
        raise GameError("not_eligible", "one side of the trade must be the current player")

    proposer = state.players[offer.proposer]
    acceptor = state.players[name]
    if not _has_resources(proposer, offer.give) or not _has_resources(acceptor, offer.want):
        state.trade = None
        raise GameError("insufficient_resources", "a trader no longer has the required resources")

    for resource, amount in offer.give.items():
        proposer.resources[resource] -= amount
        acceptor.resources[resource] += amount
    for resource, amount in offer.want.items():
        acceptor.resources[resource] -= amount
        proposer.resources[resource] += amount

    state.trade = None


def trade_reject(state: GameState, name: str):
    offer = state.trade
    if offer is None:
        raise GameError("no_active_trade", "there is no active trade offer")
    if name == offer.proposer:
        raise GameError("invalid_trade", "use trade_cancel to withdraw your own offer")
    if offer.target is not None:
        if offer.target != name:
            raise GameError("not_eligible", "you are not part of this trade")
        state.trade = None
        return

    if name not in state.players:
        raise GameError("not_eligible", "unknown player")
    offer.rejected_by.add(name)
    eligible = set(state.players) - {offer.proposer}
    if eligible <= offer.rejected_by:
        state.trade = None


def trade_cancel(state: GameState, name: str):
    offer = state.trade
    if offer is None:
        raise GameError("no_active_trade", "there is no active trade offer")
    if name != offer.proposer:
        raise GameError("not_eligible", "only the proposer can cancel this trade")
    state.trade = None


def buy_dev_card(board: Board, topology, state: GameState, name: str):
    _require_phase(state, Phase.BUILD)
    _require_actor(state, name)
    if not state.dev_deck:
        raise GameError("deck_empty", "no development cards left")

    player = state.players[name]
    pay(player, COSTS["dev_card"])
    card = state.dev_deck.pop()
    player.dev_new[card] += 1


def play_knight(board: Board, topology, state: GameState, name: str, hex_coord, steal_from: str | None):
    _require_phase(state, Phase.BUILD)
    _require_actor(state, name)

    player = state.players[name]
    if player.dev_cards.get("knight", 0) <= 0:
        raise GameError("no_such_card", "you have no knight card to play")

    state.phase = Phase.MOVE_ROBBER
    try:
        move_robber(board, topology, state, name, hex_coord, steal_from)
    except GameError:
        state.phase = Phase.BUILD
        raise

    player.dev_cards["knight"] -= 1
    player.dev_played["knight"] += 1
    player.knights_played += 1
    recompute_largest_army(state)


def play_monopoly(board: Board, topology, state: GameState, name: str, resource: str):
    _require_phase(state, Phase.BUILD)
    _require_actor(state, name)

    player = state.players[name]
    if player.dev_cards.get("monopoly", 0) <= 0:
        raise GameError("no_such_card", "you have no monopoly card to play")
    if resource not in RESOURCES:
        raise GameError("invalid_resource", "unknown resource")

    for other_name, other in state.players.items():
        if other_name == name:
            continue
        taken = other.resources.get(resource, 0)
        other.resources[resource] = 0
        player.resources[resource] += taken

    player.dev_cards["monopoly"] -= 1
    player.dev_played["monopoly"] += 1


def play_year_of_plenty(board: Board, topology, state: GameState, name: str, resources: list):
    _require_phase(state, Phase.BUILD)
    _require_actor(state, name)

    player = state.players[name]
    if player.dev_cards.get("year_of_plenty", 0) <= 0:
        raise GameError("no_such_card", "you have no year of plenty card to play")
    if not isinstance(resources, list) or len(resources) != 2:
        raise GameError("invalid_resource", "must take exactly 2 resources")
    for r in resources:
        if r not in RESOURCES:
            raise GameError("invalid_resource", "unknown resource")

    for r in resources:
        player.resources[r] += 1

    player.dev_cards["year_of_plenty"] -= 1
    player.dev_played["year_of_plenty"] += 1


def play_road_building(board: Board, topology, state: GameState, name: str, edges: list):
    _require_phase(state, Phase.BUILD)
    _require_actor(state, name)
    index = _index(topology)

    player = state.players[name]
    if player.dev_cards.get("road_building", 0) <= 0:
        raise GameError("no_such_card", "you have no road building card to play")
    if not isinstance(edges, list) or not 0 <= len(edges) <= 2:
        raise GameError("invalid_action", "must place at most 2 roads")
    if player.roads_left <= 0:
        raise GameError("no_pieces_left", "no roads left to place")

    if not edges:
        if legal_road_spots(index, state, name, setup=False):
            raise GameError("invalid_action", "you must place a road if you have a legal spot")
    else:
        saved_roads = set(player.roads)
        saved_left = player.roads_left
        try:
            for eid in edges:
                if player.roads_left <= 0:
                    raise GameError("no_pieces_left", "no roads left to place")
                check_road(index, state, name, eid, setup=False)
                player.roads.add(eid)
                player.roads_left -= 1
        except GameError:
            player.roads = saved_roads
            player.roads_left = saved_left
            raise

        if len(edges) < 2 and player.roads_left > 0 and legal_road_spots(index, state, name, setup=False):
            player.roads = saved_roads
            player.roads_left = saved_left
            raise GameError("invalid_action", "must place two roads")

    player.dev_cards["road_building"] -= 1
    player.dev_played["road_building"] += 1
    recompute_longest_road(index, state)


def legal_moves(board: Board, topology, state: GameState) -> dict:
    index = _index(topology)
    name = state.current_player()
    bank_ratios = port_ratios(board, state, name)
    if state.phase is Phase.SETUP_SETTLEMENT:
        return {
            "vertices": legal_settlement_spots(index, state, name, setup=True),
            "edges": [],
            "bank_ratios": bank_ratios,
        }
    if state.phase is Phase.SETUP_ROAD:
        return {
            "vertices": [],
            "edges": legal_road_spots(index, state, name, setup=True, required_vertex=state.setup_last_vertex),
            "bank_ratios": bank_ratios,
        }
    if state.phase is Phase.BUILD:
        return {
            "vertices": legal_settlement_spots(index, state, name, setup=False),
            "edges": legal_road_spots(index, state, name, setup=False),
            "bank_ratios": bank_ratios,
        }
    return {"vertices": [], "edges": [], "bank_ratios": bank_ratios}


WIN_VICTORY_POINTS = 10


def check_win(state: GameState) -> str | None:
    if state.winner is not None:
        return state.winner

    for name in state.order:
        if state.true_victory_points(name) >= WIN_VICTORY_POINTS:
            state.winner = name
            state.phase = Phase.GAME_OVER
            state.trade = None
            return name

    return None
