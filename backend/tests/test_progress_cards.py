import random

import pytest

from app.game import engine
from app.game.board import generate_board, topology_for
from app.game.ids import edge_id, vertex_id
from app.game.placement import GameError
from app.game.state import GameState, Phase, PlayerState


def make_state(names, phase=Phase.BUILD):
    players = {n: PlayerState(name=n) for n in names}
    return GameState(order=list(names), players=players, rng=random.Random(0), phase=phase)


@pytest.fixture
def board_and_topo():
    board = generate_board(2, seed=3)
    topology = topology_for(board)
    return board, topology


# ---- Monopoly ----


def test_monopoly_sweeps_all_other_players(board_and_topo):
    board, topology = board_and_topo
    state = make_state(["A", "B", "C"])
    state.players["A"].dev_cards["monopoly"] = 1
    state.players["B"].resources["wood"] = 3
    state.players["C"].resources["wood"] = 2
    state.players["C"].resources["brick"] = 5

    engine.play_monopoly(board, topology, state, "A", "wood")

    assert state.players["A"].resources["wood"] == 5
    assert state.players["B"].resources["wood"] == 0
    assert state.players["C"].resources["wood"] == 0
    assert state.players["C"].resources["brick"] == 5
    assert state.players["A"].dev_cards["monopoly"] == 0
    assert state.players["A"].dev_played["monopoly"] == 1


def test_monopoly_on_a_resource_nobody_holds_still_succeeds(board_and_topo):
    board, topology = board_and_topo
    state = make_state(["A", "B"])
    state.players["A"].dev_cards["monopoly"] = 1

    engine.play_monopoly(board, topology, state, "A", "ore")
    assert state.players["A"].resources["ore"] == 0
    assert state.players["A"].dev_played["monopoly"] == 1


def test_monopoly_does_not_touch_callers_own_stock(board_and_topo):
    board, topology = board_and_topo
    state = make_state(["A", "B"])
    state.players["A"].dev_cards["monopoly"] = 1
    state.players["A"].resources["wood"] = 4

    engine.play_monopoly(board, topology, state, "A", "wood")
    assert state.players["A"].resources["wood"] == 4


def test_monopoly_requires_the_card(board_and_topo):
    board, topology = board_and_topo
    state = make_state(["A", "B"])
    with pytest.raises(GameError) as exc:
        engine.play_monopoly(board, topology, state, "A", "wood")
    assert exc.value.code == "no_such_card"


def test_monopoly_rejects_unknown_resource(board_and_topo):
    board, topology = board_and_topo
    state = make_state(["A", "B"])
    state.players["A"].dev_cards["monopoly"] = 1
    with pytest.raises(GameError) as exc:
        engine.play_monopoly(board, topology, state, "A", "gold")
    assert exc.value.code == "invalid_resource"


def test_monopoly_rejected_outside_build(board_and_topo):
    board, topology = board_and_topo
    state = make_state(["A", "B"], phase=Phase.ROLL)
    state.players["A"].dev_cards["monopoly"] = 1
    with pytest.raises(GameError) as exc:
        engine.play_monopoly(board, topology, state, "A", "wood")
    assert exc.value.code == "wrong_phase"


def test_monopoly_rejected_for_non_current_player(board_and_topo):
    board, topology = board_and_topo
    state = make_state(["A", "B"])
    state.players["B"].dev_cards["monopoly"] = 1
    with pytest.raises(GameError) as exc:
        engine.play_monopoly(board, topology, state, "B", "wood")
    assert exc.value.code == "not_your_turn"


def test_card_bought_this_turn_cannot_be_played_as_monopoly(board_and_topo):
    board, topology = board_and_topo
    state = make_state(["A", "B"])
    state.players["A"].dev_new["monopoly"] = 1
    with pytest.raises(GameError) as exc:
        engine.play_monopoly(board, topology, state, "A", "wood")
    assert exc.value.code == "no_such_card"


# ---- Year of Plenty ----


def test_year_of_plenty_two_different_resources(board_and_topo):
    board, topology = board_and_topo
    state = make_state(["A", "B"])
    state.players["A"].dev_cards["year_of_plenty"] = 1

    engine.play_year_of_plenty(board, topology, state, "A", ["wood", "brick"])
    assert state.players["A"].resources["wood"] == 1
    assert state.players["A"].resources["brick"] == 1
    assert state.players["A"].dev_played["year_of_plenty"] == 1


def test_year_of_plenty_two_of_the_same_resource(board_and_topo):
    board, topology = board_and_topo
    state = make_state(["A", "B"])
    state.players["A"].dev_cards["year_of_plenty"] = 1

    engine.play_year_of_plenty(board, topology, state, "A", ["ore", "ore"])
    assert state.players["A"].resources["ore"] == 2


def test_year_of_plenty_rejects_wrong_count(board_and_topo):
    board, topology = board_and_topo
    state = make_state(["A", "B"])
    state.players["A"].dev_cards["year_of_plenty"] = 1
    with pytest.raises(GameError) as exc:
        engine.play_year_of_plenty(board, topology, state, "A", ["wood"])
    assert exc.value.code == "invalid_resource"


def test_year_of_plenty_rejects_unknown_resource(board_and_topo):
    board, topology = board_and_topo
    state = make_state(["A", "B"])
    state.players["A"].dev_cards["year_of_plenty"] = 1
    with pytest.raises(GameError) as exc:
        engine.play_year_of_plenty(board, topology, state, "A", ["wood", "gold"])
    assert exc.value.code == "invalid_resource"


def test_year_of_plenty_requires_the_card(board_and_topo):
    board, topology = board_and_topo
    state = make_state(["A", "B"])
    with pytest.raises(GameError) as exc:
        engine.play_year_of_plenty(board, topology, state, "A", ["wood", "brick"])
    assert exc.value.code == "no_such_card"


# ---- Road Building ----


def test_road_building_places_two_free_roads(board_and_topo):
    board, topology = board_and_topo
    state = make_state(["A", "B"])
    state.players["A"].dev_cards["road_building"] = 1

    v0 = topology.vertices[0]
    state.players["A"].settlements.add(vertex_id(v0))
    e0 = topology.vertex_edges[v0][0]
    e0_id = edge_id(e0)
    other_end = e0[0] if e0[0] != v0 else e0[1]
    e1_id = edge_id(next(e for e in topology.vertex_edges[other_end] if edge_id(e) != e0_id))

    before_resources = dict(state.players["A"].resources)
    engine.play_road_building(board, topology, state, "A", [e0_id, e1_id])

    assert e0_id in state.players["A"].roads
    assert e1_id in state.players["A"].roads
    assert state.players["A"].resources == before_resources
    assert state.players["A"].dev_cards["road_building"] == 0
    assert state.players["A"].roads_left == 13


def test_road_building_rolls_back_on_illegal_second_road(board_and_topo):
    board, topology = board_and_topo
    state = make_state(["A", "B"])
    state.players["A"].dev_cards["road_building"] = 1

    v0 = topology.vertices[0]
    state.players["A"].settlements.add(vertex_id(v0))
    legal_edge = edge_id(topology.vertex_edges[v0][0])
    illegal_edge = edge_id(topology.edges[-1])

    with pytest.raises(GameError):
        engine.play_road_building(board, topology, state, "A", [legal_edge, illegal_edge])

    assert state.players["A"].roads == set()
    assert state.players["A"].roads_left == 15
    assert state.players["A"].dev_cards["road_building"] == 1


def test_road_building_rejects_zero_roads_when_spots_are_available(board_and_topo):
    board, topology = board_and_topo
    state = make_state(["A", "B"])
    state.players["A"].dev_cards["road_building"] = 1
    state.players["A"].settlements.add(vertex_id(topology.vertices[0]))

    with pytest.raises(GameError) as exc:
        engine.play_road_building(board, topology, state, "A", [])
    assert exc.value.code == "invalid_action"
    assert state.players["A"].dev_cards["road_building"] == 1


def test_road_building_with_zero_roads_left_errors_and_keeps_card(board_and_topo):
    board, topology = board_and_topo
    state = make_state(["A", "B"])
    state.players["A"].dev_cards["road_building"] = 1
    state.players["A"].roads_left = 0

    with pytest.raises(GameError) as exc:
        engine.play_road_building(board, topology, state, "A", [])
    assert exc.value.code == "no_pieces_left"
    assert state.players["A"].dev_cards["road_building"] == 1


def test_road_building_requires_the_card(board_and_topo):
    board, topology = board_and_topo
    state = make_state(["A", "B"])
    with pytest.raises(GameError) as exc:
        engine.play_road_building(board, topology, state, "A", [])
    assert exc.value.code == "no_such_card"


def test_road_building_updates_longest_road(board_and_topo):
    board, topology = board_and_topo
    state = make_state(["A", "B"])
    state.players["A"].dev_cards["road_building"] = 1

    v0 = topology.vertices[0]
    state.players["A"].settlements.add(vertex_id(v0))
    e0 = topology.vertex_edges[v0][0]
    e0_id = edge_id(e0)
    other_end = e0[0] if e0[0] != v0 else e0[1]
    e1_id = edge_id(next(e for e in topology.vertex_edges[other_end] if edge_id(e) != e0_id))

    engine.play_road_building(board, topology, state, "A", [e0_id, e1_id])
    assert state.players["A"].longest_road == 2
