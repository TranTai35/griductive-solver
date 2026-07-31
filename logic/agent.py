from dataclasses import dataclass

from core.models import SolverStats, Status
from logic.cnf_encoder import CNFEncoder
from logic.dpll import DPLLSolver


@dataclass
class Analysis:
    classifications: dict[str, Status]
    clauses: int
    primary_variables: int
    auxiliary_variables: int
    stats: SolverStats
    inconsistent: bool = False


class LogicAgent:
    """Consumes PublicState only. It has no reference to Puzzle or GameEngine."""

    def __init__(self):
        self.solver = DPLLSolver()

    def analyze(self, public_state):
        encoder = CNFEncoder(public_state.characters)
        clauses = encoder.encode_public_state(public_state)
        total = SolverStats()
        base = self.solver.solve(clauses, encoder.primary_variables)
        total.add(base.stats)
        if not base.satisfiable:
            return Analysis(
                {}, len(clauses), encoder.primary_variables,
                encoder.auxiliary_variables, total, True
            )

        classifications = {}
        ordered = sorted(
            public_state.characters,
            key=lambda cell: (int(cell[1:]), cell[0]),
        )
        for cell in ordered:
            if cell in public_state.proved_statuses:
                classifications[cell] = public_state.proved_statuses[cell]
                continue
            variable = encoder.variable_map[cell]
            assume_innocent = self.solver.solve(
                clauses, encoder.primary_variables, assumptions=[-variable]
            )
            total.add(assume_innocent.stats)
            assume_criminal = self.solver.solve(
                clauses, encoder.primary_variables, assumptions=[variable]
            )
            total.add(assume_criminal.stats)
            if not assume_innocent.satisfiable and assume_criminal.satisfiable:
                classifications[cell] = Status.CRIMINAL
            elif assume_innocent.satisfiable and not assume_criminal.satisfiable:
                classifications[cell] = Status.INNOCENT
            else:
                classifications[cell] = Status.UNKNOWN
        return Analysis(
            classifications, len(clauses), encoder.primary_variables,
            encoder.auxiliary_variables, total
        )

    def next_forced(self, public_state, analysis=None):
        analysis = analysis or self.analyze(public_state)
        for cell in sorted(
            public_state.characters,
            key=lambda value: (int(value[1:]), value[0]),
        ):
            if (
                cell not in public_state.proved_statuses
                and analysis.classifications.get(cell, Status.UNKNOWN) != Status.UNKNOWN
            ):
                return cell, analysis.classifications[cell]
        return None

    def uniqueness_check(self, public_state):
        encoder = CNFEncoder(public_state.characters)
        clauses = encoder.encode_public_state(public_state)
        first = self.solver.solve(clauses, encoder.primary_variables)
        if not first.satisfiable:
            return "INCONSISTENT"
        blocking = [
            -variable if value else variable
            for variable, value in sorted(first.assignment.items())
            if variable <= encoder.primary_variables
        ]
        second = self.solver.solve(
            clauses + [blocking],
            encoder.primary_variables,
        )
        return "UNIQUE" if not second.satisfiable else "MULTIPLE"

