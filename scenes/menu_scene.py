import pygame

from scenes.base_scene import BaseScene
from ui.button import Button
from ui.text import draw_text, draw_wrapped
from ui.theme import ACCENT, ACCENT_2, BG, MUTED, PANEL, SCREEN_SIZE, TEXT


class MenuScene(BaseScene):
    def __init__(self, app, on_play, on_tutorial, on_quit):
        super().__init__(app)
        self.buttons = [
            Button((105, 390, 260, 52), "PLAY / SOLVE", on_play, accent=True),
            Button((105, 456, 260, 52), "HOW TO PLAY", on_tutorial),
            Button((105, 522, 260, 52), "QUIT", on_quit),
        ]

    def draw(self, screen):
        screen.fill(BG)
        width, height = screen.get_size()
        pygame.draw.circle(screen, (24, 74, 81), (width - 100, -10), 390)
        pygame.draw.circle(screen, (39, 42, 90), (width - 180, height + 100), 330)
        pygame.draw.rect(screen, PANEL, (65, 68, 390, height - 136), border_radius=22)

        draw_text(screen, "GRIDUCTIVE", (104, 115), 48, ACCENT, True)
        draw_text(screen, "SOLVER", (105, 170), 48, TEXT, True)
        draw_wrapped(
            screen,
            "A no-guess deduction game powered by propositional logic, automatic CNF encoding, and a DPLL SAT solver.",
            pygame.Rect(106, 245, 300, 110),
            18,
            MUTED,
        )
        for button in self.buttons:
            button.draw(screen)
        draw_text(screen, "CSC14003 · INTRODUCTION TO AI", (105, height - 100), 15, MUTED, True)

        # Decorative logical grid
        origin_x, origin_y, cell = width - 615, 130, 120
        symbols = [("A1", "?"), ("B1", "C"), ("C1", "?"), ("A2", "I"),
                   ("B2", "?"), ("C2", "C"), ("A3", "?"), ("B3", "?"), ("C3", "I")]
        for index, (coord, symbol) in enumerate(symbols):
            row, col = divmod(index, 3)
            rect = pygame.Rect(origin_x + col * (cell + 12), origin_y + row * (cell + 12), cell, cell)
            pygame.draw.rect(screen, (29, 39, 59), rect, border_radius=14)
            pygame.draw.rect(screen, ACCENT_2 if symbol == "?" else ACCENT, rect, 2, border_radius=14)
            draw_text(screen, coord, (rect.x + 12, rect.y + 10), 14, MUTED, True)
            draw_text(screen, symbol, rect.center, 43, TEXT, True, "center")

