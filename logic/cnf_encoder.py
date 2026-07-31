from itertools import combinations, product

from core.models import Status
from core.regions import resolve_region


class CNFEncoder:
    def __init__(self, characters):
        ordered_cells = sorted(
            characters,
            key=lambda cell: (int(cell[1:]), ord(cell[0])),
        )
        self.variable_map = {cell: index + 1 for index, cell in enumerate(ordered_cells)}
        self.primary_variables = len(self.variable_map)
        self.auxiliary_variables = 0

    def encode_public_state(self, public_state):
        clauses = []
        for owner in sorted(public_state.revealed_clues):
            clauses.extend(self.encode_clue(public_state.revealed_clues[owner], public_state.size))
        for cell in sorted(public_state.proved_statuses):
            var = self.variable_map[cell]
            clauses.append([var if public_state.proved_statuses[cell] == Status.CRIMINAL else -var])
        return clauses

    def encode_clue(self, clue, size):
        clue_type = clue.type
        data = clue.data
        var = self.variable_map
        if clue_type == "FACT":
            literal = var[data["cell"]]
            return [[literal if Status(data["status"]) == Status.CRIMINAL else -literal]]
        if clue_type == "SAME":
            a, b = var[data["a"]], var[data["b"]]
            return [[-a, b], [a, -b]]
        if clue_type == "DIFFERENT":
            a, b = var[data["a"]], var[data["b"]]
            return [[a, b], [-a, -b]]
        if clue_type == "IMPLIES":
            return [[-var[data["a"]], var[data["b"]]]]

        variables = [var[cell] for cell in resolve_region(data["region"], size)]
        if clue_type == "EXACTLY":
            k = int(data["k"])
            return self._at_least(variables, k) + self._at_most(variables, k)
        if clue_type == "AT_LEAST":
            return self._at_least(variables, int(data["k"]))
        if clue_type == "AT_MOST":
            return self._at_most(variables, int(data["k"]))
        if clue_type == "PARITY":
            wanted = 1 if data["parity"].upper() == "ODD" else 0
            clauses = []
            # Forbid each complete regional assignment with the wrong parity.
            for bits in product((False, True), repeat=len(variables)):
                if sum(bits) % 2 != wanted:
                    clauses.append([-v if bit else v for v, bit in zip(variables, bits)])
            return clauses
        raise ValueError(f"Unsupported clue type: {clue_type}")

    @staticmethod
    def _at_most(variables, k):
        if k >= len(variables):
            return []
        return [[-value for value in group] for group in combinations(variables, k + 1)]

    @staticmethod
    def _at_least(variables, k):
        if k <= 0:
            return []
        choose = len(variables) - k + 1
        return [list(group) for group in combinations(variables, choose)]

