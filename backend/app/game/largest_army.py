MIN_KNIGHTS = 3


def recompute_largest_army(state) -> None:
    counts = {name: state.players[name].knights_played for name in state.order}
    best = max(counts.values()) if counts else 0
    if best < MIN_KNIGHTS:
        return

    holder = state.largest_army_holder
    if holder is not None and counts[holder] >= best:
        return

    leaders = [n for n in state.order if counts[n] == best]
    if len(leaders) == 1:
        state.largest_army_holder = leaders[0]
