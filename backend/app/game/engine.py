import random

from app.game.board import RESOURCE_BY_TERRAIN, Board, Terrain
from app.game.ids import TopologyIndex
from app.game.placement import (
    GameError,
    check_city,
    check_road,
    check_settlement,
    legal_road_spots,
    legal_settlement_spots,
    occupied_vertices,
)
from app.game.state import GameState, Phase, PlayerState

COSTS = {
    "road": {"wood": 1, "brick": 1},
    "settlement": {"wood": 1, "brick": 1, "wheat": 1, "sheep": 1},
    "city": {"wheat": 2, "ore": 3},
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
    return GameState(order=order, players=players, rng=rng)


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

    state.current_index = (state.current_index + 1) % len(state.order)
    state.turn_number += 1
    state.phase = Phase.ROLL


def legal_moves(topology, state: GameState) -> dict:
    index = _index(topology)
    name = state.current_player()
    if state.phase is Phase.SETUP_SETTLEMENT:
        return {"vertices": legal_settlement_spots(index, state, name, setup=True), "edges": []}
    if state.phase is Phase.SETUP_ROAD:
        return {
            "vertices": [],
            "edges": legal_road_spots(index, state, name, setup=True, required_vertex=state.setup_last_vertex),
        }
    if state.phase is Phase.BUILD:
        return {
            "vertices": legal_settlement_spots(index, state, name, setup=False),
            "edges": legal_road_spots(index, state, name, setup=False),
        }
    return {"vertices": [], "edges": []}
