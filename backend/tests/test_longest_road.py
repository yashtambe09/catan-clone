import random

import pytest

from app.game.board import BOARD_SPECS, BoardSize
from app.game.coords import hexes_in_bounds
from app.game.ids import TopologyIndex, edge_id
from app.game.longest_road import player_longest_road, recompute_longest_road
from app.game.state import GameState, PlayerState
from app.game.topology import Topology

STANDARD = Topology(hexes_in_bounds(BOARD_SPECS[BoardSize.STANDARD].bounds))
EXPANDED = Topology(hexes_in_bounds(BOARD_SPECS[BoardSize.EXPANDED].bounds))


def make_state(topology, names):
    players = {n: PlayerState(name=n) for n in names}
    return GameState(order=list(names), players=players, rng=random.Random(0))


def chain(topology, index: TopologyIndex, length: int) -> list:
    """Walk `length` distinct edges from an arbitrary starting vertex."""
    start = next(iter(index.vertex_edges))
    path_edges = []
    visited_vertices = {start}
    current = start
    for _ in range(length):
        for neighbor in index.vertex_neighbors[current]:
            eid = edge_id(tuple(sorted((_parse(current), _parse(neighbor)))))
            if eid in index.edges and neighbor not in visited_vertices:
                path_edges.append(eid)
                visited_vertices.add(neighbor)
                current = neighbor
                break
        else:
            raise RuntimeError("could not extend chain further on this board")
    return path_edges


def _parse(vid):
    from app.game.ids import parse_vertex

    return parse_vertex(vid)


@pytest.mark.parametrize("topology", [STANDARD, EXPANDED])
def test_empty_and_single_road(topology):
    index = TopologyIndex(topology)
    state = make_state(topology, ["A"])
    assert player_longest_road(index, state, "A") == 0

    state.players["A"].roads = set(chain(topology, index, 1))
    assert player_longest_road(index, state, "A") == 1


@pytest.mark.parametrize("topology", [STANDARD, EXPANDED])
@pytest.mark.parametrize("length", [2, 3, 4, 5])
def test_straight_chain_length(topology, length):
    index = TopologyIndex(topology)
    state = make_state(topology, ["A"])
    state.players["A"].roads = set(chain(topology, index, length))
    assert player_longest_road(index, state, "A") == length


@pytest.mark.parametrize("topology", [STANDARD, EXPANDED])
def test_y_shape_gives_two_not_three(topology):
    index = TopologyIndex(topology)
    center = next(v for v in index.vertex_edges if len(index.vertex_edges[v]) == 3)
    roads = set(index.vertex_edges[center][:3])
    state = make_state(topology, ["A"])
    state.players["A"].roads = roads
    assert player_longest_road(index, state, "A") == 2


@pytest.mark.parametrize("topology", [STANDARD, EXPANDED])
def test_hex_ring_gives_six(topology):
    index = TopologyIndex(topology)
    hex_coord = topology.hexes[len(topology.hexes) // 2]
    ring_edges = set()
    verts = index.hex_vertices[hex_coord]
    for i in range(6):
        a, b = verts[i], verts[(i + 1) % 6]
        eid = edge_id(tuple(sorted((_parse(a), _parse(b)))))
        assert eid in index.edges
        ring_edges.add(eid)

    state = make_state(topology, ["A"])
    state.players["A"].roads = ring_edges
    assert player_longest_road(index, state, "A") == 6


@pytest.mark.parametrize("topology", [STANDARD, EXPANDED])
def test_disconnected_components_take_the_max(topology):
    index = TopologyIndex(topology)
    a_edges = chain(topology, index, 3)

    used_vertices = set()
    for eid in a_edges:
        used_vertices.update(eid.split("~"))

    other_start = next(v for v in index.vertex_edges if v not in used_vertices)

    def chain_from(start, length):
        path = []
        visited = {start}
        current = start
        for _ in range(length):
            for neighbor in index.vertex_neighbors[current]:
                eid = edge_id(tuple(sorted((_parse(current), _parse(neighbor)))))
                if (
                    eid in index.edges
                    and neighbor not in visited
                    and neighbor not in used_vertices
                    and eid not in a_edges
                ):
                    path.append(eid)
                    visited.add(neighbor)
                    current = neighbor
                    break
            else:
                raise RuntimeError("cannot extend")
        return path

    b_edges = chain_from(other_start, 5)
    b_vertices = {v for eid in b_edges for v in eid.split("~")}
    assert not (used_vertices & b_vertices), "test components must stay disconnected"

    state = make_state(topology, ["A"])
    state.players["A"].roads = set(a_edges) | set(b_edges)
    assert player_longest_road(index, state, "A") == 5


@pytest.mark.parametrize("topology", [STANDARD, EXPANDED])
def test_opponent_settlement_cuts_a_chain_in_the_middle(topology):
    index = TopologyIndex(topology)
    edges = chain(topology, index, 6)

    visited = []
    cur = None
    for eid in edges:
        a, b = eid.split("~")
        if cur is None:
            visited.append(a)
            cur = a
        nxt = b if a == cur else a
        visited.append(nxt)
        cur = nxt

    cut_vertex = visited[3]

    state = make_state(topology, ["A", "B"])
    state.players["A"].roads = set(edges)
    state.players["B"].settlements = {cut_vertex}

    result = player_longest_road(index, state, "A")
    assert result == 3


@pytest.mark.parametrize("topology", [STANDARD, EXPANDED])
def test_own_settlement_mid_chain_has_no_effect(topology):
    index = TopologyIndex(topology)
    edges = chain(topology, index, 4)
    mid_vertex = edges[1].split("~")[0]

    state = make_state(topology, ["A"])
    state.players["A"].roads = set(edges)
    state.players["A"].settlements = {mid_vertex}

    assert player_longest_road(index, state, "A") == 4


def test_recompute_first_claim_requires_five():
    index = TopologyIndex(STANDARD)
    state = make_state(STANDARD, ["A", "B"])
    state.players["A"].roads = set(chain(STANDARD, index, 4))
    recompute_longest_road(index, state)
    assert state.longest_road_holder is None
    assert state.players["A"].longest_road == 4

    state.players["A"].roads = set(chain(STANDARD, index, 5))
    recompute_longest_road(index, state)
    assert state.longest_road_holder == "A"


def test_recompute_strict_exceed_transfers_holder():
    index = TopologyIndex(STANDARD)
    state = make_state(STANDARD, ["A", "B"])
    state.players["A"].roads = set(chain(STANDARD, index, 5))
    recompute_longest_road(index, state)
    assert state.longest_road_holder == "A"

    a_vertices = set()
    for eid in state.players["A"].roads:
        a_vertices.update(eid.split("~"))
    start_b = next(v for v in index.vertex_edges if v not in a_vertices)

    def chain_from(start, length, avoid):
        path = []
        visited = {start}
        current = start
        for _ in range(length):
            for neighbor in index.vertex_neighbors[current]:
                eid = edge_id(tuple(sorted((_parse(current), _parse(neighbor)))))
                if eid in index.edges and neighbor not in visited and eid not in avoid:
                    path.append(eid)
                    visited.add(neighbor)
                    current = neighbor
                    break
            else:
                raise RuntimeError("cannot extend")
        return path

    state.players["B"].roads = set(chain_from(start_b, 5, state.players["A"].roads))
    recompute_longest_road(index, state)
    assert state.longest_road_holder == "A", "tie must not transfer"

    state.players["B"].roads = set(chain_from(start_b, 6, state.players["A"].roads))
    recompute_longest_road(index, state)
    assert state.longest_road_holder == "B"


def test_recompute_revokes_when_holder_drops_below_five():
    index = TopologyIndex(STANDARD)
    state = make_state(STANDARD, ["A", "B"])
    edges = chain(STANDARD, index, 6)
    state.players["A"].roads = set(edges)
    recompute_longest_road(index, state)
    assert state.longest_road_holder == "A"

    visited = []
    cur = None
    for eid in edges:
        a, b = eid.split("~")
        if cur is None:
            visited.append(a)
            cur = a
        nxt = b if a == cur else a
        visited.append(nxt)
        cur = nxt
    cut_vertex = visited[3]
    state.players["B"].settlements = {cut_vertex}

    recompute_longest_road(index, state)
    assert state.players["A"].longest_road == 3
    assert state.longest_road_holder is None, "card becomes unheld even though nobody else qualifies"


def test_victory_points_include_longest_road_bonus_for_holder_only():
    index = TopologyIndex(STANDARD)
    state = make_state(STANDARD, ["A", "B"])
    state.players["A"].roads = set(chain(STANDARD, index, 5))
    recompute_longest_road(index, state)

    payload = state.to_dict()
    assert payload["players"]["A"]["victory_points"] == 2
    assert payload["players"]["B"]["victory_points"] == 0
    assert payload["longest_road_holder"] == "A"
