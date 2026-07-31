import pygame

from scenes.base_scene import BaseScene
from ui.button import Button
from ui.text import draw_text, draw_wrapped
from ui.theme import (
    ACCENT,
    ACCENT_2,
    BG,
    MUTED,
    PANEL,
    TEXT,
)


class MenuScene(BaseScene):
    def __init__(
        self,
        app,
        on_play,
        on_solve,
        on_tutorial,
        on_quit,
    ):
        super().__init__(app)

        self.buttons = [
            Button(
                (105, 365, 260, 52),
                "PLAY",
                on_play,
                accent=True,
            ),

            Button(
                (105, 431, 260, 52),
                "SOLVE",
                on_solve,
            ),

            Button(
                (105, 497, 260, 52),
                "HOW TO PLAY",
                on_tutorial,
            ),

            Button(
                (105, 563, 260, 52),
                "QUIT",
                on_quit,
            ),
        ]

    def draw(self, screen):
        screen.fill(BG)

        width, height = screen.get_size()

        # Decorative background
        pygame.draw.circle(
            screen,
            (24, 74, 81),
            (width - 100, -10),
            390,
        )

        pygame.draw.circle(
            screen,
            (39, 42, 90),
            (width - 180, height + 100),
            330,
        )

        # Left panel
        pygame.draw.rect(
            screen,
            PANEL,
            (65, 68, 390, height - 136),
            border_radius=22,
        )

        # Title
        draw_text(
            screen,
            "GRIDUCTIVE",
            (104, 115),
            48,
            ACCENT,
            True,
        )

        draw_text(
            screen,
            "SOLVER",
            (105, 170),
            48,
            TEXT,
            True,
        )

        # Description
        draw_wrapped(
            screen,
            (
                "A no-guess deduction game powered by "
                "propositional logic, automatic CNF encoding, "
                "and a DPLL SAT solver."
            ),
            pygame.Rect(
                106,
                245,
                300,
                100,
            ),
            18,
            MUTED,
        )

        # Buttons
        for button in self.buttons:
            button.draw(screen)

        # Footer
        draw_text(
            screen,
            "CSC14003 · INTRODUCTION TO AI",
            (105, height - 75),
            15,
            MUTED,
            True,
        )

        # =====================================================
        # Decorative logical grid
        # =====================================================

        origin_x = width - 615
        origin_y = 130
        cell = 120

        symbols = [
            ("A1", "?"),
            ("B1", "C"),
            ("C1", "?"),

            ("A2", "I"),
            ("B2", "?"),
            ("C2", "C"),

            ("A3", "?"),
            ("B3", "?"),
            ("C3", "I"),
        ]

        for index, (coord, symbol) in enumerate(symbols):
            row, col = divmod(index, 3)

            rect = pygame.Rect(
                origin_x + col * (cell + 12),
                origin_y + row * (cell + 12),
                cell,
                cell,
            )

            pygame.draw.rect(
                screen,
                (29, 39, 59),
                rect,
                border_radius=14,
            )

            pygame.draw.rect(
                screen,
                ACCENT_2 if symbol == "?" else ACCENT,
                rect,
                2,
                border_radius=14,
            )

            draw_text(
                screen,
                coord,
                (rect.x + 12, rect.y + 10),
                14,
                MUTED,
                True,
            )

            draw_text(
                screen,
                symbol,
                rect.center,
                43,
                TEXT,
                True,
                "center",
            )