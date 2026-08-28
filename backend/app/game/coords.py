from typing import NamedTuple


class Axial(NamedTuple):
    q: int
    r: int

    @property
    def s(self) -> int:
        return -self.q - self.r


# Cyclic order (E, NE, NW, W, SW, SE). Consecutive entries share a hex corner,
# which is what topology.py relies on to enumerate vertices.
DIRECTIONS = (
    Axial(1, 0),
    Axial(1, -1),
    Axial(0, -1),
    Axial(-1, 0),
    Axial(-1, 1),
    Axial(0, 1),
)


class Bounds(NamedTuple):
    q_min: int
    q_max: int
    r_min: int
    r_max: int
    s_min: int
    s_max: int


def add(a: Axial, b: Axial) -> Axial:
    return Axial(a.q + b.q, a.r + b.r)


def neighbors(hex_: Axial) -> tuple[Axial, ...]:
    return tuple(add(hex_, direction) for direction in DIRECTIONS)


def distance(a: Axial, b: Axial) -> int:
    return (abs(a.q - b.q) + abs(a.r - b.r) + abs(a.s - b.s)) // 2


def hexes_in_bounds(bounds: Bounds) -> list[Axial]:
    if bounds.q_min + bounds.r_min + bounds.s_min > 0:
        raise ValueError(f"unsatisfiable hex bounds (minimums exceed 0): {bounds}")
    if bounds.q_max + bounds.r_max + bounds.s_max < 0:
        raise ValueError(f"unsatisfiable hex bounds (maximums below 0): {bounds}")

    hexes = []
    for r in range(bounds.r_min, bounds.r_max + 1):
        # s = -q-r, so bounding s bounds q from both sides for this row.
        q_lo = max(bounds.q_min, -bounds.s_max - r)
        q_hi = min(bounds.q_max, -bounds.s_min - r)
        for q in range(q_lo, q_hi + 1):
            hexes.append(Axial(q, r))
    return hexes


def rows(hexes: list[Axial]) -> list[list[Axial]]:
    grouped: dict[int, list[Axial]] = {}
    for hex_ in hexes:
        grouped.setdefault(hex_.r, []).append(hex_)
    return [sorted(grouped[r]) for r in sorted(grouped)]
