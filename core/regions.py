import re


CELL_PATTERN = re.compile(r"^[A-Z][1-9][0-9]*$")


def all_cells(size):
    return [f"{chr(65 + col)}{row + 1}" for row in range(size) for col in range(size)]


def parse_cell(cell_id, size):
    if not isinstance(cell_id, str) or not CELL_PATTERN.match(cell_id):
        raise ValueError(f"Invalid cell identifier: {cell_id!r}")
    col = ord(cell_id[0]) - 65
    row = int(cell_id[1:]) - 1
    if not (0 <= row < size and 0 <= col < size):
        raise ValueError(f"Cell {cell_id} is outside the {size}x{size} board")
    return row, col


def resolve_region(region, size):
    if not isinstance(region, dict):
        raise ValueError("Region must be an object")
    kind = str(region.get("kind", "")).upper()
    cells = all_cells(size)

    if kind == "ROW":
        row = int(region["index"])
        result = [cell for cell in cells if int(cell[1:]) == row]
    elif kind == "COLUMN":
        column = str(region["index"]).upper()
        result = [cell for cell in cells if cell[0] == column]
    elif kind == "NEIGHBORS":
        center = str(region["cell"]).upper()
        center_row, center_col = parse_cell(center, size)
        result = []
        for cell in cells:
            row, col = parse_cell(cell, size)
            if cell != center and abs(row - center_row) <= 1 and abs(col - center_col) <= 1:
                result.append(cell)
    elif kind == "EXPLICIT":
        result = [str(cell).upper() for cell in region.get("cells", [])]
    elif kind == "CORNERS":
        result = [f"A1", f"{chr(64 + size)}1", f"A{size}", f"{chr(64 + size)}{size}"]
    elif kind == "BOUNDARY":
        result = []
        for cell in cells:
            row, col = parse_cell(cell, size)
            if row in (0, size - 1) or col in (0, size - 1):
                result.append(cell)
    else:
        raise ValueError(f"Unsupported region kind: {kind}")

    if len(result) != len(set(result)):
        raise ValueError("A region cannot contain duplicate cells")
    for cell in result:
        parse_cell(cell, size)
    if not result:
        raise ValueError("A region cannot be empty")
    return result

