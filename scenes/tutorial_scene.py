import pygame

from scenes.base_scene import BaseScene
from ui.button import Button
from ui.text import draw_text, draw_wrapped
from ui.theme import ACCENT, BG, MUTED, PANEL, TEXT


class TutorialScene(BaseScene):
    def __init__(self, app, on_back):
        super().__init__(app)
        self.on_back = on_back
        self.buttons = [Button((65, 42, 110, 44), "BACK", on_back)]

    def handle_event(self, event):
        super().handle_event(event)
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.on_back()

    def draw(self, screen):
        screen.fill(BG)
        for button in self.buttons:
            button.draw(screen)
        draw_text(screen, "HOW TO PLAY", (65, 112), 40, TEXT, True)
        sections = [
            ("1. READ PUBLIC CLUES", "Face-up cards show true statements. Names and professions have no logical meaning."),
            ("2. SELECT A CARD", "Click an unresolved character, then choose CRIMINAL or INNOCENT."),
            ("3. NEVER GUESS", "A verdict is accepted only if it follows in every model of the current knowledge base."),
            ("4. REVEAL MORE", "A proved verdict flips that card and exposes a new true clue. Continue until all cards are proved."),
            ("5. ASK THE AGENT", "Hint finds one forced next move. Auto Solve performs the same no-guess deduction loop."),
            ("RESULT MESSAGES", "NOT_PROVABLE means both statuses remain possible. CONTRADICTED means the opposite status is forced."),
        ]
        for index, (title, body) in enumerate(sections):
            col, row = index % 2, index // 2
            rect = pygame.Rect(65 + col * 600, 190 + row * 165, 550, 130)
            pygame.draw.rect(screen, PANEL, rect, border_radius=14)
            draw_text(screen, title, (rect.x + 22, rect.y + 18), 19, ACCENT, True)
            draw_wrapped(screen, body, pygame.Rect(rect.x + 22, rect.y + 52, rect.width - 44, 60), 17, MUTED)

