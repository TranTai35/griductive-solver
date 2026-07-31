from core.models import Status
from core.regions import parse_cell, resolve_region


CORE_TYPES = {"FACT", "SAME", "DIFFERENT", "EXACTLY", "AT_LEAST", "AT_MOST"}
EXTENSION_TYPES = {"PARITY", "IMPLIES"}
COUNT_TYPES = {"EXACTLY", "AT_LEAST", "AT_MOST", "PARITY"}


def validate_clue(clue, size, valid_cells):
    clue_type = clue.type.upper()
    if clue_type not in CORE_TYPES | EXTENSION_TYPES:
        raise ValueError(f"Unsupported clue type: {clue_type}")
    data = clue.data
    if clue_type == "FACT":
        _require_cell(data.get("cell"), size, valid_cells)
        Status(data.get("status"))
    elif clue_type in {"SAME", "DIFFERENT", "IMPLIES"}:
        _require_cell(data.get("a"), size, valid_cells)
        _require_cell(data.get("b"), size, valid_cells)
        if data["a"] == data["b"]:
            raise ValueError(f"{clue_type} requires two distinct cells")
    elif clue_type in COUNT_TYPES:
        region = resolve_region(data.get("region"), size)
        if clue_type == "PARITY":
            if str(data.get("parity", "")).upper() not in {"EVEN", "ODD"}:
                raise ValueError("PARITY must be EVEN or ODD")
        else:
            k = int(data.get("k"))
            if not 0 <= k <= len(region):
                raise ValueError(f"k must be between 0 and {len(region)}")


def _require_cell(cell, size, valid_cells):
    parse_cell(str(cell), size)
    if cell not in valid_cells:
        raise ValueError(f"Unknown character cell: {cell}")


def clue_cells(clue, size):
    data = clue.data
    if clue.type == "FACT":
        return [data["cell"]]
    if clue.type in {"SAME", "DIFFERENT", "IMPLIES"}:
        return [data["a"], data["b"]]
    return resolve_region(data["region"], size)


def evaluate_clue(clue, assignment, size):
    """Direct semantic evaluator; it never calls the CNF encoder."""
    is_criminal = lambda cell: assignment[cell] == Status.CRIMINAL
    data = clue.data
    clue_type = clue.type
    if clue_type == "FACT":
        return assignment[data["cell"]] == Status(data["status"])
    if clue_type == "SAME":
        return is_criminal(data["a"]) == is_criminal(data["b"])
    if clue_type == "DIFFERENT":
        return is_criminal(data["a"]) != is_criminal(data["b"])
    if clue_type == "IMPLIES":
        return (not is_criminal(data["a"])) or is_criminal(data["b"])

    count = sum(is_criminal(cell) for cell in resolve_region(data["region"], size))
    if clue_type == "EXACTLY":
        return count == int(data["k"])
    if clue_type == "AT_LEAST":
        return count >= int(data["k"])
    if clue_type == "AT_MOST":
        return count <= int(data["k"])
    if clue_type == "PARITY":
        return count % 2 == (1 if data["parity"].upper() == "ODD" else 0)
    raise ValueError(f"Unsupported clue type: {clue_type}")

