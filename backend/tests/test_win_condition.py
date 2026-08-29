import random

import pytest

from app.game import engine
from app.game.board import generate_board, topology_for
from app.game.state import GameState, Phase, PlayerState


def make_state(names, phase=Phase.BUILD):
    players = {n: PlayerState(name=n) for n in names}
    return GameState(order=list(names), players=players, rng=random.Random(0), phase=phase)


@pytest.fixture
def board_and_topo():
    board = generate_board(2, seed=3)
    topology = topology_for(board)
    return board, topology


def test_true_victory_points_includes_hidden_vp_cards():
    state = make_state(["A", "B"])
    state.players["A"].settlements = {"v1", "v2"}
    state.players["A"].dev_cards["victory_point"] = 2

    assert state.players["A"].base_victory_points() == 2
    assert state.true_victory_points("A") == 4
    assert state.public_victory_points("A") == 2


def test_dev_new_victory_point_counts_immediately():
    state = make_state(["A", "B"])
    state.players["A"].dev_new["victory_point"] = 1
    assert state.true_victory_points("A") == 1


def test_true_victory_points_includes_bonuses():
    state = make_state(["A", "B"])
    state.longest_road_holder = "A"
    state.largest_army_holder = "A"
    assert state.true_victory_points("A") == 4
    assert state.public_victory_points("A") == 4


def test_own_view_shows_true_vp_others_show_public_vp():
    state = make_state(["A", "B"])
    state.players["A"].dev_cards["victory_point"] = 1

    own_view = state.to_dict(viewer="A")
    other_view = state.to_dict(viewer="B")

    assert own_view["players"]["A"]["victory_points"] == 1
    assert other_view["players"]["A"]["victory_points"] == 0


def test_spectator_view_shows_public_vp_for_everyone():
    state = make_state(["A", "B"])
    state.players["A"].dev_cards["victory_point"] = 1
    spectator_view = state.to_dict()
    assert spectator_view["players"]["A"]["victory_points"] == 0


def test_check_win_triggers_at_ten_and_sets_winner():
    state = make_state(["A", "B"])
    state.players["A"].settlements = {f"v{i}" for i in range(10)}

    winner = engine.check_win(state)
    assert winner == "A"
    assert state.winner == "A"
    assert state.phase is Phase.GAME_OVER


def test_check_win_returns_none_below_threshold():
    state = make_state(["A", "B"])
    state.players["A"].settlements = {"v1", "v2"}
    assert engine.check_win(state) is None
    assert state.phase is Phase.BUILD


def test_check_win_is_idempotent_and_keeps_first_winner():
    state = make_state(["A", "B"])
    state.players["A"].settlements = {f"v{i}" for i in range(10)}
    state.players["B"].settlements = {f"w{i}" for i in range(10)}

    first = engine.check_win(state)
    assert first == "A"

    second = engine.check_win(state)
    assert second == "A", "already-decided winner must not change on re-check"


def test_check_win_clears_a_live_trade_offer():
    state = make_state(["A", "B"])
    state.players["A"].resources["wood"] = 1
    state.players["A"].settlements = {f"v{i}" for i in range(10)}
    engine.trade_propose(state, "A", {"wood": 1}, {"brick": 1})
    assert state.trade is not None

    engine.check_win(state)
    assert state.trade is None


def test_actions_rejected_once_game_is_over(board_and_topo):
    board, topology = board_and_topo
    state = make_state(["A", "B"])
    state.players["A"].settlements = {f"v{i}" for i in range(10)}
    engine.check_win(state)

    from app.game.placement import GameError

    with pytest.raises(GameError) as exc:
        engine.end_turn(board, topology, state, "A")
    assert exc.value.code == "wrong_phase"
