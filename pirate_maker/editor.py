import sys

import pygame
from pygame.math import Vector2 as vector
from pygame.mouse import get_pos as mouse_pos
from pygame.mouse import get_pressed as mouse_buttons
from settings import LINE_COLOR, TILE_SIZE, WINDOW_HEIGHT, WINDOW_WIDTH


class Editor:
    def __init__(self):
        # main setup
        # Main.__init__()で作成済みのDisplay Surfaceを取得
        self.display_surface = pygame.display.get_surface()

        # navigation
        self.origin = vector()
        self.pan_active = False
        self.pan_offset = vector()

        # support lines
        # マス目を描くSurfaceを別に作る
        # alphaで透明色を制御するため
        self.support_line_surf = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.support_line_surf.set_colorkey("green")
        self.support_line_surf.set_alpha(30)

    # input
    def event_loop(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            self.pan_input(event)

    def pan_input(self, event):
        # middle mouse button pressed / released
        if event.type == pygame.MOUSEBUTTONDOWN and mouse_buttons()[1]:
            self.pan_active = True
            self.pan_offset = vector(mouse_pos()) - self.origin

        if not mouse_buttons()[1]:
            self.pan_active = False

        # mouse wheel
        if event.type == pygame.MOUSEWHEEL:
            # マウスによって+1/-1以外の大きな値を取る場合があるので+1/-1のみ使う
            event.y = 1 if event.y > 0 else -1
            # CTRLを押しながらホイールを動かすとoriginが縦に動く
            # 押さなかったらoriginが横に動く
            if pygame.key.get_pressed()[pygame.K_LCTRL]:
                self.origin.y -= event.y * 50
            else:
                self.origin.x -= event.y * 50

        # panning update
        if self.pan_active:
            self.origin = vector(mouse_pos()) - self.pan_offset

    def draw_tile_lines(self):
        cols = WINDOW_WIDTH // TILE_SIZE
        rows = WINDOW_HEIGHT // TILE_SIZE

        # originを移動したときに左側と右側にも描画されるように調整
        origin_offset = vector(
            x=self.origin.x - int(self.origin.x / TILE_SIZE) * TILE_SIZE,
            y=self.origin.y - int(self.origin.y / TILE_SIZE) * TILE_SIZE,
        )

        self.support_line_surf.fill("green")

        # +1はoriginを動かしたときに最右側でも表示されるように
        for col in range(cols + 1):
            x = origin_offset.x + col * TILE_SIZE
            pygame.draw.line(
                self.support_line_surf,
                color=LINE_COLOR,
                start_pos=(x, 0),
                end_pos=(x, WINDOW_HEIGHT),
            )

        for row in range(rows + 1):
            y = origin_offset.y + row * TILE_SIZE
            pygame.draw.line(
                self.support_line_surf,
                color=LINE_COLOR,
                start_pos=(0, y),
                end_pos=(WINDOW_WIDTH, y),
            )

        self.display_surface.blit(self.support_line_surf, (0, 0))

    def run(self, dt):
        self.event_loop()

        self.display_surface.fill("white")
        self.draw_tile_lines()
        pygame.draw.circle(
            self.display_surface, color="red", center=self.origin, radius=10
        )
