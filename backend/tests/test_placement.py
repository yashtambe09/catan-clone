import random

import pytest

from app.game.board import BOARD_SPECS, BoardSize
from app.game.coords import hexes_in_bounds
from app.game.ids import TopologyIndex, edge_id, vertex_id
from app.game.placement import (
    check_city,
    check_road,
    check_settlement,
    legal_road_spots,
    legal_settlement_spots,
)
from app.game.placement import GameError
from app.game.state import GameState, PlayerState
from app.game.topology import Topology

STANDARD = Topology(hexes_in_bounds(BOARD_SPECS[BoardSize.STANDARD].bounds))
EXPANDED = Topology(hexes_in_bounds(BOARD_SPECS[BoardSize.EXPANDED].bounds))


def make_state(names):
    players = {n: PlayerState(name=n) for n in names}
    return GameState(order=list(names), players=players, rng=random.Random(0))


@pytest.mark.parametrize("topology", [STANDARD, EXPANDED])
def test_distance_rule_rejects_neighbor_and_accepts_distance_two(topology):
    index = TopologyIndex(topology)
    state = make_state(["A", "B"])
    v0 = topology.vertices[0]
    v0_id = vertex_id(v0)
    state.players["A"].settlements.add(v0_id)

    for neighbor in topology.vertex_neighbors[v0]:
        with pytest.raises(GameError) as exc:
            check_settlement(index, state, "B", vertex_id(neighbor), setup=True)
        assert exc.value.code == "illegal_placement"

    far = next(v for v in topology.vertices if v != v0 and v not in topology.vertex_neighbors[v0])
    check_settlement(index, state, "B", vertex_id(far), setup=True)


@pytest.mark.parametrize("topology", [STANDARD, EXPANDED])
def test_occupied_vertex_rejected_regardless_of_owner(topology):
    index = TopologyIndex(topology)
    state = make_state(["A", "B"])
    v0_id = vertex_id(topology.vertices[0])
    state.players["A"].settlements.add(v0_id)

    with pytest.raises(GameError) as exc:
        check_settlement(index, state, "A", v0_id, setup=True)
    assert exc.value.code == "illegal_placement"
    with pytest.raises(GameError):
        check_settlement(index, state, "B", v0_id, setup=True)


@pytest.mark.parametrize("topology", [STANDARD, EXPANDED])
def test_road_accepted_off_own_settlement_and_own_road(topology):
    index = TopologyIndex(topology)
    state = make_state(["A", "B"])
    v0 = topology.vertices[0]
    v0_id = vertex_id(v0)
    state.players["A"].settlements.add(v0_id)

    e0 = topology.vertex_edges[v0][0]
    check_road(index, state, "A", edge_id(e0), setup=False)
    state.players["A"].roads.add(edge_id(e0))

    other_end = e0[0] if e0[0] != v0 else e0[1]
    e1 = next(e for e in topology.vertex_edges[other_end] if e != e0)
    check_road(index, state, "A", edge_id(e1), setup=False)


@pytest.mark.parametrize("topology", [STANDARD, EXPANDED])
def test_road_rejected_when_floating_or_occupied(topology):
    index = TopologyIndex(topology)
    state = make_state(["A", "B"])
    far_edge = edge_id(topology.edges[-1])

    with pytest.raises(GameError) as exc:
        check_road(index, state, "A", far_edge, setup=False)
    assert exc.value.code == "illegal_placement"

    v0 = topology.vertices[0]
    e0 = topology.vertex_edges[v0][0]
    state.players["A"].settlements.add(vertex_id(v0))
    state.players["B"].roads.add(edge_id(e0))

    with pytest.raises(GameError) as exc:
        check_road(index, state, "A", edge_id(e0), setup=False)
    assert exc.value.code == "illegal_placement"


@pytest.mark.parametrize("topology", [STANDARD, EXPANDED])
def test_road_blocked_through_opponent_settlement(topology):
    index = TopologyIndex(topology)
    state = make_state(["A", "B"])
    v0 = topology.vertices[0]
    v0_id = vertex_id(v0)
    e0 = topology.vertex_edges[v0][0]
    other_end = e0[0] if e0[0] != v0 else e0[1]

    state.players["A"].settlements.add(v0_id)
    state.players["A"].roads.add(edge_id(e0))
    state.players["B"].settlements.add(vertex_id(other_end))

    blocked = next(e for e in topology.vertex_edges[other_end] if e != e0)
    with pytest.raises(GameError) as exc:
        check_road(index, state, "A", edge_id(blocked), setup=False)
    assert exc.value.code == "illegal_placement"


@pytest.mark.parametrize("topology", [STANDARD, EXPANDED])
def test_city_requires_own_settlement(topology):
    index = TopologyIndex(topology)
    state = make_state(["A", "B"])
    v0_id = vertex_id(topology.vertices[0])
    v1_id = vertex_id(topology.vertices[1])
    state.players["A"].settlements.add(v0_id)
    state.players["B"].settlements.add(v1_id)

    check_city(index, state, "A", v0_id)
    with pytest.raises(GameError) as exc:
        check_city(index, state, "A", v1_id)
    assert exc.value.code == "illegal_placement"
    with pytest.raises(GameError):
        check_city(index, state, "A", vertex_id(topology.vertices[2]))


@pytest.mark.parametrize("topology", [STANDARD, EXPANDED])
def test_legal_settlement_spots_shrinks_after_placement(topology):
    index = TopologyIndex(topology)
    state = make_state(["A", "B"])
    before = len(legal_settlement_spots(index, state, "A", setup=True))
    assert before == len(topology.vertices)

    v0 = topology.vertices[0]
    state.players["A"].settlements.add(vertex_id(v0))
    after = legal_settlement_spots(index, state, "B", setup=True)
    assert vertex_id(v0) not in after
    assert all(vertex_id(n) not in after or n == v0 for n in topology.vertex_neighbors[v0])
    assert len(after) < before


@pytest.mark.parametrize("topology", [STANDARD, EXPANDED])
def test_every_setup_legal_spot_has_a_free_incident_edge(topology):
    index = TopologyIndex(topology)
    state = make_state(["A"])
    for vid in legal_settlement_spots(index, state, "A", setup=True):
        assert len(index.vertex_edges[vid]) > 0
