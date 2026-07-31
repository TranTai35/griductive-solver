import pygame

from ui.theme import BG


class BaseScene:
    def __init__(self, app):
        self.app = app
        self.buttons = []

    def handle_event(self, event):
        for button in self.buttons:
            if button.handle_event(event):
                break

    def update(self, dt):
        pass

    def draw(self, screen):
        screen.fill(BG)

    @staticmethod
    def logical_surface(screen):
        return screen

