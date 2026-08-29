import pytest

from app.game.board import BOARD_SPECS, RESOURCE_BY_TERRAIN, BoardSize, generate_board
from app.game.coords import hexes_in_bounds
from app.game.ids import parse_edge, parse_vertex
from app.game.ports import boundary_ring
from app.game.topology import Topology

STANDARD = Topology(hexes_in_bounds(BOARD_SPECS[BoardSize.STANDARD].bounds))
EXPANDED = Topology(hexes_in_bounds(BOARD_SPECS[BoardSize.EXPANDED].bounds))
RESOURCES = set(RESOURCE_BY_TERRAIN.values())


@pytest.mark.parametrize("topology,expected", [(STANDARD, 30), (EXPANDED, 38)])
def test_boundary_ring_covers_every_boundary_edge_once(topology, expected):
    ring = boundary_ring(topology)
    assert len(ring) == expected
    edges = {frozenset((ring[i], ring[(i + 1) % len(ring)])) for i in range(len(ring))}
    boundary = {frozenset(e) for e in topology.boundary_edges()}
    assert edges == boundary


@pytest.mark.parametrize(
    "player_count,expected_total,expected_generic",
    [(4, 9, 4), (6, 11, 6)],
)
def test_port_count_and_mix(player_count, expected_total, expected_generic):
    board = generate_board(player_count, seed=1)
    assert len(board.ports) == expected_total
    generics = [p for p in board.ports if p.resource is None]
    specifics = [p for p in board.ports if p.resource is not None]
    assert len(generics) == expected_generic
    assert all(p.ratio == 3 for p in generics)
    assert all(p.ratio == 2 for p in specifics)
    assert {p.resource for p in specifics} == RESOURCES
    assert len(specifics) == len(RESOURCES)


@pytest.mark.parametrize("player_count", [4, 6])
def test_ports_sit_on_real_boundary_edges(player_count):
    board = generate_board(player_count, seed=2)
    topology = Topology([h.coord for h in board.hexes])
    boundary_edges = {frozenset(e) for e in topology.boundary_edges()}
    for port in board.ports:
        edge = parse_edge(port.edge)
        assert frozenset(edge) in boundary_edges
        assert {parse_vertex(v) for v in port.vertices} == set(edge)


@pytest.mark.parametrize("player_count", [4, 6])
def test_no_two_ports_share_a_vertex(player_count):
    board = generate_board(player_count, seed=3)
    seen = set()
    for port in board.ports:
        for v in port.vertices:
            assert v not in seen
            seen.add(v)


@pytest.mark.parametrize("player_count", [4, 6])
def test_port_generation_is_deterministic_under_seed(player_count):
    a = generate_board(player_count, seed=42)
    b = generate_board(player_count, seed=42)
    assert a.ports == b.ports


def test_different_seeds_rotate_port_positions():
    boards = {tuple(p.edge for p in generate_board(4, seed=s).ports) for s in range(30)}
    assert len(boards) > 1


def test_board_round_trips_ports_through_json():
    board = generate_board(6, seed=7)
    restored = board.model_validate_json(board.model_dump_json())
    assert restored.ports == board.ports
