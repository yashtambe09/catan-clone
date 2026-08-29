import pytest

from app.game import engine
from app.game.board import Terrain, generate_board, topology_for
from app.game.ids import TopologyIndex, edge_id, vertex_id
from app.game.placement import GameError, legal_road_spots, legal_settlement_spots
from app.game.state import Phase


def setup_board(player_count, seed=1):
    board = generate_board(player_count, seed=seed)
    topology = topology_for(board)
    names = [f"P{i}" for i in range(player_count)]
    state = engine.new_game(board, names, seed=seed)
    return board, topology, state


@pytest.mark.parametrize("player_count", [2, 3, 4, 6])
def test_snake_draft_order_is_forward_then_reverse(player_count):
    board, topology, state = setup_board(player_count)
    order = state.order
    n = player_count
    expected_actors = order + list(reversed(order))

    for expected in expected_actors:
        assert state.current_player() == expected
        index = TopologyIndex(topology)
        vid = legal_settlement_spots(index, state, expected, setup=True)[0]
        engine.setup_settlement(board, topology, state, expected, vid)
        eid = legal_road_spots(index, state, expected, setup=True, required_vertex=vid)[0]
        engine.setup_road(board, topology, state, expected, eid)

    assert state.phase is Phase.ROLL
    assert state.current_player() == order[0]


def test_wrong_player_rejected_during_setup():
    board, topology, state = setup_board(2)
    other = state.order[1]
    index = TopologyIndex(topology)
    vid = legal_settlement_spots(index, state, other, setup=True)[0]
    with pytest.raises(GameError) as exc:
        engine.setup_settlement(board, topology, state, other, vid)
    assert exc.value.code == "not_your_turn"


def test_setup_road_must_touch_the_just_placed_settlement():
    board, topology, state = setup_board(2)
    actor = state.order[0]
    index = TopologyIndex(topology)
    vid = legal_settlement_spots(index, state, actor, setup=True)[0]
    engine.setup_settlement(board, topology, state, actor, vid)

    unrelated_edge = next(e for e in topology.edges if vertex_id(e[0]) != vid and vertex_id(e[1]) != vid)
    with pytest.raises(GameError) as exc:
        engine.setup_road(board, topology, state, actor, edge_id(unrelated_edge))
    assert exc.value.code == "illegal_placement"


def test_settlement_required_before_road():
    board, topology, state = setup_board(2)
    actor = state.order[0]
    index = TopologyIndex(topology)
    eid = edge_id(topology.edges[0])
    with pytest.raises(GameError) as exc:
        engine.setup_road(board, topology, state, actor, eid)
    assert exc.value.code == "wrong_phase"


def test_second_settlement_grants_one_resource_per_adjacent_non_desert_hex():
    board, topology, state = setup_board(2, seed=5)
    index = TopologyIndex(topology)
    actor = state.order[0]

    # burn through round 1 for both players
    for name in state.order:
        vid = legal_settlement_spots(index, state, name, setup=True)[0]
        engine.setup_settlement(board, topology, state, name, vid)
        eid = legal_road_spots(index, state, name, setup=True, required_vertex=vid)[0]
        engine.setup_road(board, topology, state, name, eid)

    # round 2, first actor (order[1] goes first in the reverse leg)
    actor = state.order[1]
    hex_by_coord = {h.coord: h for h in board.hexes}
    vid = legal_settlement_spots(index, state, actor, setup=True)[0]
    adjacent_hexes = [hex_by_coord[h] for h in hex_by_coord if vid in index.hex_vertices.get(h, [])]
    expected_gain = sum(1 for h in adjacent_hexes if h.terrain is not Terrain.DESERT)

    before = state.players[actor].hand_size()
    engine.setup_settlement(board, topology, state, actor, vid)
    eid = legal_road_spots(index, state, actor, setup=True, required_vertex=vid)[0]
    engine.setup_road(board, topology, state, actor, eid)
    after = state.players[actor].hand_size()

    assert after - before == expected_gain


def test_round_two_still_obeys_distance_rule_against_round_one_pieces():
    board, topology, state = setup_board(2)
    index = TopologyIndex(topology)

    first = state.order[0]
    v1 = legal_settlement_spots(index, state, first, setup=True)[0]
    engine.setup_settlement(board, topology, state, first, v1)
    e1 = legal_road_spots(index, state, first, setup=True, required_vertex=v1)[0]
    engine.setup_road(board, topology, state, first, e1)

    second = state.order[1]
    v2 = legal_settlement_spots(index, state, second, setup=True)[0]
    engine.setup_settlement(board, topology, state, second, v2)
    e2 = legal_road_spots(index, state, second, setup=True, required_vertex=v2)[0]
    engine.setup_road(board, topology, state, second, e2)

    # now second player's turn again (reverse leg) - v1's neighbors must still be illegal
    neighbor_of_v1 = vertex_id(next(iter(topology.vertex_neighbors[
        next(v for v in topology.vertices if vertex_id(v) == v1)
    ])))
    with pytest.raises(GameError):
        engine.setup_settlement(board, topology, state, second, neighbor_of_v1)
