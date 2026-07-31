import unittest
from pathlib import Path

from core.game_engine import GameEngine
from core.models import PublicState
from core.puzzle_loader import load_puzzle
from game.session import GameSession
from logic.agent import LogicAgent


class PuzzleTests(unittest.TestCase):
    def test_every_sample_is_unique_and_progressively_solvable(self):
        root = Path(__file__).parents[1]
        for path in sorted((root / "puzzles").glob("*.json")):
            with self.subTest(path=path.name):
                puzzle = load_puzzle(path)
                agent = LogicAgent()
                session = GameSession(GameEngine(puzzle), agent)
                while not session.engine.is_solved():
                    move = agent.next_forced(session.public, session.analysis)
                    self.assertIsNotNone(move, "Deduction chain became UNKNOWN")
                    result, _ = session.submit(*move)
                    self.assertEqual(result.value, "ACCEPTED")
                self.assertEqual(len(session.trace), puzzle.size ** 2)
                full_public = PublicState(
                    puzzle.puzzle_id,
                    puzzle.size,
                    dict(puzzle.characters),
                    dict(puzzle.clues),
                )
                self.assertEqual(agent.uniqueness_check(full_public), "UNIQUE")


if __name__ == "__main__":
    unittest.main()

