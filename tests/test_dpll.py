import unittest

from logic.dpll import DPLLSolver


class DPLLTests(unittest.TestCase):
    def test_sat_returns_complete_assignment(self):
        result = DPLLSolver().solve([[1, 2], [-1, 2]], 2)
        self.assertTrue(result.satisfiable)
        self.assertEqual(set(result.assignment), {1, 2})
        self.assertTrue(result.assignment[2])

    def test_unsat_detected(self):
        result = DPLLSolver().solve([[1], [-1]], 1)
        self.assertFalse(result.satisfiable)

    def test_assumption(self):
        solver = DPLLSolver()
        self.assertFalse(solver.solve([[1]], 1, assumptions=[-1]).satisfiable)


if __name__ == "__main__":
    unittest.main()

