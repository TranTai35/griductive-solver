from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Status(str, Enum):
    CRIMINAL = "CRIMINAL"
    INNOCENT = "INNOCENT"
    UNKNOWN = "UNKNOWN"


class VerdictResult(str, Enum):
    ACCEPTED = "ACCEPTED"
    NOT_PROVABLE = "NOT_PROVABLE"
    CONTRADICTED = "CONTRADICTED"
    INCONSISTENT = "INCONSISTENT"


@dataclass(frozen=True)
class Character:
    cell_id: str
    name: str
    profession: str


@dataclass(frozen=True)
class Clue:
    clue_id: str
    type: str
    data: dict[str, Any]
    text: str = ""


@dataclass
class Puzzle:
    puzzle_id: str
    title: str
    size: int
    characters: dict[str, Character]
    solution: dict[str, Status]
    clues: dict[str, Clue]
    initially_revealed: list[str]
    description: str = ""


@dataclass
class PublicState:
    puzzle_id: str
    size: int
    characters: dict[str, Character]
    revealed_clues: dict[str, Clue] = field(default_factory=dict)
    proved_statuses: dict[str, Status] = field(default_factory=dict)

    def clone(self):
        return PublicState(
            puzzle_id=self.puzzle_id,
            size=self.size,
            characters=dict(self.characters),
            revealed_clues=dict(self.revealed_clues),
            proved_statuses=dict(self.proved_statuses),
        )


@dataclass
class SolverStats:
    sat_calls: int = 0
    decisions: int = 0
    propagations: int = 0
    backtracks: int = 0
    runtime_ms: float = 0.0

    def add(self, other):
        self.sat_calls += 1
        self.decisions += other.decisions
        self.propagations += other.propagations
        self.backtracks += other.backtracks
        self.runtime_ms += other.runtime_ms

