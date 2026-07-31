from pathlib import Path

import pygame

from core.puzzle_loader import load_puzzle
from scenes.base_scene import BaseScene
from ui.button import Button
from ui.text import draw_text, draw_wrapped
from ui.theme import ACCENT, BG, BORDER, MUTED, PANEL, TEXT


class LevelSelectScene(BaseScene):
    def __init__(self, app, on_level_selected, on_back):
        super().__init__(app)
        self.on_level_selected = on_level_selected
        self.puzzle_paths = sorted(Path(__file__).parents[1].joinpath("puzzles").glob("*.json"))
        self.cards = []
        for index, path in enumerate(self.puzzle_paths):
            x = 70 + (index % 3) * 390
            y = 180 + (index // 3) * 230
            self.cards.append((pygame.Rect(x, y, 350, 190), path, load_puzzle(path)))
        self.buttons = [Button((70, 80, 110, 44), "BACK", on_back)]

    def handle_event(self, event):
        super().handle_event(event)
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.buttons[0].callback()
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for rect, path, _ in self.cards:
                if rect.collidepoint(event.pos):
                    self.on_level_selected(path)

    def draw(self, screen):
        screen.fill(BG)
        draw_text(screen, "SELECT A CASE", (70, 28), 38, TEXT, True)
        draw_text(screen, "Every case is solved through public clues only.", (70, 132), 18, MUTED)
        for button in self.buttons:
            button.draw(screen)
        mouse = pygame.mouse.get_pos()
        for index, (rect, _, puzzle) in enumerate(self.cards, start=1):
            color = (37, 50, 71) if rect.collidepoint(mouse) else PANEL
            pygame.draw.rect(screen, color, rect, border_radius=16)
            pygame.draw.rect(screen, ACCENT if rect.collidepoint(mouse) else BORDER, rect, 2, border_radius=16)
            draw_text(screen, f"CASE {index:02}", (rect.x + 22, rect.y + 18), 15, ACCENT, True)
            draw_text(screen, puzzle.title, (rect.x + 22, rect.y + 48), 25, TEXT, True)
            draw_wrapped(screen, puzzle.description, pygame.Rect(rect.x + 22, rect.y + 86, rect.width - 44, 55), 16, MUTED)
            draw_text(
                screen,
                f"{puzzle.size} × {puzzle.size}  ·  {len(puzzle.initially_revealed)} public clues",
                (rect.x + 22, rect.bottom - 28),
                15,
                MUTED,
            )

