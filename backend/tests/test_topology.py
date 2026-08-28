import pytest

from app.game.board import BOARD_SPECS, BoardSize
from app.game.coords import Axial, hexes_in_bounds
from app.game.topology import Topology, hex_corners, hex_edges

STANDARD = hexes_in_bounds(BOARD_SPECS[BoardSize.STANDARD].bounds)
EXPANDED = hexes_in_bounds(BOARD_SPECS[BoardSize.EXPANDED].bounds)


def test_a_shared_corner_gets_the_same_id_from_all_three_hexes():
    shared = tuple(sorted((Axial(0, 0), Axial(1, 0), Axial(1, -1))))
    assert shared in hex_corners(Axial(0, 0))
    assert shared in hex_corners(Axial(1, 0))
    assert shared in hex_corners(Axial(1, -1))


def test_each_hex_has_six_distinct_corners_and_edges():
    for hex_ in (Axial(0, 0), Axial(-2, 1), Axial(2, -2)):
        assert len(set(hex_corners(hex_))) == 6
        assert len(set(hex_edges(hex_))) == 6


def test_every_corner_is_three_mutually_distinct_hexes():
    for corner in hex_corners(Axial(0, 0)):
        assert len(set(corner)) == 3


def test_standard_board_has_54_vertices_and_72_edges():
    topology = Topology(STANDARD)
    assert len(topology.vertices) == 54
    assert len(topology.edges) == 72
    assert topology.adjacent_hex_pairs() == 42


def test_expanded_board_vertex_and_edge_counts():
    topology = Topology(EXPANDED)
    assert len(topology.vertices) == 80
    assert len(topology.edges) == 109
    assert topology.adjacent_hex_pairs() == 71


@pytest.mark.parametrize("hexes", [STANDARD, EXPANDED])
def test_edge_count_matches_hex_and_adjacency_identity(hexes):
    topology = Topology(hexes)
    assert len(topology.edges) == 6 * len(hexes) - topology.adjacent_hex_pairs()


@pytest.mark.parametrize("hexes", [STANDARD, EXPANDED])
def test_vertex_count_satisfies_eulers_formula(hexes):
    topology = Topology(hexes)
    faces = len(hexes) + 1
    assert len(topology.vertices) - len(topology.edges) + faces == 2


@pytest.mark.parametrize("hexes", [STANDARD, EXPANDED])
def test_boundary_edges_equal_boundary_vertices(hexes):
    topology = Topology(hexes)
    expected = 6 * len(hexes) - 2 * topology.adjacent_hex_pairs()
    assert len(topology.boundary_edges()) == expected
    assert len(topology.boundary_vertices()) == expected


@pytest.mark.parametrize("hexes", [STANDARD, EXPANDED])
def test_every_vertex_touches_one_to_three_board_hexes(hexes):
    topology = Topology(hexes)
    for vertex in topology.vertices:
        assert 1 <= len(topology.vertex_hexes[vertex]) <= 3


@pytest.mark.parametrize("hexes", [STANDARD, EXPANDED])
def test_every_vertex_has_two_or_three_incident_edges(hexes):
    topology = Topology(hexes)
    for vertex in topology.vertices:
        assert 2 <= len(topology.vertex_edges[vertex]) <= 3


@pytest.mark.parametrize("hexes", [STANDARD, EXPANDED])
def test_vertex_neighbors_are_symmetric(hexes):
    topology = Topology(hexes)
    for vertex, adjacent in topology.vertex_neighbors.items():
        assert len(set(adjacent)) == len(adjacent)
        for other in adjacent:
            assert vertex in topology.vertex_neighbors[other]


@pytest.mark.parametrize("hexes", [STANDARD, EXPANDED])
def test_every_hex_has_six_vertices_all_registered_on_the_board(hexes):
    topology = Topology(hexes)
    known = set(topology.vertices)
    for hex_ in hexes:
        vertices = topology.hex_vertices[hex_]
        assert len(set(vertices)) == 6
        assert known.issuperset(vertices)


@pytest.mark.parametrize("hexes", [STANDARD, EXPANDED])
def test_hex_neighbors_are_symmetric(hexes):
    topology = Topology(hexes)
    for hex_, adjacent in topology.hex_neighbors.items():
        for other in adjacent:
            assert hex_ in topology.hex_neighbors[other]


@pytest.mark.parametrize("hexes", [STANDARD, EXPANDED])
def test_topology_is_deterministic(hexes):
    assert Topology(hexes).vertices == Topology(hexes).vertices
    assert Topology(hexes).edges == Topology(hexes).edges
