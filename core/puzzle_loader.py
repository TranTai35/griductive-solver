import json
from pathlib import Path

from core.models import Character, Clue, Puzzle, Status
from core.regions import all_cells
from logic.semantics import evaluate_clue, validate_clue


def load_puzzle(path):
    path = Path(path)
    with path.open("r", encoding="utf-8") as stream:
        raw = json.load(stream)

    size = int(raw["size"])
    expected = all_cells(size)
    character_rows = raw["characters"]
    characters = {
        item["cell"]: Character(item["cell"], item["name"], item["profession"])
        for item in character_rows
    }
    if set(characters) != set(expected):
        raise ValueError("Characters must cover every board cell exactly once")

    solution = {cell: Status(value) for cell, value in raw["solution"].items()}
    if set(solution) != set(expected):
        raise ValueError("Solution must cover every board cell exactly once")

    clues = {}
    for cell, item in raw["clues"].items():
        clue = Clue(
            clue_id=item.get("id", f"CLUE_{cell}"),
            type=item["type"].upper(),
            data=item.get("data", {}),
            text=item.get("text", ""),
        )
        validate_clue(clue, size, set(expected))
        clues[cell] = clue
    if set(clues) != set(expected):
        raise ValueError("Every character must own exactly one clue")
    clue_ids = [clue.clue_id for clue in clues.values()]
    if len(clue_ids) != len(set(clue_ids)):
        raise ValueError("Clue identifiers must be unique")
    for cell, clue in clues.items():
        if not evaluate_clue(clue, solution, size):
            raise ValueError(f"Clue owned by {cell} is false under the hidden solution")

    initially_revealed = [str(cell).upper() for cell in raw["initially_revealed"]]
    if not set(initially_revealed) <= set(expected):
        raise ValueError("Initially revealed cells must exist")

    return Puzzle(
        puzzle_id=raw["id"],
        title=raw["title"],
        description=raw.get("description", ""),
        size=size,
        characters=characters,
        solution=solution,
        clues=clues,
        initially_revealed=initially_revealed,
    )
