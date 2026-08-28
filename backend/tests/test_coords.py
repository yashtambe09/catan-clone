import pytest

from app.game.board import BOARD_SPECS, BoardSize
from app.game.coords import (
    Axial,
    Bounds,
    distance,
    hexes_in_bounds,
    neighbors,
    rows,
)

STANDARD_BOUNDS = BOARD_SPECS[BoardSize.STANDARD].bounds
EXPANDED_BOUNDS = BOARD_SPECS[BoardSize.EXPANDED].bounds


def test_axial_s_is_negated_sum():
    assert Axial(2, -3).s == 1
    assert all(h.q + h.r + h.s == 0 for h in hexes_in_bounds(STANDARD_BOUNDS))


def test_every_hex_has_six_neighbors_at_distance_one():
    origin = Axial(0, 0)
    result = neighbors(origin)
    assert len(set(result)) == 6
    assert all(distance(origin, n) == 1 for n in result)


def test_distance_is_symmetric_and_zero_on_self():
    a, b = Axial(-2, 1), Axial(1, 1)
    assert distance(a, b) == distance(b, a) == 3
    assert distance(a, a) == 0


def test_standard_board_is_nineteen_hexes_in_3_4_5_4_3_rows():
    hexes = hexes_in_bounds(STANDARD_BOUNDS)
    assert len(hexes) == 19
    assert [len(row) for row in rows(hexes)] == [3, 4, 5, 4, 3]


def test_expanded_board_is_thirty_hexes_in_3_4_5_6_5_4_3_rows():
    hexes = hexes_in_bounds(EXPANDED_BOUNDS)
    assert len(hexes) == 30
    assert [len(row) for row in rows(hexes)] == [3, 4, 5, 6, 5, 4, 3]


@pytest.mark.parametrize("bounds", [STANDARD_BOUNDS, EXPANDED_BOUNDS])
def test_board_has_no_duplicate_hexes(bounds):
    hexes = hexes_in_bounds(bounds)
    assert len(set(hexes)) == len(hexes)


@pytest.mark.parametrize("bounds", [STANDARD_BOUNDS, EXPANDED_BOUNDS])
def test_board_is_contiguous(bounds):
    hexes = set(hexes_in_bounds(bounds))
    start = next(iter(sorted(hexes)))
    reached = {start}
    stack = [start]
    while stack:
        for neighbor in neighbors(stack.pop()):
            if neighbor in hexes and neighbor not in reached:
                reached.add(neighbor)
                stack.append(neighbor)
    assert reached == hexes


def test_hexes_in_bounds_is_deterministically_ordered():
    assert hexes_in_bounds(EXPANDED_BOUNDS) == hexes_in_bounds(EXPANDED_BOUNDS)


def test_unsatisfiable_bounds_raise():
    with pytest.raises(ValueError):
        hexes_in_bounds(Bounds(q_min=5, q_max=6, r_min=5, r_max=6, s_min=5, s_max=6))
    with pytest.raises(ValueError):
        hexes_in_bounds(
            Bounds(q_min=-6, q_max=-5, r_min=-6, r_max=-5, s_min=-6, s_max=-5)
        )
