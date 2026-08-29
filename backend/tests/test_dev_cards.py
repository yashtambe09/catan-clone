import random
from collections import Counter

import pytest

from app.game import engine
from app.game.board import generate_board, topology_for
from app.game.placement import GameError
from app.game.state import DEV_CARDS, GameState, Phase, PlayerState


def make_state(names, phase=Phase.BUILD, dev_deck=None):
    players = {n: PlayerState(name=n) for n in names}
    return GameState(
        order=list(names), players=players, rng=random.Random(0), phase=phase,
        dev_deck=list(dev_deck) if dev_deck is not None else [],
    )


@pytest.fixture
def board_and_topo():
    board = generate_board(2, seed=3)
    topology = topology_for(board)
    return board, topology


def test_new_game_deck_has_the_standard_25_card_composition():
    board = generate_board(2, seed=1)
    state = engine.new_game(board, ["A", "B"], seed=1)
    assert len(state.dev_deck) == 25
    counts = Counter(state.dev_deck)
    assert counts == {
        "knight": 14, "victory_point": 5, "monopoly": 2, "road_building": 2, "year_of_plenty": 2,
    }


def test_deck_order_is_deterministic_under_seed(board_and_topo):
    board, _ = board_and_topo
    a = engine.new_game(board, ["A", "B"], seed=9)
    b = engine.new_game(board, ["A", "B"], seed=9)
    assert a.dev_deck == b.dev_deck


def test_buy_pays_cost_and_draws_from_deck(board_and_topo):
    board, topology = board_and_topo
    state = make_state(["A", "B"], dev_deck=["knight", "monopoly"])
    state.players["A"].resources.update({"wheat": 1, "sheep": 1, "ore": 1})

    engine.buy_dev_card(board, topology, state, "A")
    assert len(state.dev_deck) == 1
    assert sum(state.players["A"].resources.values()) == 0
    assert state.players["A"].dev_new["monopoly"] == 1


def test_buy_rejects_insufficient_resources(board_and_topo):
    board, topology = board_and_topo
    state = make_state(["A", "B"], dev_deck=["knight"])
    with pytest.raises(GameError) as exc:
        engine.buy_dev_card(board, topology, state, "A")
    assert exc.value.code == "insufficient_resources"


def test_buy_rejects_empty_deck(board_and_topo):
    board, topology = board_and_topo
    state = make_state(["A", "B"], dev_deck=[])
    state.players["A"].resources.update({"wheat": 1, "sheep": 1, "ore": 1})
    with pytest.raises(GameError) as exc:
        engine.buy_dev_card(board, topology, state, "A")
    assert exc.value.code == "deck_empty"


def test_card_bought_this_turn_cannot_be_played(board_and_topo):
    board, topology = board_and_topo
    state = make_state(["A", "B"], dev_deck=["knight"])
    state.players["A"].resources.update({"wheat": 1, "sheep": 1, "ore": 1})
    engine.buy_dev_card(board, topology, state, "A")

    empty_hex = next(h for h in board.hexes if h.coord != board.robber)
    with pytest.raises(GameError) as exc:
        engine.play_knight(board, topology, state, "A", empty_hex.coord, None)
    assert exc.value.code == "no_such_card"


def test_end_turn_promotes_dev_new_to_playable(board_and_topo):
    board, topology = board_and_topo
    state = make_state(["A", "B"], dev_deck=["knight"])
    state.players["A"].resources.update({"wheat": 1, "sheep": 1, "ore": 1})
    engine.buy_dev_card(board, topology, state, "A")

    engine.end_turn(board, topology, state, "A")
    assert state.players["A"].dev_cards["knight"] == 1
    assert state.players["A"].dev_new["knight"] == 0


def test_knight_moves_robber_steals_and_increments_counter(board_and_topo):
    board, topology = board_and_topo
    state = make_state(["A", "B"])
    state.players["A"].dev_cards["knight"] = 1
    target_hex = next(h for h in board.hexes if h.coord != board.robber)
    from app.game.ids import TopologyIndex

    index = TopologyIndex(topology)
    vid = index.hex_vertices[target_hex.coord][0]
    state.players["B"].settlements.add(vid)
    state.players["B"].resources["wood"] = 1

    engine.play_knight(board, topology, state, "A", target_hex.coord, "B")

    assert board.robber == target_hex.coord
    assert state.players["A"].resources["wood"] == 1
    assert state.players["A"].knights_played == 1
    assert state.players["A"].dev_cards["knight"] == 0
    assert state.players["A"].dev_played["knight"] == 1
    assert state.phase is Phase.BUILD


def test_knight_with_no_candidates_requires_no_steal(board_and_topo):
    board, topology = board_and_topo
    state = make_state(["A", "B"])
    state.players["A"].dev_cards["knight"] = 1
    empty_hex = next(h for h in board.hexes if h.coord != board.robber)

    engine.play_knight(board, topology, state, "A", empty_hex.coord, None)
    assert state.players["A"].knights_played == 1


def test_invalid_knight_target_leaves_card_and_phase_untouched(board_and_topo):
    board, topology = board_and_topo
    state = make_state(["A", "B"])
    state.players["A"].dev_cards["knight"] = 1

    with pytest.raises(GameError) as exc:
        engine.play_knight(board, topology, state, "A", board.robber, None)
    assert exc.value.code == "illegal_placement"
    assert state.players["A"].dev_cards["knight"] == 1
    assert state.phase is Phase.BUILD


def test_playing_without_a_knight_card_rejected(board_and_topo):
    board, topology = board_and_topo
    state = make_state(["A", "B"])
    empty_hex = next(h for h in board.hexes if h.coord != board.robber)
    with pytest.raises(GameError) as exc:
        engine.play_knight(board, topology, state, "A", empty_hex.coord, None)
    assert exc.value.code == "no_such_card"


def test_non_current_player_cannot_play_knight(board_and_topo):
    board, topology = board_and_topo
    state = make_state(["A", "B"])
    state.players["B"].dev_cards["knight"] = 1
    empty_hex = next(h for h in board.hexes if h.coord != board.robber)
    with pytest.raises(GameError) as exc:
        engine.play_knight(board, topology, state, "B", empty_hex.coord, None)
    assert exc.value.code == "not_your_turn"


def test_dev_card_visibility_hides_others_hands():
    players = {"A": PlayerState(name="A"), "B": PlayerState(name="B")}
    players["A"].dev_cards["knight"] = 2
    players["B"].dev_cards["monopoly"] = 1
    state = GameState(order=["A", "B"], players=players, rng=random.Random(0))

    view_a = state.to_dict(viewer="A")
    assert "dev_cards" in view_a["players"]["A"]
    assert view_a["players"]["A"]["dev_cards"]["knight"] == 2
    assert "dev_cards" not in view_a["players"]["B"]
    assert view_a["players"]["B"]["dev_card_count"] == 1

    view_none = state.to_dict()
    assert "dev_cards" not in view_none["players"]["A"]
    assert "dev_cards" not in view_none["players"]["B"]
    assert view_none["players"]["A"]["dev_card_count"] == 2
