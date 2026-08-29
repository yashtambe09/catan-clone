from app.game.ids import TopologyIndex
from app.game.placement import occupied_vertices


def _blocked_vertices(state, name: str) -> set:
    occ = occupied_vertices(state)
    return {v for v, owner in occ.items() if owner != name}


def player_longest_road(index: TopologyIndex, state, name: str) -> int:
    roads = state.players[name].roads
    if not roads:
        return 0

    adj: dict[str, list] = {}
    for eid in roads:
        a, b = eid.split("~")
        adj.setdefault(a, []).append((b, eid))
        adj.setdefault(b, []).append((a, eid))

    blocked = _blocked_vertices(state, name)
    best = 0

    # A blocked vertex (an opponent's settlement/city) may contribute at most
    # ONE of its incident edges to any single trail - it can be an endpoint,
    # but a trail can never use two of its edges (that would "pass through"
    # it, which the rule forbids even when the two uses aren't consecutive,
    # e.g. a loop that returns to a blocked vertex via a different edge).
    def dfs(vertex: str, used: set, blocked_used: set):
        nonlocal best
        best = max(best, len(used))
        for neighbor, eid in adj.get(vertex, []):
            if eid in used:
                continue
            newly_blocked = []
            ok = True
            for endpoint in (vertex, neighbor):
                if endpoint in blocked:
                    if endpoint in blocked_used:
                        ok = False
                        break
                    newly_blocked.append(endpoint)
            if not ok:
                continue

            used.add(eid)
            blocked_used.update(newly_blocked)
            dfs(neighbor, used, blocked_used)
            used.discard(eid)
            blocked_used.difference_update(newly_blocked)

    for start in adj:
        dfs(start, set(), set())

    return best


def recompute_longest_road(index: TopologyIndex, state) -> None:
    lengths = {name: player_longest_road(index, state, name) for name in state.order}
    for name, length in lengths.items():
        state.players[name].longest_road = length

    holder = state.longest_road_holder
    if holder is not None and lengths.get(holder, 0) < 5:
        holder = None

    best = max(lengths.values()) if lengths else 0
    if best < 5:
        state.longest_road_holder = None
        return

    if holder is not None and lengths[holder] == best:
        state.longest_road_holder = holder
        return

    leaders = [n for n in state.order if lengths[n] == best]
    state.longest_road_holder = leaders[0] if len(leaders) == 1 else None
