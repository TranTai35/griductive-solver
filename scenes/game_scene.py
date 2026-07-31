import pygame

from core.game_engine import GameEngine
from core.models import Status, VerdictResult
from core.puzzle_loader import load_puzzle
from game.session import GameSession
from logic.agent import LogicAgent
from logic.semantics import clue_cells
from scenes.base_scene import BaseScene
from ui.button import Button
from ui.avatar_manager import AvatarManager
from ui.text import (
    draw_text,
    draw_wrapped,
    wrap_lines,
)
from ui.theme import (
    ACCENT,
    ACCENT_2,
    BG,
    BORDER,
    CARD_BACK,
    CRIMINAL,
    INNOCENT,
    MUTED,
    PANEL,
    PANEL_2,
    TEXT,
    WARNING,
)


class GameScene(BaseScene):
    def __init__(
        self,
        app,
        puzzle_path,
        mode,
        on_back,
    ):
        super().__init__(app)

        self.puzzle_path = puzzle_path
        self.mode = mode
        self.on_back = on_back

        self.puzzle = load_puzzle(puzzle_path)

        self.session = GameSession(
            GameEngine(self.puzzle),
            LogicAgent(),
        )

        self.avatar_manager = AvatarManager(
            self.puzzle.puzzle_id,
            self.puzzle.characters,
        )

        self.selected_cell = None
        self.highlighted = set()

        self.auto_solving = False
        self.auto_timer = 0.0

        self.flip_progress = {}
        self.card_rects = {}

        # -----------------------------------------------------
        # Message tùy theo mode
        # -----------------------------------------------------

        if self.mode == "play":
            self.message = (
                "Select a face-up clue or an unresolved "
                "character and submit a provable verdict."
            )

        else:
            self.message = (
                "Press START SOLVER to let the Logic Agent "
                "solve this case automatically."
            )

        self.message_color = MUTED

        self._make_buttons()

    # =========================================================
    # BUTTONS
    # =========================================================

    def _make_buttons(self):
        # Các button dùng chung
        self.top_buttons = [
            Button(
                (30, 18, 92, 40),
                "BACK",
                self.on_back,
            ),

            Button(
                (132, 18, 100, 40),
                "RESTART",
                self.restart,
            ),
        ]

        # -----------------------------------------------------
        # PLAY MODE
        # -----------------------------------------------------

        if self.mode == "play":

            self.top_buttons.append(
                Button(
                    (242, 18, 82, 40),
                    "HINT",
                    self.hint,
                )
            )

            self.action_buttons = [
                Button(
                    (780, 682, 190, 48),
                    "CRIMINAL",
                    lambda: self.submit(
                        Status.CRIMINAL
                    ),
                ),

                Button(
                    (980, 682, 190, 48),
                    "INNOCENT",
                    lambda: self.submit(
                        Status.INNOCENT
                    ),
                ),
            ]

        # -----------------------------------------------------
        # SOLVE MODE
        # -----------------------------------------------------

        else:

            self.top_buttons.append(
                Button(
                    (242, 18, 150, 40),
                    "START SOLVER",
                    self.start_auto,
                    accent=True,
                )
            )

            self.action_buttons = []

        self.buttons = (
            self.top_buttons
            + self.action_buttons
        )

    # =========================================================
    # RESTART
    # =========================================================

    def restart(self):
        self.auto_solving = False
        self.auto_timer = 0.0

        self.session.restart()

        self.selected_cell = None

        self.highlighted.clear()
        self.flip_progress.clear()

        if self.mode == "play":
            self._set_message(
                "Puzzle restarted. Select a character and "
                "submit a logically provable verdict.",
                MUTED,
            )

        else:
            self._set_message(
                "Puzzle restarted. Press START SOLVER.",
                MUTED,
            )

    # =========================================================
    # HINT
    # =========================================================

    def hint(self):
        # Hint chỉ dành cho Play mode
        if self.mode != "play":
            return

        move = self.session.agent.next_forced(
            self.session.public,
            self.session.analysis,
        )

        if move is None:
            self._set_message(
                (
                    "No forced verdict is available: "
                    "the public state is UNKNOWN."
                ),
                WARNING,
            )

            return

        cell, verdict = move

        self.selected_cell = cell

        related = []

        for owner, clue in (
            self.session.public
            .revealed_clues
            .items()
        ):
            if cell in clue_cells(
                clue,
                self.session.public.size,
            ):
                related.append(owner)

        clue_hint = ""

        if related:
            clue_hint = (
                " Relevant clue card(s): "
                + ", ".join(related)
                + "."
            )

        self._set_message(
            (
                f"Hint: {cell} can be proved "
                f"{verdict.value}."
                f"{clue_hint}"
            ),
            ACCENT,
        )

    # =========================================================
    # SOLVER
    # =========================================================

    def start_auto(self):
        if self.mode != "solve":
            return

        if self.session.engine.is_solved():
            self._set_message(
                "This case has already been solved.",
                MUTED,
            )

            return

        if self.auto_solving:
            return

        self.auto_solving = True
        self.auto_timer = 0.0

        self._set_message(
            (
                "Solver started. Every verdict is proved "
                "by SAT entailment before being revealed."
            ),
            ACCENT,
        )

    # =========================================================
    # SUBMIT VERDICT
    # =========================================================

    def submit(self, verdict):
        if not self.selected_cell:
            self._set_message(
                "Select an unresolved character first.",
                WARNING,
            )
            return

        if (
            self.selected_cell
            in self.session.public.proved_statuses
        ):
            self._set_message(
                "That character has already been proved.",
                WARNING,
            )
            return

        result, clue = self.session.submit(
            self.selected_cell,
            verdict,
        )

        # -----------------------------------------------------
        # ACCEPTED
        # -----------------------------------------------------

        if result == VerdictResult.ACCEPTED:

            self.flip_progress[
                self.selected_cell
            ] = 0.0

            self._set_message(
                (
                    f"ACCEPTED: "
                    f"{self.selected_cell} "
                    f"is {verdict.value}. "
                    f"Revealed {clue.clue_id}."
                ),
                (
                    INNOCENT
                    if verdict == Status.INNOCENT
                    else CRIMINAL
                ),
            )

            if self.session.engine.is_solved():
                self.auto_solving = False

                self._set_message(
                    (
                        "CASE SOLVED — every verdict "
                        "was logically entailed."
                    ),
                    ACCENT,
                )

        # -----------------------------------------------------
        # NOT PROVABLE
        # -----------------------------------------------------

        elif result == VerdictResult.NOT_PROVABLE:

            self._set_message(
                (
                    "NOT_PROVABLE: both statuses are still "
                    "possible. Nothing was revealed."
                ),
                WARNING,
            )

        # -----------------------------------------------------
        # CONTRADICTED
        # -----------------------------------------------------

        elif result == VerdictResult.CONTRADICTED:

            self._set_message(
                (
                    "CONTRADICTED: the opposite status "
                    "is forced. Nothing was revealed."
                ),
                CRIMINAL,
            )

        # -----------------------------------------------------
        # INCONSISTENT
        # -----------------------------------------------------

        else:

            self._set_message(
                (
                    "INCONSISTENT: the public knowledge "
                    "base is unsatisfiable."
                ),
                CRIMINAL,
            )

    # =========================================================
    # MESSAGE
    # =========================================================

    def _set_message(self, text, color):
        self.message = text
        self.message_color = color

    # =========================================================
    # UPDATE
    # =========================================================

    def update(self, dt):
        # -----------------------------------------------------
        # Card flip animation
        # -----------------------------------------------------

        for cell in list(
            self.flip_progress
        ):
            self.flip_progress[cell] += (
                dt / 0.34
            )

            if (
                self.flip_progress[cell]
                >= 1
            ):
                del self.flip_progress[cell]

        # -----------------------------------------------------
        # Auto solver
        # -----------------------------------------------------

        if not self.auto_solving:
            return

        self.auto_timer -= dt

        if self.auto_timer > 0:
            return

        # Khoảng nghỉ giữa 2 deduction
        self.auto_timer = 0.65

        move = (
            self.session.agent
            .next_forced(
                self.session.public,
                self.session.analysis,
            )
        )

        if move is None:

            self.auto_solving = False

            self._set_message(
                (
                    "Solver stopped: no forced verdict "
                    "is currently available."
                ),
                WARNING,
            )

            return

        self.selected_cell, verdict = move

        self.submit(verdict)

    # =========================================================
    # INPUT
    # =========================================================

    def handle_event(self, event):
        super().handle_event(event)

        # -----------------------------------------------------
        # Keyboard
        # -----------------------------------------------------

        if event.type == pygame.KEYDOWN:

            if event.key == pygame.K_ESCAPE:
                self.on_back()

            elif event.key == pygame.K_r:
                self.restart()

            elif (
                event.key == pygame.K_h
                and self.mode == "play"
            ):
                self.hint()

        # -----------------------------------------------------
        # Mouse
        # -----------------------------------------------------

        if (
            event.type
            == pygame.MOUSEBUTTONDOWN
            and event.button == 1
        ):

            for cell, rect in (
                self.card_rects.items()
            ):

                if not rect.collidepoint(
                    event.pos
                ):
                    continue

                # ---------------------------------------------
                # PLAY MODE
                # ---------------------------------------------

                if self.mode == "play":
                    self.select_card(cell)

                # ---------------------------------------------
                # SOLVE MODE
                # User chỉ được inspect card đã reveal
                # ---------------------------------------------

                else:
                    if (
                        cell
                        in self.session.public
                        .revealed_clues
                    ):
                        self.select_card(cell)

                break

    # =========================================================
    # SELECT CARD
    # =========================================================

    def select_card(self, cell):
        self.selected_cell = cell

        clue = (
            self.session.public
            .revealed_clues
            .get(cell)
        )

        if clue:

            self.highlighted = set(
                clue_cells(
                    clue,
                    self.session.public.size,
                )
            )

            self._set_message(
                (
                    f"Selected {clue.clue_id}; "
                    "referenced cells are highlighted."
                ),
                ACCENT_2,
            )

        else:

            self.highlighted = set()

            if self.mode == "play":

                self._set_message(
                    (
                        f"Selected face-down card {cell}. "
                        "Submit a provable verdict."
                    ),
                    MUTED,
                )

    # =========================================================
    # DRAW
    # =========================================================

    def draw(self, screen):
        screen.fill(BG)

        # -----------------------------------------------------
        # Top buttons
        # -----------------------------------------------------

        for button in self.top_buttons:
            button.draw(screen)

        # -----------------------------------------------------
        # Mode title
        # -----------------------------------------------------

        if self.mode == "play":
            mode_label = "PLAY MODE"
        else:
            mode_label = "SOLVER MODE"

        draw_text(
            screen,
            mode_label,
            (490, 13),
            13,
            ACCENT,
            True,
        )

        draw_text(
            screen,
            self.session.engine.title,
            (490, 32),
            25,
            TEXT,
            True,
        )

        draw_text(
            screen,
            (
                f"{self.puzzle.size}×"
                f"{self.puzzle.size}"
                f"  ·  "
                f"{len(self.session.public.proved_statuses)}"
                f"/{self.puzzle.size ** 2} proved"
            ),
            (490, 61),
            15,
            MUTED,
        )

        self._draw_board(screen)
        self._draw_side_panel(screen)
        self._draw_status_bar(screen)

    # =========================================================
    # BOARD
    # =========================================================

    def _draw_board(self, screen):
        size = self.puzzle.size

        available_w = 700
        available_h = 565

        card = min(
            (
                available_w
                - (size - 1) * 10
            ) // size,
            (
                available_h
                - (size - 1) * 10
            ) // size,
        )

        origin_x = (
            42
            + (
                available_w
                - (
                    card * size
                    + 10 * (size - 1)
                )
            ) // 2
        )

        origin_y = (
            105
            + (
                available_h
                - (
                    card * size
                    + 10 * (size - 1)
                )
            ) // 2
        )

        self.card_rects.clear()

        # Column coordinates
        for col in range(size):

            draw_text(
                screen,
                chr(65 + col),
                (
                    origin_x
                    + col * (card + 10)
                    + card // 2,
                    origin_y - 25,
                ),
                17,
                MUTED,
                True,
                "center",
            )

        # Rows
        for row in range(size):

            draw_text(
                screen,
                str(row + 1),
                (
                    origin_x - 22,
                    origin_y
                    + row * (card + 10)
                    + card // 2,
                ),
                17,
                MUTED,
                True,
                "center",
            )

            for col in range(size):

                cell = (
                    f"{chr(65 + col)}"
                    f"{row + 1}"
                )

                rect = pygame.Rect(
                    origin_x
                    + col * (card + 10),
                    origin_y
                    + row * (card + 10),
                    card,
                    card,
                )

                self.card_rects[
                    cell
                ] = rect

                self._draw_card(
                    screen,
                    cell,
                    rect,
                )

    # =========================================================
    # CARD
    # =========================================================

    def _draw_card(
        self,
        screen,
        cell,
        rect,
    ):
        public = self.session.public

        progress = (
            self.flip_progress
            .get(cell)
        )

        draw_rect = rect.copy()

        show_front = True

        # -----------------------------------------------------
        # Flip animation
        # -----------------------------------------------------

        if progress is not None:

            scale = max(
                0.04,
                abs(
                    1.0
                    - 2.0 * progress
                ),
            )

            draw_rect.width = max(
                4,
                int(
                    rect.width
                    * scale
                ),
            )

            draw_rect.centerx = (
                rect.centerx
            )

            show_front = (
                progress >= 0.5
            )

        # -----------------------------------------------------

        revealed = (
            cell
            in public.revealed_clues
            and show_front
        )

        selected = (
            cell
            == self.selected_cell
        )

        highlighted = (
            cell
            in self.highlighted
        )

        status = (
            public.proved_statuses
            .get(cell)
            if show_front
            else None
        )

        fill = (
            PANEL_2
            if revealed
            else CARD_BACK
        )

        border = (
            ACCENT_2
            if selected
            else (
                ACCENT
                if highlighted
                else BORDER
            )
        )

        if status == Status.CRIMINAL:
            border = CRIMINAL

        elif status == Status.INNOCENT:
            border = INNOCENT

        pygame.draw.rect(
            screen,
            fill,
            draw_rect,
            border_radius=12,
        )

        pygame.draw.rect(
            screen,
            border,
            draw_rect,
            (
                3
                if (
                    selected
                    or highlighted
                    or status
                )
                else 1
            ),
            border_radius=12,
        )

        if draw_rect.width < 35:
            return

        character = (
            public.characters[cell]
        )

        draw_text(
            screen,
            cell,
            (
                draw_rect.x + 9,
                draw_rect.y + 7,
            ),
            12,
            MUTED,
            True,
        )

        # -----------------------------------------------------
        # Revealed
        # -----------------------------------------------------

        if revealed:

            self._draw_revealed_card(
                screen,
                cell,
                draw_rect,
                character,
                public.revealed_clues[
                    cell
                ],
                status,
            )

        # -----------------------------------------------------
        # Hidden
        # -----------------------------------------------------

        else:

            self._draw_character_card(
                screen,
                cell,
                draw_rect,
                character,
                show_question=(
                    not show_front
                ),
            )

    # =========================================================
    # HIDDEN CHARACTER CARD
    # =========================================================

    def _draw_character_card(
        self,
        screen,
        cell,
        rect,
        character,
        show_question=False,
    ):
        if rect.height >= 160:

            avatar_box = (92, 86)
            avatar_offset = 24

            name_offset = 119
            job_offset = 144

            name_size = 18
            job_size = 13

        elif rect.height >= 120:

            avatar_box = (66, 61)
            avatar_offset = 22

            name_offset = 83
            job_offset = 105

            name_size = 15
            job_size = 11

        else:

            avatar_box = (52, 45)
            avatar_offset = 18

            name_offset = 65
            job_offset = 84

            name_size = 13
            job_size = 9

        avatar_y = (
            rect.y
            + avatar_offset
        )

        avatar = (
            self.avatar_manager
            .get(
                cell,
                avatar_box,
            )
        )

        avatar_rect = (
            avatar.get_rect(
                midtop=(
                    rect.centerx,
                    avatar_y,
                )
            )
        )

        screen.blit(
            avatar,
            avatar_rect,
        )

        draw_text(
            screen,
            character.name,
            (
                rect.centerx,
                rect.y
                + name_offset,
            ),
            name_size,
            TEXT,
            True,
            "midtop",
        )

        draw_text(
            screen,
            character.profession,
            (
                rect.centerx,
                rect.y
                + job_offset,
            ),
            job_size,
            MUTED,
            False,
            "midtop",
        )

        if show_question:

            overlay = pygame.Surface(
                rect.size,
                pygame.SRCALPHA,
            )

            overlay.fill(
                (15, 20, 31, 150)
            )

            screen.blit(
                overlay,
                rect,
            )

            draw_text(
                screen,
                "?",
                rect.center,
                28,
                TEXT,
                True,
                "center",
            )

    # =========================================================
    # REVEALED CARD
    # =========================================================

    def _draw_revealed_card(
        self,
        screen,
        cell,
        rect,
        character,
        clue,
        status,
    ):
        if rect.height >= 160:

            header_height = 62
            avatar_size = (42, 42)

            name_offset = 15
            job_offset = 35

            name_size = 15
            job_size = 11
            clue_size = 12

        elif rect.height >= 120:

            header_height = 51
            avatar_size = (31, 31)

            name_offset = 11
            job_offset = 28

            name_size = 12
            job_size = 9
            clue_size = 10

        else:

            header_height = 42
            avatar_size = (25, 25)

            name_offset = 8
            job_offset = 23

            name_size = 10
            job_size = 8
            clue_size = 9

        avatar = (
            self.avatar_manager
            .get(
                cell,
                avatar_size,
            )
        )

        avatar_rect = (
            avatar.get_rect(
                midleft=(
                    rect.x + 40,
                    rect.y
                    + header_height // 2
                    + 2,
                )
            )
        )

        screen.blit(
            avatar,
            avatar_rect,
        )

        identity_x = (
            avatar_rect.right + 7
        )

        draw_text(
            screen,
            character.name,
            (
                identity_x,
                rect.y
                + name_offset,
            ),
            name_size,
            TEXT,
            True,
        )

        draw_text(
            screen,
            character.profession,
            (
                identity_x,
                rect.y
                + job_offset,
            ),
            job_size,
            MUTED,
        )

        divider_y = (
            rect.y
            + header_height
        )

        pygame.draw.line(
            screen,
            BORDER,
            (
                rect.x + 9,
                divider_y,
            ),
            (
                rect.right - 9,
                divider_y,
            ),
            1,
        )

        clue_top = divider_y + 7

        clue_bottom_padding = (
            20
            if status
            else 7
        )

        clue_rect = pygame.Rect(
            rect.x + 9,
            clue_top,
            rect.width - 18,
            max(
                1,
                rect.bottom
                - clue_top
                - clue_bottom_padding,
            ),
        )

        lines = wrap_lines(
            clue.text
            or clue.type,
            clue_rect.width,
            clue_size,
        )

        line_height = (
            clue_size + 3
        )

        max_lines = max(
            1,
            clue_rect.height
            // line_height,
        )

        for index, line in enumerate(
            lines[:max_lines]
        ):

            draw_text(
                screen,
                line,
                (
                    clue_rect.centerx,
                    clue_rect.y
                    + index
                    * line_height,
                ),
                clue_size,
                TEXT,
                False,
                "midtop",
            )

        if status:

            status_color = (
                CRIMINAL
                if status
                == Status.CRIMINAL
                else INNOCENT
            )

            status_label = (
                "CRIMINAL"
                if status
                == Status.CRIMINAL
                else "INNOCENT"
            )

            draw_text(
                screen,
                status_label,
                (
                    rect.centerx,
                    rect.bottom - 12,
                ),
                (
                    10
                    if rect.height >= 160
                    else (
                        9
                        if rect.height >= 120
                        else 8
                    )
                ),
                status_color,
                True,
                "center",
            )

    # =========================================================
    # SIDE PANEL
    # =========================================================

    def _draw_side_panel(
        self,
        screen,
    ):
        panel = pygame.Rect(
            765,
            84,
            485,
            570,
        )

        pygame.draw.rect(
            screen,
            PANEL,
            panel,
            border_radius=16,
        )

        draw_text(
            screen,
            "PUBLIC KNOWLEDGE",
            (
                panel.x + 22,
                panel.y + 18,
            ),
            18,
            ACCENT,
            True,
        )

        clue = (
            self.session.public
            .revealed_clues
            .get(
                self.selected_cell
            )
        )

        # -----------------------------------------------------
        # Selected clue
        # -----------------------------------------------------

        if clue:

            draw_text(
                screen,
                clue.clue_id,
                (
                    panel.x + 22,
                    panel.y + 58,
                ),
                21,
                TEXT,
                True,
            )

            draw_text(
                screen,
                clue.type,
                (
                    panel.right - 22,
                    panel.y + 61,
                ),
                15,
                ACCENT_2,
                True,
                "topright",
            )

            draw_wrapped(
                screen,
                clue.text
                or str(clue.data),
                pygame.Rect(
                    panel.x + 22,
                    panel.y + 94,
                    panel.width - 44,
                    82,
                ),
                18,
                TEXT,
            )

            refs = ", ".join(
                clue_cells(
                    clue,
                    self.session.public.size,
                )
            )

            draw_wrapped(
                screen,
                f"References: {refs}",
                pygame.Rect(
                    panel.x + 22,
                    panel.y + 182,
                    panel.width - 44,
                    48,
                ),
                15,
                MUTED,
            )

        else:

            draw_wrapped(
                screen,
                (
                    "Select a revealed card to inspect "
                    "its clue and highlight every "
                    "referenced cell."
                ),
                pygame.Rect(
                    panel.x + 22,
                    panel.y + 60,
                    panel.width - 44,
                    90,
                ),
                18,
                MUTED,
            )

        # -----------------------------------------------------
        # Analysis metrics
        # -----------------------------------------------------

        analysis = (
            self.session.analysis
        )

        y = panel.y + 255

        draw_text(
            screen,
            "CNF / DPLL METRICS",
            (
                panel.x + 22,
                y,
            ),
            17,
            ACCENT,
            True,
        )

        rows = [
            (
                "Primary variables",
                analysis.primary_variables,
            ),
            (
                "Auxiliary variables",
                analysis.auxiliary_variables,
            ),
            (
                "Active clauses",
                analysis.clauses,
            ),
            (
                "SAT calls (analysis)",
                analysis.stats.sat_calls,
            ),
            (
                "Decisions",
                analysis.stats.decisions,
            ),
            (
                "Propagations",
                analysis.stats.propagations,
            ),
            (
                "Backtracks",
                analysis.stats.backtracks,
            ),
            (
                "Runtime",
                (
                    f"{analysis.stats.runtime_ms:.3f} ms"
                ),
            ),
            (
                "Deduction steps",
                len(self.session.trace),
            ),
        ]

        for index, (
            label,
            value,
        ) in enumerate(rows):

            row_y = (
                y
                + 34
                + index * 27
            )

            draw_text(
                screen,
                label,
                (
                    panel.x + 22,
                    row_y,
                ),
                15,
                MUTED,
            )

            draw_text(
                screen,
                value,
                (
                    panel.right - 22,
                    row_y,
                ),
                15,
                TEXT,
                True,
                "topright",
            )

        # -----------------------------------------------------
        # Current uniqueness
        # -----------------------------------------------------

        unique = (
            self.session.agent
            .uniqueness_check(
                self.session.public
            )
        )

        draw_text(
            screen,
            "Current public KB",
            (
                panel.x + 22,
                panel.bottom - 38,
            ),
            15,
            MUTED,
        )

        draw_text(
            screen,
            unique,
            (
                panel.right - 22,
                panel.bottom - 38,
            ),
            15,
            (
                ACCENT
                if unique == "UNIQUE"
                else WARNING
            ),
            True,
            "topright",
        )

    # =========================================================
    # STATUS BAR
    # =========================================================

    def _draw_status_bar(
        self,
        screen,
    ):
        box = pygame.Rect(
            30,
            682,
            720,
            48,
        )

        pygame.draw.rect(
            screen,
            PANEL,
            box,
            border_radius=9,
        )

        draw_wrapped(
            screen,
            self.message,
            pygame.Rect(
                box.x + 14,
                box.y + 8,
                box.width - 28,
                35,
            ),
            15,
            self.message_color,
            True,
            2,
        )

        # -----------------------------------------------------
        # PLAY MODE:
        # CRIMINAL / INNOCENT buttons
        # -----------------------------------------------------

        if self.mode == "play":

            enabled = (
                self.selected_cell
                is not None
                and self.selected_cell
                not in self.session.public
                .proved_statuses
                and not self.session.engine
                .is_solved()
            )

            for button in (
                self.action_buttons
            ):
                button.enabled = enabled
                button.draw(screen)