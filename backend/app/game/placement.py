from app.game.ids import TopologyIndex


class GameError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


def occupied_vertices(state) -> dict:
    occ = {}
    for name, p in state.players.items():
        for v in p.settlements | p.cities:
            occ[v] = name
    return occ


def road_owners(state) -> dict:
    occ = {}
    for name, p in state.players.items():
        for e in p.roads:
            occ[e] = name
    return occ


def legal_settlement_spots(index: TopologyIndex, state, name: str, setup: bool = False) -> list:
    occ = occupied_vertices(state)
    all_roads = road_owners(state)
    player_roads = state.players[name].roads
    spots = []
    for vid in index.vertices:
        if vid in occ:
            continue
        if any(n in occ for n in index.vertex_neighbors[vid]):
            continue
        if setup:
            if not any(e not in all_roads for e in index.vertex_edges[vid]):
                continue
        else:
            if not any(e in player_roads for e in index.vertex_edges[vid]):
                continue
        spots.append(vid)
    return spots


def legal_road_spots(
    index: TopologyIndex, state, name: str, setup: bool = False, required_vertex: str | None = None
) -> list:
    roads = road_owners(state)
    occ = occupied_vertices(state)
    player_roads = state.players[name].roads
    spots = []
    for eid in index.edges:
        if eid in roads:
            continue
        a, b = eid.split("~")
        if setup:
            if required_vertex not in (a, b):
                continue
        else:
            ok = False
            for v in (a, b):
                owner = occ.get(v)
                if owner == name:
                    ok = True
                    break
                if owner is None and any(e in player_roads for e in index.vertex_edges[v]):
                    ok = True
                    break
            if not ok:
                continue
        spots.append(eid)
    return spots


def check_settlement(index: TopologyIndex, state, name: str, vid: str, setup: bool = False):
    if vid not in index.vertices:
        raise GameError("invalid_vertex", "unknown vertex")
    if vid not in legal_settlement_spots(index, state, name, setup=setup):
        raise GameError("illegal_placement", "that vertex is not a legal settlement spot")


def check_road(
    index: TopologyIndex, state, name: str, eid: str, setup: bool = False, required_vertex: str | None = None
):
    if eid not in index.edges:
        raise GameError("invalid_edge", "unknown edge")
    if eid not in legal_road_spots(index, state, name, setup=setup, required_vertex=required_vertex):
        raise GameError("illegal_placement", "that edge is not a legal road spot")


def check_city(index: TopologyIndex, state, name: str, vid: str):
    if vid not in index.vertices:
        raise GameError("invalid_vertex", "unknown vertex")
    if vid not in state.players[name].settlements:
        raise GameError("illegal_placement", "you don't have a settlement there")
