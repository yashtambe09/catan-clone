from app.game.coords import DIRECTIONS, Axial, add

Vertex = tuple[Axial, Axial, Axial]
Edge = tuple[Vertex, Vertex]


def hex_corners(hex_: Axial) -> tuple[Vertex, ...]:
    corners = []
    for i in range(6):
        a = add(hex_, DIRECTIONS[i])
        b = add(hex_, DIRECTIONS[(i + 1) % 6])
        corners.append(tuple(sorted((hex_, a, b))))
    return tuple(corners)


def hex_edges(hex_: Axial) -> tuple[Edge, ...]:
    corners = hex_corners(hex_)
    return tuple(
        tuple(sorted((corners[i], corners[(i + 1) % 6]))) for i in range(6)
    )


class Topology:
    def __init__(self, hexes: list[Axial]):
        self.hexes = list(hexes)
        hex_set = set(self.hexes)

        self.hex_neighbors: dict[Axial, list[Axial]] = {
            hex_: [n for n in (add(hex_, d) for d in DIRECTIONS) if n in hex_set]
            for hex_ in self.hexes
        }

        self.hex_vertices: dict[Axial, tuple[Vertex, ...]] = {
            hex_: hex_corners(hex_) for hex_ in self.hexes
        }

        vertices: list[Vertex] = []
        seen_vertices: set[Vertex] = set()
        for hex_ in self.hexes:
            for vertex in self.hex_vertices[hex_]:
                if vertex not in seen_vertices:
                    seen_vertices.add(vertex)
                    vertices.append(vertex)
        self.vertices = vertices

        edges: list[Edge] = []
        seen_edges: set[Edge] = set()
        for hex_ in self.hexes:
            for edge in hex_edges(hex_):
                if edge not in seen_edges:
                    seen_edges.add(edge)
                    edges.append(edge)
        self.edges = edges

        self.vertex_hexes: dict[Vertex, list[Axial]] = {
            vertex: [h for h in vertex if h in hex_set] for vertex in self.vertices
        }

        self.vertex_edges: dict[Vertex, list[Edge]] = {v: [] for v in self.vertices}
        self.vertex_neighbors: dict[Vertex, list[Vertex]] = {v: [] for v in self.vertices}
        for edge in self.edges:
            a, b = edge
            self.vertex_edges[a].append(edge)
            self.vertex_edges[b].append(edge)
            self.vertex_neighbors[a].append(b)
            self.vertex_neighbors[b].append(a)

    def adjacent_hex_pairs(self) -> int:
        return sum(len(n) for n in self.hex_neighbors.values()) // 2

    def boundary_vertices(self) -> list[Vertex]:
        return [v for v in self.vertices if len(self.vertex_hexes[v]) <= 2]

    def boundary_edges(self) -> list[Edge]:
        counts: dict[Edge, int] = {}
        for hex_ in self.hexes:
            for edge in hex_edges(hex_):
                counts[edge] = counts.get(edge, 0) + 1
        return [edge for edge in self.edges if counts[edge] == 1]
