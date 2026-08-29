import random

import pytest

from app.game import engine
from app.game.board import generate_board, topology_for
from app.game.ids import vertex_id
from app.game.placement import GameError
from app.game.ports import Port
from app.game.state import GameState, Phase, PlayerState


def make_state(names, phase=Phase.BUILD):
    players = {n: PlayerState(name=n) for n in names}
    return GameState(order=list(names), players=players, rng=random.Random(0), phase=phase)


@pytest.fixture
def board_and_topo():
    board = generate_board(2, seed=3)
    topology = topology_for(board)
    return board, topology


def test_bank_trade_four_to_one_happy_path(board_and_topo):
    board, topology = board_and_topo
    board.ports = []
    state = make_state(["A", "B"])
    state.players["A"].resources["wood"] = 4

    engine.bank_trade(board, topology, state, "A", "wood", "brick", 1)
    assert state.players["A"].resources["wood"] == 0
    assert state.players["A"].resources["brick"] == 1


def test_bank_trade_insufficient_resources(board_and_topo):
    board, topology = board_and_topo
    board.ports = []
    state = make_state(["A", "B"])
    state.players["A"].resources["wood"] = 3

    with pytest.raises(GameError) as exc:
        engine.bank_trade(board, topology, state, "A", "wood", "brick", 1)
    assert exc.value.code == "insufficient_resources"


def test_bank_trade_rejects_same_resource(board_and_topo):
    board, topology = board_and_topo
    state = make_state(["A", "B"])
    with pytest.raises(GameError) as exc:
        engine.bank_trade(board, topology, state, "A", "wood", "wood", 1)
    assert exc.value.code == "invalid_trade"


def test_generic_port_gives_three_to_one_only_with_a_building(board_and_topo):
    board, topology = board_and_topo
    v0 = vertex_id(topology.vertices[0])
    board.ports = [Port(edge="e", vertices=(v0, "other"), ratio=3, resource=None)]
    state = make_state(["A", "B"])
    state.players["A"].resources["wood"] = 3

    with pytest.raises(GameError):
        engine.bank_trade(board, topology, state, "A", "wood", "brick", 1)

    state.players["A"].settlements.add(v0)
    engine.bank_trade(board, topology, state, "A", "wood", "brick", 1)
    assert state.players["A"].resources["wood"] == 0


def test_resource_port_gives_two_to_one_only_for_matching_resource(board_and_topo):
    board, topology = board_and_topo
    v0 = vertex_id(topology.vertices[0])
    board.ports = [Port(edge="e", vertices=(v0, "other"), ratio=2, resource="wood")]
    state = make_state(["A", "B"])
    state.players["A"].settlements.add(v0)
    state.players["A"].resources.update({"wood": 2, "brick": 3})

    engine.bank_trade(board, topology, state, "A", "wood", "sheep", 1)
    assert state.players["A"].resources["wood"] == 0

    with pytest.raises(GameError) as exc:
        engine.bank_trade(board, topology, state, "A", "brick", "sheep", 1)
    assert exc.value.code == "insufficient_resources"


def test_road_only_at_port_vertex_does_not_grant_ratio(board_and_topo):
    board, topology = board_and_topo
    v0 = topology.vertices[0]
    v0_id = vertex_id(v0)
    board.ports = [Port(edge="e", vertices=(v0_id, "other"), ratio=3, resource=None)]
    state = make_state(["A", "B"])
    e0 = topology.vertex_edges[v0][0]
    from app.game.ids import edge_id

    state.players["A"].roads.add(edge_id(e0))
    state.players["A"].resources["wood"] = 3

    with pytest.raises(GameError) as exc:
        engine.bank_trade(board, topology, state, "A", "wood", "brick", 1)
    assert exc.value.code == "insufficient_resources"


def test_city_on_port_still_grants_ratio(board_and_topo):
    board, topology = board_and_topo
    v0 = vertex_id(topology.vertices[0])
    board.ports = [Port(edge="e", vertices=(v0, "other"), ratio=2, resource="wood")]
    state = make_state(["A", "B"])
    state.players["A"].cities.add(v0)
    state.players["A"].resources["wood"] = 2

    engine.bank_trade(board, topology, state, "A", "wood", "sheep", 1)
    assert state.players["A"].resources["wood"] == 0


def test_best_ratio_wins_over_generic(board_and_topo):
    board, topology = board_and_topo
    v0 = vertex_id(topology.vertices[0])
    board.ports = [
        Port(edge="e1", vertices=(v0, "x"), ratio=3, resource=None),
        Port(edge="e2", vertices=(v0, "y"), ratio=2, resource="wood"),
    ]
    state = make_state(["A", "B"])
    state.players["A"].settlements.add(v0)
    ratios = engine.port_ratios(board, state, "A")
    assert ratios["wood"] == 2
    assert ratios["brick"] == 3


def test_bank_trade_rejected_outside_build(board_and_topo):
    board, topology = board_and_topo
    state = make_state(["A", "B"], phase=Phase.ROLL)
    with pytest.raises(GameError) as exc:
        engine.bank_trade(board, topology, state, "A", "wood", "brick", 1)
    assert exc.value.code == "wrong_phase"


# ---- Player-to-player trading ----


def test_propose_requires_current_player():
    state = make_state(["A", "B"])
    state.players["B"].resources["wood"] = 1
    with pytest.raises(GameError) as exc:
        engine.trade_propose(state, "B", {"wood": 1}, {"brick": 1})
    assert exc.value.code == "not_your_turn"


def test_propose_requires_offered_resources():
    state = make_state(["A", "B"])
    with pytest.raises(GameError) as exc:
        engine.trade_propose(state, "A", {"wood": 1}, {"brick": 1})
    assert exc.value.code == "insufficient_resources"


def test_open_offer_accepted_by_any_non_proposer():
    state = make_state(["A", "B", "C"])
    state.players["A"].resources["wood"] = 1
    state.players["C"].resources["brick"] = 1

    engine.trade_propose(state, "A", {"wood": 1}, {"brick": 1})
    engine.trade_accept(state, "C")

    assert state.players["A"].resources["wood"] == 0
    assert state.players["A"].resources["brick"] == 1
    assert state.players["C"].resources["brick"] == 0
    assert state.players["C"].resources["wood"] == 1
    assert state.trade is None


def test_targeted_offer_not_acceptable_by_third_party():
    state = make_state(["A", "B", "C"])
    state.players["A"].resources["wood"] = 1
    state.players["B"].resources["brick"] = 1
    state.players["C"].resources["brick"] = 1

    engine.trade_propose(state, "A", {"wood": 1}, {"brick": 1}, target="B")
    with pytest.raises(GameError) as exc:
        engine.trade_accept(state, "C")
    assert exc.value.code == "not_eligible"


def test_counter_replaces_offer_and_only_original_proposer_can_accept():
    state = make_state(["A", "B", "C"])
    state.players["A"].resources["wood"] = 1
    state.players["B"].resources["brick"] = 1

    engine.trade_propose(state, "A", {"wood": 1}, {"brick": 1})
    engine.trade_counter(state, "B", {"brick": 1}, {"wood": 1})

    assert state.trade.proposer == "B"
    assert state.trade.target == "A"

    with pytest.raises(GameError) as exc:
        engine.trade_accept(state, "C")
    assert exc.value.code == "not_eligible"

    engine.trade_accept(state, "A")
    assert state.players["A"].resources["brick"] == 1
    assert state.players["B"].resources["wood"] == 1


def test_reject_targeted_clears_immediately_but_open_needs_everyone():
    state = make_state(["A", "B", "C"])
    state.players["A"].resources["wood"] = 1

    engine.trade_propose(state, "A", {"wood": 1}, {"brick": 1}, target="B")
    engine.trade_reject(state, "B")
    assert state.trade is None

    engine.trade_propose(state, "A", {"wood": 1}, {"brick": 1})
    engine.trade_reject(state, "B")
    assert state.trade is not None
    engine.trade_reject(state, "C")
    assert state.trade is None


def test_cancel_only_by_proposer():
    state = make_state(["A", "B"])
    state.players["A"].resources["wood"] = 1
    engine.trade_propose(state, "A", {"wood": 1}, {"brick": 1})

    with pytest.raises(GameError) as exc:
        engine.trade_cancel(state, "B")
    assert exc.value.code == "not_eligible"

    engine.trade_cancel(state, "A")
    assert state.trade is None


def test_accept_fails_and_clears_if_hand_changed_since_propose():
    state = make_state(["A", "B"])
    state.players["A"].resources["wood"] = 1
    state.players["B"].resources["brick"] = 1
    engine.trade_propose(state, "A", {"wood": 1}, {"brick": 1})

    state.players["A"].resources["wood"] = 0
    with pytest.raises(GameError) as exc:
        engine.trade_accept(state, "B")
    assert exc.value.code == "insufficient_resources"
    assert state.trade is None


def test_offer_cleared_by_end_turn(board_and_topo):
    board, topology = board_and_topo
    state = make_state(["A", "B"])
    state.players["A"].resources["wood"] = 1
    engine.trade_propose(state, "A", {"wood": 1}, {"brick": 1})

    engine.end_turn(board, topology, state, "A")
    assert state.trade is None


def test_cannot_trade_with_self():
    state = make_state(["A", "B"])
    state.players["A"].resources["wood"] = 1
    with pytest.raises(GameError) as exc:
        engine.trade_propose(state, "A", {"wood": 1}, {"brick": 1}, target="A")
    assert exc.value.code == "invalid_trade"


def test_trade_rejected_outside_build():
    state = make_state(["A", "B"], phase=Phase.ROLL)
    with pytest.raises(GameError) as exc:
        engine.trade_propose(state, "A", {"wood": 1}, {"brick": 1})
    assert exc.value.code == "wrong_phase"
