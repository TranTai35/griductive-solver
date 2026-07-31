from core.models import PublicState, Status, VerdictResult


class GameEngine:
    """Private authority. Only this class may see the complete puzzle."""

    def __init__(self, puzzle):
        self._puzzle = puzzle
        self._public = PublicState(
            puzzle_id=puzzle.puzzle_id,
            size=puzzle.size,
            characters=dict(puzzle.characters),
        )
        self.restart()

    @property
    def title(self):
        return self._puzzle.title

    @property
    def description(self):
        return self._puzzle.description

    def restart(self):
        self._public.revealed_clues.clear()
        self._public.proved_statuses.clear()
        for cell in self._puzzle.initially_revealed:
            self._public.revealed_clues[cell] = self._puzzle.clues[cell]

    def get_public_state(self):
        return self._public.clone()

    def submit_verdict(self, cell, proposed, classification):
        """classification comes from LogicAgent, which only received public state."""
        proposed = Status(proposed)
        forced = classification.get(cell, Status.UNKNOWN)
        if forced == Status.UNKNOWN:
            return VerdictResult.NOT_PROVABLE, None
        if forced != proposed:
            return VerdictResult.CONTRADICTED, None
        # A correct entailment must agree with a valid puzzle's private solution.
        if self._puzzle.solution[cell] != proposed:
            return VerdictResult.INCONSISTENT, None
        self._public.proved_statuses[cell] = proposed
        self._public.revealed_clues[cell] = self._puzzle.clues[cell]
        return VerdictResult.ACCEPTED, self._puzzle.clues[cell]

    def is_solved(self):
        return len(self._public.proved_statuses) == len(self._puzzle.characters)

