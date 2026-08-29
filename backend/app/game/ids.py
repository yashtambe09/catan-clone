from app.game.coords import Axial


def vertex_id(vertex) -> str:
    return "|".join(f"{h.q},{h.r}" for h in vertex)


def edge_id(edge) -> str:
    a, b = edge
    return f"{vertex_id(a)}~{vertex_id(b)}"


def parse_vertex(vid: str):
    hexes = [Axial(*(int(x) for x in part.split(","))) for part in vid.split("|")]
    return tuple(sorted(hexes))


def parse_edge(eid: str):
    a_str, b_str = eid.split("~")
    return tuple(sorted((parse_vertex(a_str), parse_vertex(b_str))))


class TopologyIndex:
    def __init__(self, topology):
        self.vertices = {vertex_id(v) for v in topology.vertices}
        self.edges = {edge_id(e) for e in topology.edges}
        self.vertex_neighbors = {
            vertex_id(v): [vertex_id(n) for n in ns]
            for v, ns in topology.vertex_neighbors.items()
        }
        self.vertex_edges = {
            vertex_id(v): [edge_id(e) for e in es]
            for v, es in topology.vertex_edges.items()
        }
        self.hex_vertices = {
            hex_: [vertex_id(v) for v in vs] for hex_, vs in topology.hex_vertices.items()
        }
