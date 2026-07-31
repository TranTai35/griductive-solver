import pygame

from ui.theme import ACCENT, BORDER, PANEL_2, TEXT, font


class Button:
    def __init__(self, rect, text, callback, accent=False, enabled=True):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.callback = callback
        self.accent = accent
        self.enabled = enabled
        self.hovered = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        elif (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and self.enabled
            and self.rect.collidepoint(event.pos)
        ):
            self.callback()
            return True
        return False

    def draw(self, surface):
        if not self.enabled:
            color = (45, 52, 67)
            text_color = (102, 112, 132)
        elif self.accent:
            color = (54, 188, 163) if self.hovered else ACCENT
            text_color = (10, 30, 35)
        else:
            color = (54, 68, 94) if self.hovered else PANEL_2
            text_color = TEXT
        pygame.draw.rect(surface, color, self.rect, border_radius=8)
        pygame.draw.rect(surface, BORDER, self.rect, width=1, border_radius=8)
        label = font(17, True).render(self.text, True, text_color)
        surface.blit(label, label.get_rect(center=self.rect.center))

