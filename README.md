# Griductive Solver

Griductive Solver is a playable 2D deduction game built with Python and Pygame. It follows the no-guess rule from HCMUS CSC14003 Project 2: a character may be called **CRIMINAL** or **INNOCENT** only when that verdict is logically entailed by currently public clues.

The project mirrors the modular organization of the earlier Bloxorz Solver while replacing its 3D Ursina layer with a Pygame desktop interface.

## Features

- Four sample cases: two 3×3 and two 4×4 puzzles.
- Manual play with `NOT_PROVABLE` and `CONTRADICTED` rejection states.
- Progressive card reveal; hidden clues never enter the active knowledge base.
- Selectable clues and visual highlighting of referenced cells.
- Fifty character avatars loaded from `assets/sprites/avatars`.
- Unique, stable avatar assignment for every character in a grid.
- A compact avatar/name/profession header when a card reveals its clue.
- Green borders for proved Innocents and red borders for proved Criminals.
- Load, Restart, Hint, and animated Auto Solve controls.
- Automatic CNF encoder for `FACT`, `SAME`, `DIFFERENT`, `EXACTLY`, `AT_LEAST`, and `AT_MOST`.
- Two extensions: `PARITY` and `IMPLIES`.
- Direct semantic evaluator for every clue type.
- Self-implemented deterministic DPLL with unit propagation, conflict detection, branching, and backtracking.
- Entailment classification through SAT under opposite assumptions.
- Uniqueness checking, deduction traces, experiment CSV output, and unit tests.

## Architecture

```text
griductive-solver/
├── algorithms/              # compatibility notes / algorithm-facing package
├── core/                    # puzzle models, loader, regions, private GameEngine
├── game/                    # playable session and deduction trace
├── logic/                   # CNF encoder, DPLL, semantic evaluator, LogicAgent
├── puzzles/                 # structured JSON cases
├── scenes/                  # menu, case select, tutorial, game screen
├── tests/                   # DPLL, encoder, and end-to-end puzzle tests
├── ui/                      # reusable Pygame widgets and theme
├── app_controller.py        # screen transitions and global event loop
├── main.py
├── run_experiments.py
└── requirements.txt
```

`GameEngine` owns the hidden solution and all unrevealed clues. `LogicAgent` is constructed separately and receives only a copied `PublicState`. It therefore cannot use hidden labels to produce a hint or verdict.

Avatar assignment is handled only by `ui/avatar_manager.py`. It deterministically
shuffles the available PNG files using the puzzle ID, then assigns one distinct
file to each cell. Restarting a puzzle keeps the same faces, and no avatar is
reused inside the same grid. Add more `.png` files to
`assets/sprites/avatars/` to extend the pool.

## Installation

Python 3.10 or newer is recommended.

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

macOS/Linux:

```bash
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

## Controls

| Input | Action |
|---|---|
| Left click a card | Select a character or inspect a public clue |
| Criminal / Innocent buttons | Submit a verdict for the selected card |
| `H` | Request a no-guess hint |
| `R` | Restart the current case |
| `Esc` | Return to case selection |

## Experiments and Tests

Generate metrics and complete deduction traces:

```bash
python run_experiments.py
```

Results are written to `output/experiments.csv` and `output/deduction_traces.json`.

Run all tests:

```bash
python -m unittest discover -s tests -v
```

## Puzzle JSON

Every card has a character and a structured clue. Regions support:

- `ROW`
- `COLUMN`
- `NEIGHBORS`
- `EXPLICIT`
- `CORNERS` (advanced region)
- `BOUNDARY` (advanced region)

To add a case, copy a file in `puzzles/`, keep one clue per cell, ensure every clue is true under the complete solution, and choose enough initially revealed clues for at least one forced first verdict. The loader validates cells, clue parameters, duplicate clue IDs, and clue truth.

## Important Logic Rule

A satisfying assignment is only one possible model. For character `Ci`:

- `KB ∧ ¬Ci` UNSAT means `Ci` is forced Criminal.
- `KB ∧ Ci` UNSAT means `Ci` is forced Innocent.
- If both are SAT, the verdict is Unknown and the game refuses to reveal the card.
