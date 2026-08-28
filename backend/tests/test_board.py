from collections import Counter

import pytest

from app.game.board import (
    BOARD_SPECS,
    HOT_NUMBERS,
    MAX_TERRAIN_CLUSTER,
    BoardSize,
    Terrain,
    board_size_for,
    generate_board,
    topology_for,
)

SEEDS = range(60)


def neighbor_map(board):
    return topology_for(board).hex_neighbors


def terrain_by_coord(board):
    return {hex_.coord: hex_.terrain for hex_ in board.hexes}


def number_by_coord(board):
    return {hex_.coord: hex_.number for hex_ in board.hexes}


@pytest.mark.parametrize(
    "player_count,expected",
    [
        (2, BoardSize.STANDARD),
        (3, BoardSize.STANDARD),
        (4, BoardSize.STANDARD),
        (5, BoardSize.EXPANDED),
        (6, BoardSize.EXPANDED),
    ],
)
def test_player_count_selects_board_size(player_count, expected):
    assert board_size_for(player_count) is expected
    assert generate_board(player_count, seed=1).size is expected


@pytest.mark.parametrize("player_count", [0, 1, 7, -3])
def test_player_count_outside_two_to_six_is_rejected(player_count):
    with pytest.raises(ValueError):
        generate_board(player_count, seed=1)


@pytest.mark.parametrize("player_count,hex_count", [(4, 19), (6, 30)])
def test_board_has_the_right_number_of_hexes(player_count, hex_count):
    board = generate_board(player_count, seed=7)
    assert len(board.hexes) == hex_count
    assert len({hex_.coord for hex_ in board.hexes}) == hex_count


@pytest.mark.parametrize("player_count", [4, 6])
def test_terrain_counts_match_the_spec(player_count):
    board = generate_board(player_count, seed=11)
    spec = BOARD_SPECS[board.size]
    counts = Counter(hex_.terrain for hex_ in board.hexes)
    assert counts == Counter(spec.terrain_counts)


@pytest.mark.parametrize("player_count", [4, 6])
def test_number_tokens_match_the_spec_and_skip_deserts(player_count):
    board = generate_board(player_count, seed=13)
    spec = BOARD_SPECS[board.size]
    numbered = [hex_ for hex_ in board.hexes if hex_.number is not None]
    deserts = [hex_ for hex_ in board.hexes if hex_.terrain is Terrain.DESERT]

    assert Counter(hex_.number for hex_ in numbered) == Counter(spec.tokens)
    assert len(numbered) == len(board.hexes) - len(deserts)
    assert all(hex_.number is None for hex_ in deserts)


@pytest.mark.parametrize("player_count", [4, 6])
def test_seven_is_never_placed(player_count):
    board = generate_board(player_count, seed=17)
    assert all(hex_.number != 7 for hex_ in board.hexes)


@pytest.mark.parametrize("player_count", [4, 6])
@pytest.mark.parametrize("seed", SEEDS)
def test_no_two_adjacent_hexes_both_show_six_or_eight(player_count, seed):
    board = generate_board(player_count, seed=seed)
    numbers = number_by_coord(board)
    for coord, adjacent in neighbor_map(board).items():
        if numbers[coord] not in HOT_NUMBERS:
            continue
        assert all(numbers[other] not in HOT_NUMBERS for other in adjacent)


@pytest.mark.parametrize("player_count", [4, 6])
@pytest.mark.parametrize("seed", SEEDS)
def test_no_resource_clusters_beyond_the_limit(player_count, seed):
    board = generate_board(player_count, seed=seed)
    terrain = terrain_by_coord(board)
    adjacency = neighbor_map(board)

    seen = set()
    for start in terrain:
        if start in seen or terrain[start] is Terrain.DESERT:
            continue
        stack = [start]
        seen.add(start)
        size = 0
        while stack:
            current = stack.pop()
            size += 1
            for other in adjacency[current]:
                if other not in seen and terrain[other] is terrain[start]:
                    seen.add(other)
                    stack.append(other)
        assert size <= MAX_TERRAIN_CLUSTER


@pytest.mark.parametrize("player_count", [4, 6])
@pytest.mark.parametrize("seed", SEEDS)
def test_robber_starts_on_a_desert(player_count, seed):
    board = generate_board(player_count, seed=seed)
    assert terrain_by_coord(board)[board.robber] is Terrain.DESERT


@pytest.mark.parametrize("player_count", [4, 6])
def test_same_seed_produces_an_identical_board(player_count):
    assert generate_board(player_count, seed=99) == generate_board(player_count, seed=99)


@pytest.mark.parametrize("player_count", [4, 6])
def test_different_seeds_produce_different_boards(player_count):
    boards = {
        generate_board(player_count, seed=seed).model_dump_json() for seed in SEEDS
    }
    assert len(boards) > len(SEEDS) // 2


def test_boards_are_serializable_and_round_trip():
    board = generate_board(6, seed=23)
    assert board.model_validate_json(board.model_dump_json()) == board
