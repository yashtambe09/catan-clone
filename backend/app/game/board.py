import random
from enum import Enum
from typing import NamedTuple

from pydantic import BaseModel

from app.game.coords import Axial, Bounds, hexes_in_bounds, neighbors
from app.game.ports import Port, generate_ports
from app.game.topology import Topology


class Terrain(str, Enum):
    FOREST = "forest"
    HILLS = "hills"
    PASTURE = "pasture"
    FIELDS = "fields"
    MOUNTAINS = "mountains"
    DESERT = "desert"


class BoardSize(str, Enum):
    STANDARD = "19-hex"
    EXPANDED = "30-hex"


RESOURCE_BY_TERRAIN = {
    Terrain.FOREST: "wood",
    Terrain.HILLS: "brick",
    Terrain.PASTURE: "sheep",
    Terrain.FIELDS: "wheat",
    Terrain.MOUNTAINS: "ore",
}

HOT_NUMBERS = frozenset({6, 8})
MAX_TERRAIN_CLUSTER = 3
# Both layouts are found by rejection sampling. Measured acceptance per shuffle:
# terrain 78.0% (19-hex) / 41.5% (30-hex); numbers 14.9% / 3.0%. The worst case
# leaves a ~4e-14 chance of exhausting MAX_ATTEMPTS.
MAX_ATTEMPTS = 1000


class BoardSpec(NamedTuple):
    bounds: Bounds
    terrain_counts: dict[Terrain, int]
    tokens: tuple[int, ...]
    port_generics: int


BOARD_SPECS = {
    BoardSize.STANDARD: BoardSpec(
        bounds=Bounds(q_min=-2, q_max=2, r_min=-2, r_max=2, s_min=-2, s_max=2),
        terrain_counts={
            Terrain.FOREST: 4,
            Terrain.PASTURE: 4,
            Terrain.FIELDS: 4,
            Terrain.HILLS: 3,
            Terrain.MOUNTAINS: 3,
            Terrain.DESERT: 1,
        },
        tokens=(2, 3, 3, 4, 4, 5, 5, 6, 6, 8, 8, 9, 9, 10, 10, 11, 11, 12),
        port_generics=4,
    ),
    BoardSize.EXPANDED: BoardSpec(
        bounds=Bounds(q_min=-3, q_max=2, r_min=-3, r_max=3, s_min=-2, s_max=3),
        terrain_counts={
            Terrain.FOREST: 6,
            Terrain.PASTURE: 6,
            Terrain.FIELDS: 6,
            Terrain.HILLS: 5,
            Terrain.MOUNTAINS: 5,
            Terrain.DESERT: 2,
        },
        tokens=(
            2, 2,
            3, 3, 3,
            4, 4, 4,
            5, 5, 5,
            6, 6, 6,
            8, 8, 8,
            9, 9, 9,
            10, 10, 10,
            11, 11, 11,
            12, 12,
        ),
        port_generics=6,
    ),
}


class BoardGenerationError(RuntimeError):
    pass


class Hex(BaseModel):
    coord: Axial
    terrain: Terrain
    number: int | None = None


class Board(BaseModel):
    size: BoardSize
    player_count: int
    hexes: list[Hex]
    robber: Axial
    ports: list[Port] = []


def board_size_for(player_count: int) -> BoardSize:
    if not 2 <= player_count <= 6:
        raise ValueError(f"player_count must be between 2 and 6, got {player_count}")
    return BoardSize.STANDARD if player_count <= 4 else BoardSize.EXPANDED


def topology_for(board: Board) -> Topology:
    return Topology([hex_.coord for hex_ in board.hexes])


def largest_terrain_cluster(
    layout: dict[Axial, Terrain], neighbor_map: dict[Axial, list[Axial]]
) -> int:
    seen: set[Axial] = set()
    largest = 0
    for start in layout:
        if start in seen:
            continue
        terrain = layout[start]
        if terrain is Terrain.DESERT:
            continue
        stack = [start]
        seen.add(start)
        size = 0
        while stack:
            current = stack.pop()
            size += 1
            for neighbor in neighbor_map[current]:
                if neighbor not in seen and layout[neighbor] is terrain:
                    seen.add(neighbor)
                    stack.append(neighbor)
        largest = max(largest, size)
    return largest


def has_adjacent_hot_numbers(
    layout: dict[Axial, int], neighbor_map: dict[Axial, list[Axial]]
) -> bool:
    for hex_, number in layout.items():
        if number not in HOT_NUMBERS:
            continue
        for neighbor in neighbor_map[hex_]:
            if layout.get(neighbor) in HOT_NUMBERS:
                return True
    return False


def _place_terrain(
    coords: list[Axial],
    neighbor_map: dict[Axial, list[Axial]],
    spec: BoardSpec,
    rng: random.Random,
    seed: int | None,
) -> tuple[dict[Axial, Terrain], int]:
    pool: list[Terrain] = []
    for terrain, count in spec.terrain_counts.items():
        pool.extend([terrain] * count)
    if len(pool) != len(coords):
        raise BoardGenerationError(
            f"terrain pool has {len(pool)} tiles but board has {len(coords)} hexes"
        )

    for attempt in range(1, MAX_ATTEMPTS + 1):
        rng.shuffle(pool)
        layout = dict(zip(coords, pool))
        if largest_terrain_cluster(layout, neighbor_map) <= MAX_TERRAIN_CLUSTER:
            return layout, attempt
    raise BoardGenerationError(
        f"no terrain layout satisfied the clustering limit in {MAX_ATTEMPTS} attempts (seed={seed})"
    )


def _place_numbers(
    coords: list[Axial],
    neighbor_map: dict[Axial, list[Axial]],
    terrain: dict[Axial, Terrain],
    spec: BoardSpec,
    rng: random.Random,
    seed: int | None,
) -> tuple[dict[Axial, int], int]:
    targets = [c for c in coords if terrain[c] is not Terrain.DESERT]
    tokens = list(spec.tokens)
    if len(tokens) != len(targets):
        raise BoardGenerationError(
            f"token pool has {len(tokens)} tokens but board has {len(targets)} non-desert hexes"
        )

    for attempt in range(1, MAX_ATTEMPTS + 1):
        rng.shuffle(tokens)
        layout = dict(zip(targets, tokens))
        if not has_adjacent_hot_numbers(layout, neighbor_map):
            return layout, attempt
    raise BoardGenerationError(
        f"no number layout avoided adjacent 6/8 in {MAX_ATTEMPTS} attempts (seed={seed})"
    )


def generate_board(player_count: int, seed: int | None = None) -> Board:
    size = board_size_for(player_count)
    spec = BOARD_SPECS[size]
    rng = random.Random(seed)

    coords = hexes_in_bounds(spec.bounds)
    coord_set = set(coords)
    neighbor_map = {
        coord: [n for n in neighbors(coord) if n in coord_set] for coord in coords
    }

    terrain, _ = _place_terrain(coords, neighbor_map, spec, rng, seed)
    numbers, _ = _place_numbers(coords, neighbor_map, terrain, spec, rng, seed)

    deserts = sorted(c for c in coords if terrain[c] is Terrain.DESERT)

    topology = Topology(coords)
    kinds = [None] * spec.port_generics + list(RESOURCE_BY_TERRAIN.values())
    ports = generate_ports(topology, kinds, rng)

    return Board(
        size=size,
        player_count=player_count,
        hexes=[
            Hex(coord=coord, terrain=terrain[coord], number=numbers.get(coord))
            for coord in coords
        ],
        robber=rng.choice(deserts),
        ports=ports,
    )
