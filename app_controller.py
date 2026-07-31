import pygame

from scenes.game_scene import GameScene
from scenes.level_select_scene import LevelSelectScene
from scenes.menu_scene import MenuScene
from scenes.tutorial_scene import TutorialScene
from ui.theme import FPS, SCREEN_SIZE, TITLE


class AppController:
    """Owns the Pygame loop and switches screens without restarting Pygame."""

    def __init__(self):
        pygame.init()
        pygame.display.set_caption(TITLE)

        self.screen = pygame.display.set_mode(
            SCREEN_SIZE,
            pygame.RESIZABLE,
        )

        self.clock = pygame.time.Clock()
        self.running = True
        self.scene = None

        # Mode hiện tại:
        # None
        # "play"
        # "solve"
        self.game_mode = None

        self.show_main_menu()

    def change_scene(self, scene):
        self.scene = scene

    # =========================================================
    # MAIN MENU
    # =========================================================

    def show_main_menu(self):
        self.game_mode = None

        self.change_scene(
            MenuScene(
                self,
                on_play=self.show_play_levels,
                on_solve=self.show_solve_levels,
                on_tutorial=self.show_tutorial,
                on_quit=self.quit,
            )
        )

    # =========================================================
    # PLAY
    # =========================================================

    def show_play_levels(self):
        self.game_mode = "play"
        self.show_level_select()

    # =========================================================
    # SOLVE
    # =========================================================

    def show_solve_levels(self):
        self.game_mode = "solve"
        self.show_level_select()

    # =========================================================
    # LEVEL SELECT
    # =========================================================

    def show_level_select(self):
        self.change_scene(
            LevelSelectScene(
                self,
                mode=self.game_mode,
                on_level_selected=self.start_game,
                on_back=self.show_main_menu,
            )
        )

    # =========================================================
    # TUTORIAL
    # =========================================================

    def show_tutorial(self):
        self.change_scene(
            TutorialScene(
                self,
                on_back=self.show_main_menu,
            )
        )

    # =========================================================
    # GAME
    # =========================================================

    def start_game(self, puzzle_path):
        self.change_scene(
            GameScene(
                self,
                puzzle_path=puzzle_path,
                mode=self.game_mode,
                on_back=self.show_level_select,
            )
        )

    # =========================================================
    # APP
    # =========================================================

    def quit(self):
        self.running = False

    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.quit()
                else:
                    self.scene.handle_event(event)

            self.scene.update(dt)
            self.scene.draw(self.screen)

            pygame.display.flip()

        pygame.quit()