import random

from app.game.largest_army import recompute_largest_army
from app.game.state import GameState, PlayerState


def make_state(names):
    players = {n: PlayerState(name=n) for n in names}
    return GameState(order=list(names), players=players, rng=random.Random(0))


def test_no_holder_below_three_knights():
    state = make_state(["A", "B"])
    state.players["A"].knights_played = 2
    recompute_largest_army(state)
    assert state.largest_army_holder is None


def test_first_claim_at_three_knights():
    state = make_state(["A", "B"])
    state.players["A"].knights_played = 3
    recompute_largest_army(state)
    assert state.largest_army_holder == "A"


def test_tie_does_not_award_anyone():
    state = make_state(["A", "B"])
    state.players["A"].knights_played = 3
    state.players["B"].knights_played = 3
    recompute_largest_army(state)
    assert state.largest_army_holder is None


def test_strict_exceed_transfers_holder():
    state = make_state(["A", "B"])
    state.players["A"].knights_played = 3
    recompute_largest_army(state)
    assert state.largest_army_holder == "A"

    state.players["B"].knights_played = 3
    recompute_largest_army(state)
    assert state.largest_army_holder == "A", "tie must not transfer"

    state.players["B"].knights_played = 4
    recompute_largest_army(state)
    assert state.largest_army_holder == "B"


def test_never_revoked_once_claimed():
    state = make_state(["A", "B"])
    state.players["A"].knights_played = 5
    recompute_largest_army(state)
    assert state.largest_army_holder == "A"

    # nothing decreases knights_played in real play, but even a hypothetical
    # drop (or B staying at 0) must not clear the incumbent - only a strict
    # exceed by someone else transfers it.
    recompute_largest_army(state)
    assert state.largest_army_holder == "A"
