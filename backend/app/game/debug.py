from app.game.board import Board, Terrain
from app.game.coords import rows

TERRAIN_ABBR = {
    Terrain.FOREST: "FOR",
    Terrain.HILLS: "HIL",
    Terrain.PASTURE: "PAS",
    Terrain.FIELDS: "FLD",
    Terrain.MOUNTAINS: "MTN",
    Terrain.DESERT: "DES",
}


def render_ascii(board: Board) -> str:
    by_coord = {hex_.coord: hex_ for hex_ in board.hexes}
    columns = {coord: 2 * coord.q + coord.r for coord in by_coord}
    min_column = min(columns.values())

    lines = []
    for row in rows(list(by_coord)):
        indent = " " * ((columns[row[0]] - min_column) * 4)
        cells = []
        for coord in row:
            hex_ = by_coord[coord]
            number = f"{hex_.number:>2}" if hex_.number is not None else " -"
            robber = "*" if coord == board.robber else " "
            cells.append(f"{TERRAIN_ABBR[hex_.terrain]}{number}{robber}")
        lines.append(indent + " ".join(cells))
    return "\n".join(lines)
