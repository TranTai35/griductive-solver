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
from ui.text import draw_text, draw_wrapped, wrap_lines
from ui.theme import (
    ACCENT, ACCENT_2, BG, BORDER, CARD_BACK, CRIMINAL, INNOCENT,
    MUTED, PANEL, PANEL_2, TEXT, WARNING,
)


class GameScene(BaseScene):
    def __init__(self, app, puzzle_path, on_back):
        super().__init__(app)
        self.puzzle_path = puzzle_path
        self.on_back = on_back
        self.puzzle = load_puzzle(puzzle_path)
        self.session = GameSession(GameEngine(self.puzzle), LogicAgent())
        self.avatar_manager = AvatarManager(
            self.puzzle.puzzle_id,
            self.puzzle.characters,
        )
        self.selected_cell = None
        self.highlighted = set()
        self.message = "Select a face-up clue or an unresolved character."
        self.message_color = MUTED
        self.auto_solving = False
        self.auto_timer = 0.0
        self.flip_progress = {}
        self.card_rects = {}
        self._make_buttons()

    def _make_buttons(self):
        self.buttons = [
            Button((30, 18, 92, 40), "LOAD", self.on_back),
            Button((132, 18, 100, 40), "RESTART", self.restart),
            Button((242, 18, 82, 40), "HINT", self.hint),
            Button((334, 18, 132, 40), "AUTO SOLVE", self.start_auto, accent=True),
            Button((780, 682, 190, 48), "CRIMINAL", lambda: self.submit(Status.CRIMINAL)),
            Button((980, 682, 190, 48), "INNOCENT", lambda: self.submit(Status.INNOCENT)),
        ]

    def restart(self):
        self.auto_solving = False
        self.session.restart()
        self.selected_cell = None
        self.highlighted.clear()
        self.flip_progress.clear()
        self._set_message("Puzzle restarted.", MUTED)

    def hint(self):
        move = self.session.agent.next_forced(self.session.public, self.session.analysis)
        if move is None:
            self._set_message("No forced verdict is available: the public state is UNKNOWN.", WARNING)
            return
        cell, verdict = move
        self.selected_cell = cell
        related = []
        for owner, clue in self.session.public.revealed_clues.items():
            if cell in clue_cells(clue, self.session.public.size):
                related.append(owner)
        clue_hint = f" Relevant clue card(s): {', '.join(related)}." if related else ""
        self._set_message(f"Hint: {cell} can be proved {verdict.value}.{clue_hint}", ACCENT)

    def start_auto(self):
        self.auto_solving = True
        self.auto_timer = 0.0
        self._set_message("Auto Solve started. Every move is proved by SAT entailment.", ACCENT)

    def submit(self, verdict):
        if not self.selected_cell:
            self._set_message("Select an unresolved character first.", WARNING)
            return
        if self.selected_cell in self.session.public.proved_statuses:
            self._set_message("That character has already been proved.", WARNING)
            return
        result, clue = self.session.submit(self.selected_cell, verdict)
        if result == VerdictResult.ACCEPTED:
            self.flip_progress[self.selected_cell] = 0.0
            self._set_message(
                f"ACCEPTED: {self.selected_cell} is {verdict.value}. Revealed {clue.clue_id}.",
                INNOCENT if verdict == Status.INNOCENT else CRIMINAL,
            )
            if self.session.engine.is_solved():
                self.auto_solving = False
                self._set_message("CASE SOLVED — every verdict was logically entailed.", ACCENT)
        elif result == VerdictResult.NOT_PROVABLE:
            self._set_message("NOT_PROVABLE: both statuses are still possible. Nothing was revealed.", WARNING)
        elif result == VerdictResult.CONTRADICTED:
            self._set_message("CONTRADICTED: the opposite status is forced. Nothing was revealed.", CRIMINAL)
        else:
            self._set_message("INCONSISTENT: the public knowledge base is unsatisfiable.", CRIMINAL)

    def _set_message(self, text, color):
        self.message = text
        self.message_color = color

    def update(self, dt):
        for cell in list(self.flip_progress):
            self.flip_progress[cell] += dt / 0.34
            if self.flip_progress[cell] >= 1:
                del self.flip_progress[cell]
        if not self.auto_solving:
            return
        self.auto_timer -= dt
        if self.auto_timer > 0:
            return
        self.auto_timer = 0.65
        move = self.session.agent.next_forced(self.session.public, self.session.analysis)
        if move is None:
            self.auto_solving = False
            self._set_message("Auto Solve stopped: no forced verdict is currently available.", WARNING)
            return
        self.selected_cell, verdict = move
        self.submit(verdict)

    def handle_event(self, event):
        super().handle_event(event)
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.on_back()
            elif event.key == pygame.K_r:
                self.restart()
            elif event.key == pygame.K_h:
                self.hint()
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for cell, rect in self.card_rects.items():
                if rect.collidepoint(event.pos):
                    self.select_card(cell)
                    break

    def select_card(self, cell):
        self.selected_cell = cell
        clue = self.session.public.revealed_clues.get(cell)
        self.highlighted = set(clue_cells(clue, self.session.public.size)) if clue else set()
        if clue:
            self._set_message(f"Selected {clue.clue_id}; referenced cells are highlighted.", ACCENT_2)
        else:
            self._set_message(f"Selected face-down card {cell}. Submit a provable verdict.", MUTED)

    def draw(self, screen):
        screen.fill(BG)
        for button in self.buttons[:4]:
            button.draw(screen)
        draw_text(screen, self.session.engine.title, (490, 20), 28, TEXT, True)
        draw_text(
            screen,
            f"{self.puzzle.size}×{self.puzzle.size}  ·  {len(self.session.public.proved_statuses)}/{self.puzzle.size ** 2} proved",
            (490, 51),
            15,
            MUTED,
        )
        self._draw_board(screen)
        self._draw_side_panel(screen)
        self._draw_status_bar(screen)

    def _draw_board(self, screen):
        size = self.puzzle.size
        available_w, available_h = 700, 565
        card = min((available_w - (size - 1) * 10) // size, (available_h - (size - 1) * 10) // size)
        origin_x = 42 + (available_w - (card * size + 10 * (size - 1))) // 2
        origin_y = 105 + (available_h - (card * size + 10 * (size - 1))) // 2
        self.card_rects.clear()
        for col in range(size):
            draw_text(screen, chr(65 + col), (origin_x + col * (card + 10) + card // 2, origin_y - 25), 17, MUTED, True, "center")
        for row in range(size):
            draw_text(screen, str(row + 1), (origin_x - 22, origin_y + row * (card + 10) + card // 2), 17, MUTED, True, "center")
            for col in range(size):
                cell = f"{chr(65 + col)}{row + 1}"
                rect = pygame.Rect(origin_x + col * (card + 10), origin_y + row * (card + 10), card, card)
                self.card_rects[cell] = rect
                self._draw_card(screen, cell, rect)

    def _draw_card(self, screen, cell, rect):
        public = self.session.public
        progress = self.flip_progress.get(cell)
        draw_rect = rect.copy()
        show_front = True
        if progress is not None:
            scale = max(0.04, abs(1.0 - 2.0 * progress))
            draw_rect.width = max(4, int(rect.width * scale))
            draw_rect.centerx = rect.centerx
            show_front = progress >= 0.5
        revealed = cell in public.revealed_clues and show_front
        selected = cell == self.selected_cell
        highlighted = cell in self.highlighted
        status = public.proved_statuses.get(cell) if show_front else None
        fill = PANEL_2 if revealed else CARD_BACK
        border = ACCENT_2 if selected else (ACCENT if highlighted else BORDER)
        if status == Status.CRIMINAL:
            border = CRIMINAL
        elif status == Status.INNOCENT:
            border = INNOCENT
        pygame.draw.rect(screen, fill, draw_rect, border_radius=12)
        pygame.draw.rect(screen, border, draw_rect, 3 if selected or highlighted or status else 1, border_radius=12)
        if draw_rect.width < 35:
            return
        character = public.characters[cell]
        draw_text(screen, cell, (draw_rect.x + 9, draw_rect.y + 7), 12, MUTED, True)
        if revealed:
            self._draw_revealed_card(
                screen,
                cell,
                draw_rect,
                character,
                public.revealed_clues[cell],
                status,
            )
        else:
            self._draw_character_card(
                screen,
                cell,
                draw_rect,
                character,
                show_question=not show_front,
            )

    def _draw_character_card(self, screen, cell, rect, character, show_question=False):
        """Large avatar, name, and profession for a card without a visible clue."""
        if rect.height >= 160:
            avatar_box, avatar_offset = (92, 86), 24
            name_offset, job_offset = 119, 144
            name_size, job_size = 18, 13
        elif rect.height >= 120:
            avatar_box, avatar_offset = (66, 61), 22
            name_offset, job_offset = 83, 105
            name_size, job_size = 15, 11
        else:
            avatar_box, avatar_offset = (52, 45), 18
            name_offset, job_offset = 65, 84
            name_size, job_size = 13, 9

        avatar_y = rect.y + avatar_offset
        avatar = self.avatar_manager.get(cell, avatar_box)
        avatar_rect = avatar.get_rect(midtop=(rect.centerx, avatar_y))
        screen.blit(avatar, avatar_rect)

        draw_text(
            screen,
            character.name,
            (rect.centerx, rect.y + name_offset),
            name_size,
            TEXT,
            True,
            "midtop",
        )
        draw_text(
            screen,
            character.profession,
            (rect.centerx, rect.y + job_offset),
            job_size,
            MUTED,
            False,
            "midtop",
        )
        if show_question:
            overlay = pygame.Surface(rect.size, pygame.SRCALPHA)
            overlay.fill((15, 20, 31, 150))
            screen.blit(overlay, rect)
            draw_text(screen, "?", rect.center, 28, TEXT, True, "center")

    def _draw_revealed_card(self, screen, cell, rect, character, clue, status):
        """Compact identity header on top; the clue occupies the remaining area."""
        if rect.height >= 160:
            header_height, avatar_size = 62, (42, 42)
            name_offset, job_offset = 15, 35
            name_size, job_size, clue_size = 15, 11, 12
        elif rect.height >= 120:
            header_height, avatar_size = 51, (31, 31)
            name_offset, job_offset = 11, 28
            name_size, job_size, clue_size = 12, 9, 10
        else:
            header_height, avatar_size = 42, (25, 25)
            name_offset, job_offset = 8, 23
            name_size, job_size, clue_size = 10, 8, 9

        avatar = self.avatar_manager.get(cell, avatar_size)
        avatar_rect = avatar.get_rect(
            midleft=(rect.x + 40, rect.y + header_height // 2 + 2)
        )
        screen.blit(avatar, avatar_rect)

        identity_x = avatar_rect.right + 7
        draw_text(
            screen,
            character.name,
            (identity_x, rect.y + name_offset),
            name_size,
            TEXT,
            True,
        )
        draw_text(
            screen,
            character.profession,
            (identity_x, rect.y + job_offset),
            job_size,
            MUTED,
        )

        divider_y = rect.y + header_height
        pygame.draw.line(
            screen,
            BORDER,
            (rect.x + 9, divider_y),
            (rect.right - 9, divider_y),
            1,
        )

        clue_top = divider_y + 7
        clue_bottom_padding = 20 if status else 7
        clue_rect = pygame.Rect(
            rect.x + 9,
            clue_top,
            rect.width - 18,
            max(1, rect.bottom - clue_top - clue_bottom_padding),
        )
        lines = wrap_lines(clue.text or clue.type, clue_rect.width, clue_size)
        line_height = clue_size + 3
        max_lines = max(1, clue_rect.height // line_height)
        for index, line in enumerate(lines[:max_lines]):
            draw_text(
                screen,
                line,
                (clue_rect.centerx, clue_rect.y + index * line_height),
                clue_size,
                TEXT,
                False,
                "midtop",
            )

        if status:
            status_color = CRIMINAL if status == Status.CRIMINAL else INNOCENT
            status_label = "CRIMINAL" if status == Status.CRIMINAL else "INNOCENT"
            draw_text(
                screen,
                status_label,
                (rect.centerx, rect.bottom - 12),
                10 if rect.height >= 160 else 9 if rect.height >= 120 else 8,
                status_color,
                True,
                "center",
            )

    def _draw_side_panel(self, screen):
        panel = pygame.Rect(765, 84, 485, 570)
        pygame.draw.rect(screen, PANEL, panel, border_radius=16)
        draw_text(screen, "PUBLIC KNOWLEDGE", (panel.x + 22, panel.y + 18), 18, ACCENT, True)
        clue = self.session.public.revealed_clues.get(self.selected_cell)
        if clue:
            draw_text(screen, clue.clue_id, (panel.x + 22, panel.y + 58), 21, TEXT, True)
            draw_text(screen, clue.type, (panel.right - 22, panel.y + 61), 15, ACCENT_2, True, "topright")
            draw_wrapped(screen, clue.text or str(clue.data), pygame.Rect(panel.x + 22, panel.y + 94, panel.width - 44, 82), 18, TEXT)
            refs = ", ".join(clue_cells(clue, self.session.public.size))
            draw_wrapped(screen, f"References: {refs}", pygame.Rect(panel.x + 22, panel.y + 182, panel.width - 44, 48), 15, MUTED)
        else:
            draw_wrapped(
                screen,
                "Select a revealed card to inspect its clue and highlight every referenced cell.",
                pygame.Rect(panel.x + 22, panel.y + 60, panel.width - 44, 90),
                18,
                MUTED,
            )
        analysis = self.session.analysis
        y = panel.y + 255
        draw_text(screen, "CNF / DPLL METRICS", (panel.x + 22, y), 17, ACCENT, True)
        rows = [
            ("Primary variables", analysis.primary_variables),
            ("Auxiliary variables", analysis.auxiliary_variables),
            ("Active clauses", analysis.clauses),
            ("SAT calls (analysis)", analysis.stats.sat_calls),
            ("Decisions", analysis.stats.decisions),
            ("Propagations", analysis.stats.propagations),
            ("Backtracks", analysis.stats.backtracks),
            ("Runtime", f"{analysis.stats.runtime_ms:.3f} ms"),
            ("Deduction steps", len(self.session.trace)),
        ]
        for index, (label, value) in enumerate(rows):
            row_y = y + 34 + index * 27
            draw_text(screen, label, (panel.x + 22, row_y), 15, MUTED)
            draw_text(screen, value, (panel.right - 22, row_y), 15, TEXT, True, "topright")
        unique = self.session.agent.uniqueness_check(self.session.public)
        draw_text(screen, "Current public KB", (panel.x + 22, panel.bottom - 38), 15, MUTED)
        draw_text(screen, unique, (panel.right - 22, panel.bottom - 38), 15, ACCENT if unique == "UNIQUE" else WARNING, True, "topright")

    def _draw_status_bar(self, screen):
        box = pygame.Rect(30, 682, 720, 48)
        pygame.draw.rect(screen, PANEL, box, border_radius=9)
        draw_wrapped(screen, self.message, pygame.Rect(box.x + 14, box.y + 8, box.width - 28, 35), 15, self.message_color, True, 2)
        enabled = self.selected_cell is not None and self.selected_cell not in self.session.public.proved_statuses
        for button in self.buttons[4:]:
            button.enabled = enabled and not self.session.engine.is_solved()
            button.draw(screen)
