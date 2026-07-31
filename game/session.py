from dataclasses import dataclass

from core.models import Status, VerdictResult


@dataclass
class TraceEntry:
    step: int
    active_clues: list[str]
    sat_calls: int
    cell: str
    verdict: Status
    revealed_clue: str


class GameSession:
    def __init__(self, engine, agent):
        self.engine = engine
        self.agent = agent
        self.trace = []
        self.analysis = None
        self.refresh()

    def refresh(self):
        self.public = self.engine.get_public_state()
        self.analysis = self.agent.analyze(self.public)

    def submit(self, cell, verdict):
        result, clue = self.engine.submit_verdict(
            cell, verdict, self.analysis.classifications
        )
        if result == VerdictResult.ACCEPTED:
            self.trace.append(
                TraceEntry(
                    step=len(self.trace) + 1,
                    active_clues=[
                        clue.clue_id for clue in self.public.revealed_clues.values()
                    ],
                    sat_calls=self.analysis.stats.sat_calls,
                    cell=cell,
                    verdict=Status(verdict),
                    revealed_clue=clue.clue_id,
                )
            )
            self.refresh()
        return result, clue

    def restart(self):
        self.engine.restart()
        self.trace.clear()
        self.refresh()

