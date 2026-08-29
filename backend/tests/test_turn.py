import random

import pytest

from app.game import engine
from app.game.board import RESOURCE_BY_TERRAIN, Terrain, generate_board, topology_for
from app.game.ids import TopologyIndex, edge_id, vertex_id
from app.game.placement import GameError
from app.game.state import GameState, Phase, PlayerState


class FixedRNG:
    def __init__(self, values):
        self.values = list(values)

    def randint(self, a, b):
        return self.values.pop(0)

    def choice(self, seq):
        return seq[0]

    def shuffle(self, seq):
        pass


def make_ready_state(names, phase=Phase.ROLL):
    players = {n: PlayerState(name=n) for n in names}
    return GameState(order=list(names), players=players, rng=random.Random(0), phase=phase)


@pytest.fixture
def board_and_topo():
    board = generate_board(2, seed=3)
    topology = topology_for(board)
    return board, topology


def test_roll_outside_roll_phase_rejected(board_and_topo):
    board, topology = board_and_topo
    state = make_ready_state(["A", "B"], phase=Phase.BUILD)
    with pytest.raises(GameError) as exc:
        engine.roll(board, topology, state, "A")
    assert exc.value.code == "wrong_phase"


def test_non_seven_distributes_and_enters_build(board_and_topo):
    board, topology = board_and_topo
    index = TopologyIndex(topology)
    state = make_ready_state(["A", "B"])
    state.rng = FixedRNG([2, 3])

    target_hex = next(h for h in board.hexes if h.number == 5 and h.coord != board.robber)
    vid = index.hex_vertices[target_hex.coord][0]
    state.players["A"].settlements.add(vid)

    engine.roll(board, topology, state, state.current_player())
    assert state.phase is Phase.BUILD
    assert state.players["A"].resources[RESOURCE_BY_TERRAIN[target_hex.terrain]] == 1


def test_distribution_pays_settlement_one_city_two(board_and_topo):
    board, topology = board_and_topo
    index = TopologyIndex(topology)
    state = make_ready_state(["A", "B"])

    target_hex = next(h for h in board.hexes if h.terrain is not Terrain.DESERT and h.coord != board.robber)
    vid = index.hex_vertices[target_hex.coord][0]
    other_vid = index.hex_vertices[target_hex.coord][1]
    state.players["A"].settlements.add(vid)
    state.players["B"].cities.add(other_vid)

    engine._distribute(board, index, state, target_hex.number)
    resource = RESOURCE_BY_TERRAIN[target_hex.terrain]
    assert state.players["A"].resources[resource] == 1
    assert state.players["B"].resources[resource] == 2


def test_robber_hex_pays_nobody(board_and_topo):
    board, topology = board_and_topo
    index = TopologyIndex(topology)
    state = make_ready_state(["A", "B"])

    numbered_hex = next(h for h in board.hexes if h.terrain is not Terrain.DESERT)
    board.robber = numbered_hex.coord
    vid = index.hex_vertices[numbered_hex.coord][0]
    state.players["A"].settlements.add(vid)

    engine._distribute(board, index, state, numbered_hex.number)
    assert state.players["A"].resources[RESOURCE_BY_TERRAIN[numbered_hex.terrain]] == 0


def test_seven_triggers_discard_when_a_hand_exceeds_seven(board_and_topo):
    board, topology = board_and_topo
    state = make_ready_state(["A", "B"])
    state.rng = FixedRNG([3, 4])
    state.players["A"].resources["wood"] = 8

    d1, d2 = engine.roll(board, topology, state, state.current_player())
    assert (d1, d2) == (3, 4)
    assert state.phase is Phase.DISCARD
    assert state.pending_discards == {"A": 4}


def test_seven_with_no_big_hands_skips_straight_to_move_robber(board_and_topo):
    board, topology = board_and_topo
    state = make_ready_state(["A", "B"])
    state.rng = FixedRNG([3, 4])

    engine.roll(board, topology, state, state.current_player())
    assert state.phase is Phase.MOVE_ROBBER


@pytest.mark.parametrize("hand,expected", [(8, 4), (9, 4), (12, 6)])
def test_discard_required_count_is_floor_half(hand, expected):
    state = make_ready_state(["A", "B"], phase=Phase.DISCARD)
    state.players["A"].resources["wood"] = hand
    state.pending_discards = {"A": hand // 2}

    engine.discard(state, "A", {"wood": expected})
    assert state.players["A"].resources["wood"] == hand - expected
    assert "A" not in state.pending_discards


def test_discard_wrong_count_rejected():
    state = make_ready_state(["A", "B"], phase=Phase.DISCARD)
    state.players["A"].resources["wood"] = 8
    state.pending_discards = {"A": 4}
    with pytest.raises(GameError) as exc:
        engine.discard(state, "A", {"wood": 3})
    assert exc.value.code == "invalid_discard"


def test_discard_more_than_held_rejected():
    state = make_ready_state(["A", "B"], phase=Phase.DISCARD)
    state.players["A"].resources.update({"wood": 2, "brick": 2})
    state.pending_discards = {"A": 4}
    with pytest.raises(GameError) as exc:
        engine.discard(state, "A", {"wood": 4})
    assert exc.value.code == "invalid_discard"


def test_non_pending_player_cannot_discard():
    state = make_ready_state(["A", "B"], phase=Phase.DISCARD)
    state.pending_discards = {"A": 2}
    with pytest.raises(GameError) as exc:
        engine.discard(state, "B", {})
    assert exc.value.code == "not_your_turn"


def test_robber_must_move_and_steal_only_from_valid_target(board_and_topo):
    board, topology = board_and_topo
    index = TopologyIndex(topology)
    state = make_ready_state(["A", "B"], phase=Phase.MOVE_ROBBER)

    target_hex = next(h for h in board.hexes if h.coord != board.robber)
    vid = index.hex_vertices[target_hex.coord][0]
    state.players["B"].settlements.add(vid)
    state.players["B"].resources["wood"] = 1

    with pytest.raises(GameError) as exc:
        engine.move_robber(board, topology, state, "A", board.robber, None)
    assert exc.value.code == "illegal_placement"

    with pytest.raises(GameError) as exc:
        engine.move_robber(board, topology, state, "A", target_hex.coord, None)
    assert exc.value.code == "invalid_target"

    engine.move_robber(board, topology, state, "A", target_hex.coord, "B")
    assert board.robber == target_hex.coord
    assert state.players["A"].hand_size() == 1
    assert state.players["B"].hand_size() == 0
    assert state.phase is Phase.BUILD


def test_robber_with_no_candidates_requires_no_steal(board_and_topo):
    board, topology = board_and_topo
    state = make_ready_state(["A", "B"], phase=Phase.MOVE_ROBBER)
    empty_hex = next(h for h in board.hexes if h.coord != board.robber)

    engine.move_robber(board, topology, state, "A", empty_hex.coord, None)
    assert state.phase is Phase.BUILD


def test_build_settlement_deducts_cost_and_rejects_when_short(board_and_topo):
    board, topology = board_and_topo
    state = make_ready_state(["A", "B"], phase=Phase.BUILD)
    v0 = topology.vertices[0]
    vid = vertex_id(v0)
    state.players["A"].roads.add(edge_id(topology.vertex_edges[v0][0]))

    with pytest.raises(GameError) as exc:
        engine.build_settlement(board, topology, state, "A", vid)
    assert exc.value.code == "insufficient_resources"

    state.players["A"].resources.update({"wood": 1, "brick": 1, "wheat": 1, "sheep": 1})
    engine.build_settlement(board, topology, state, "A", vid)
    assert vid in state.players["A"].settlements
    assert state.players["A"].resources["wood"] == 0
    assert state.players["A"].settlements_left == 4


def test_build_road_deducts_cost(board_and_topo):
    board, topology = board_and_topo
    state = make_ready_state(["A", "B"], phase=Phase.BUILD)
    v0 = topology.vertices[0]
    state.players["A"].settlements.add(vertex_id(v0))
    e0 = topology.vertex_edges[v0][0]

    state.players["A"].resources.update({"wood": 1, "brick": 1})
    engine.build_road(board, topology, state, "A", edge_id(e0))
    assert edge_id(e0) in state.players["A"].roads
    assert state.players["A"].roads_left == 14


def test_build_city_upgrades_settlement_in_place(board_and_topo):
    board, topology = board_and_topo
    state = make_ready_state(["A", "B"], phase=Phase.BUILD)
    v0 = vertex_id(topology.vertices[0])
    state.players["A"].settlements.add(v0)
    state.players["A"].resources.update({"wheat": 2, "ore": 3})

    engine.build_city(board, topology, state, "A", v0)
    assert v0 not in state.players["A"].settlements
    assert v0 in state.players["A"].cities
    assert state.players["A"].settlements_left == 6
    assert state.players["A"].cities_left == 3


def test_piece_limit_enforced(board_and_topo):
    board, topology = board_and_topo
    state = make_ready_state(["A", "B"], phase=Phase.BUILD)
    v0 = topology.vertices[0]
    vid = vertex_id(v0)
    state.players["A"].roads.add(edge_id(topology.vertex_edges[v0][0]))
    state.players["A"].settlements_left = 0
    state.players["A"].resources.update({"wood": 1, "brick": 1, "wheat": 1, "sheep": 1})

    with pytest.raises(GameError) as exc:
        engine.build_settlement(board, topology, state, "A", vid)
    assert exc.value.code == "no_pieces_left"


def test_end_turn_advances_and_wraps(board_and_topo):
    board, topology = board_and_topo
    state = make_ready_state(["A", "B"], phase=Phase.BUILD)

    engine.end_turn(board, topology, state, "A")
    assert state.current_player() == "B"
    assert state.phase is Phase.ROLL

    state.phase = Phase.BUILD
    engine.end_turn(board, topology, state, "B")
    assert state.current_player() == "A"


def test_actions_rejected_in_wrong_phase(board_and_topo):
    board, topology = board_and_topo
    state = make_ready_state(["A", "B"], phase=Phase.ROLL)
    vid = vertex_id(topology.vertices[0])

    with pytest.raises(GameError) as exc:
        engine.build_settlement(board, topology, state, "A", vid)
    assert exc.value.code == "wrong_phase"

    with pytest.raises(GameError) as exc:
        engine.end_turn(board, topology, state, "A")
    assert exc.value.code == "wrong_phase"
