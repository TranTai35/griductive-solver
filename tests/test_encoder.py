import unittest
from itertools import product

from core.models import Character, Clue, Status
from logic.cnf_encoder import CNFEncoder
from logic.semantics import evaluate_clue


class EncoderTests(unittest.TestCase):
    def setUp(self):
        self.characters = {
            "A1": Character("A1", "A", "X"),
            "B1": Character("B1", "B", "Y"),
            "C1": Character("C1", "C", "Z"),
        }
        self.encoder = CNFEncoder(self.characters)

    def _cnf_value(self, clauses, assignment):
        variables = self.encoder.variable_map
        values = {
            variables[cell]: assignment[cell] == Status.CRIMINAL
            for cell in assignment
        }
        return all(any(values[abs(lit)] == (lit > 0) for lit in clause) for clause in clauses)

    def test_all_template_encodings_match_direct_semantics(self):
        region = {"kind": "EXPLICIT", "cells": ["A1", "B1", "C1"]}
        clues = [
            Clue("F", "FACT", {"cell": "A1", "status": "CRIMINAL"}),
            Clue("S", "SAME", {"a": "A1", "b": "B1"}),
            Clue("D", "DIFFERENT", {"a": "A1", "b": "B1"}),
            Clue("E", "EXACTLY", {"k": 2, "region": region}),
            Clue("L", "AT_LEAST", {"k": 2, "region": region}),
            Clue("M", "AT_MOST", {"k": 1, "region": region}),
            Clue("P", "PARITY", {"parity": "ODD", "region": region}),
            Clue("I", "IMPLIES", {"a": "A1", "b": "B1"}),
        ]
        for bits in product((Status.INNOCENT, Status.CRIMINAL), repeat=3):
            assignment = dict(zip(self.characters, bits))
            for clue in clues:
                with self.subTest(bits=bits, clue=clue.type):
                    clauses = self.encoder.encode_clue(clue, 3)
                    self.assertEqual(
                        self._cnf_value(clauses, assignment),
                        evaluate_clue(clue, assignment, 3),
                    )


if __name__ == "__main__":
    unittest.main()
