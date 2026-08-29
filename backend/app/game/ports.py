from pydantic import BaseModel

from app.game.ids import edge_id, vertex_id


class Port(BaseModel):
    edge: str
    vertices: tuple[str, str]
    ratio: int
    resource: str | None = None


class BoardGenerationError(RuntimeError):
    pass


def boundary_ring(topology) -> list:
    boundary_edges = topology.boundary_edges()
    adjacency = {}
    for edge in boundary_edges:
        a, b = edge
        adjacency.setdefault(a, []).append(b)
        adjacency.setdefault(b, []).append(a)

    start = min(adjacency, key=vertex_id)
    ring = [start]
    prev = None
    current = start
    while True:
        neighbors = adjacency[current]
        next_ = neighbors[0] if neighbors[0] != prev else neighbors[1]
        if next_ == start:
            break
        ring.append(next_)
        prev, current = current, next_

    if len(ring) != len(boundary_edges):
        raise BoardGenerationError("board boundary is not a single simple cycle")
    return ring


def generate_ports(topology, kinds: list, rng) -> list:
    ring = boundary_ring(topology)
    n = len(ring)
    p = len(kinds)
    offset = rng.randrange(n)
    positions = [(offset + (k * n) // p) % n for k in range(p)]

    shuffled = list(kinds)
    rng.shuffle(shuffled)

    ports = []
    for kind, pos in zip(shuffled, positions):
        a, b = ring[pos], ring[(pos + 1) % n]
        edge = tuple(sorted((a, b)))
        ports.append(
            Port(
                edge=edge_id(edge),
                vertices=(vertex_id(a), vertex_id(b)),
                ratio=2 if kind else 3,
                resource=kind,
            )
        )
    return ports
