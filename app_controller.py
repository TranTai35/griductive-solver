import pygame

from scenes.game_scene import GameScene
from scenes.level_select_scene import LevelSelectScene
from scenes.menu_scene import MenuScene
from scenes.tutorial_scene import TutorialScene
from ui.theme import (
    BG,
    FPS,
    SCREEN_SIZE,
    TITLE,
)


class AppController:
    """
    Owns the Pygame loop and switches scenes.

    Các scene vẫn được thiết kế theo kích thước logic cố định
    1280 x 760.

    Khi cửa sổ được resize/maximize:
    - toàn bộ scene được scale
    - giữ đúng aspect ratio
    - đặt vào giữa cửa sổ
    - mouse position được chuyển ngược về logical coordinates
    """

    def __init__(self):
        pygame.init()

        pygame.display.set_caption(TITLE)

        # =====================================================
        # WINDOW
        # =====================================================

        self.screen = pygame.display.set_mode(
            SCREEN_SIZE,
            pygame.RESIZABLE,
        )

        # =====================================================
        # LOGICAL CANVAS
        # =====================================================

        self.logical_width = SCREEN_SIZE[0]
        self.logical_height = SCREEN_SIZE[1]

        self.logical_surface = pygame.Surface(
            (
                self.logical_width,
                self.logical_height,
            )
        )

        # Thông tin scaling hiện tại.
        self.scale = 1.0

        self.render_width = self.logical_width
        self.render_height = self.logical_height

        self.offset_x = 0
        self.offset_y = 0

        # =====================================================

        self.clock = pygame.time.Clock()

        self.running = True
        self.scene = None

        self.game_mode = None

        self.show_main_menu()

    # =========================================================
    # SCENE
    # =========================================================

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
    # QUIT
    # =========================================================

    def quit(self):
        self.running = False

    # =========================================================
    # SCALE
    # =========================================================

    def _calculate_render_area(self):
        """
        Tính scale sao cho canvas 1280x760 lớn nhất có thể
        nhưng vẫn nằm hoàn toàn trong cửa sổ.

        Canvas luôn được đặt chính giữa.
        """

        window_width, window_height = (
            self.screen.get_size()
        )

        # Scale theo chiều rộng và chiều cao.
        scale_x = (
            window_width
            / self.logical_width
        )

        scale_y = (
            window_height
            / self.logical_height
        )

        # Lấy scale nhỏ hơn để không bị crop.
        self.scale = min(
            scale_x,
            scale_y,
        )

        # Kích thước canvas sau khi scale.
        self.render_width = int(
            self.logical_width
            * self.scale
        )

        self.render_height = int(
            self.logical_height
            * self.scale
        )

        # Đặt vào giữa cửa sổ.
        self.offset_x = (
            window_width
            - self.render_width
        ) // 2

        self.offset_y = (
            window_height
            - self.render_height
        ) // 2

    # =========================================================
    # MOUSE COORDINATES
    # =========================================================

    def _screen_to_logical(self, position):
        """
        Chuyển mouse position từ cửa sổ thật
        sang tọa độ canvas 1280x760.
        """

        mouse_x, mouse_y = position

        if self.scale <= 0:
            return position

        logical_x = (
            mouse_x
            - self.offset_x
        ) / self.scale

        logical_y = (
            mouse_y
            - self.offset_y
        ) / self.scale

        return (
            int(logical_x),
            int(logical_y),
        )

    # =========================================================
    # EVENT CONVERSION
    # =========================================================

    def _convert_event(self, event):
        """
        Button và GameScene đang kiểm tra event.pos
        dựa trên canvas 1280x760.

        Vì vậy mouse position cần được convert trước
        khi truyền cho scene.
        """

        if event.type in (
            pygame.MOUSEMOTION,
            pygame.MOUSEBUTTONDOWN,
            pygame.MOUSEBUTTONUP,
        ):

            logical_pos = (
                self._screen_to_logical(
                    event.pos
                )
            )

            event_data = (
                event.dict.copy()
            )

            event_data["pos"] = (
                logical_pos
            )

            return pygame.event.Event(
                event.type,
                event_data,
            )

        return event

    # =========================================================
    # DRAW
    # =========================================================

    def _render_scene(self):
        # ---------------------------------------------
        # Scene luôn draw vào canvas 1280x760.
        # ---------------------------------------------

        self.logical_surface.fill(BG)

        self.scene.draw(
            self.logical_surface
        )

        # ---------------------------------------------
        # Tính scale mới dựa trên window hiện tại.
        # ---------------------------------------------

        self._calculate_render_area()

        # ---------------------------------------------
        # Scale canvas.
        # ---------------------------------------------

        scaled_surface = (
            pygame.transform.smoothscale(
                self.logical_surface,
                (
                    self.render_width,
                    self.render_height,
                ),
            )
        )

        # Background của phần thừa.
        self.screen.fill(BG)

        # Đặt canvas chính giữa.
        self.screen.blit(
            scaled_surface,
            (
                self.offset_x,
                self.offset_y,
            ),
        )

    # =========================================================
    # RUN
    # =========================================================

    def run(self):
        while self.running:

            dt = (
                self.clock.tick(FPS)
                / 1000.0
            )

            # Cần update scale trước khi xử lý mouse.
            self._calculate_render_area()

            # -------------------------------------------------
            # Events
            # -------------------------------------------------

            for event in pygame.event.get():

                if event.type == pygame.QUIT:

                    self.quit()

                else:

                    converted_event = (
                        self._convert_event(
                            event
                        )
                    )

                    self.scene.handle_event(
                        converted_event
                    )

            # -------------------------------------------------
            # Update
            # -------------------------------------------------

            self.scene.update(dt)

            # -------------------------------------------------
            # Draw
            # -------------------------------------------------

            self._render_scene()

            pygame.display.flip()

        pygame.quit()