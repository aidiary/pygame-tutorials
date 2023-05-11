import sys

import pygame
from menu import Menu
from pygame.math import Vector2 as vector
from pygame.mouse import get_pos as mouse_pos
from pygame.mouse import get_pressed as mouse_buttons
from settings import EDITOR_DATA, LINE_COLOR, TILE_SIZE, WINDOW_HEIGHT, WINDOW_WIDTH


class Editor:
    def __init__(self):
        # main setup
        # Main.__init__()で作成済みのDisplay Surfaceを取得
        self.display_surface = pygame.display.get_surface()
        self.canvas_data = {}

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

        # selection
        self.selection_index = 2
        self.last_selected_cell = None

        # menu
        self.menu = Menu()

    # support
    def get_current_cell(self):
        distance_to_origin = vector(mouse_pos()) - self.origin

        if distance_to_origin.x > 0:
            col = int(distance_to_origin.x / TILE_SIZE)
        else:
            col = int(distance_to_origin.x / TILE_SIZE) - 1

        if distance_to_origin.y > 0:
            row = int(distance_to_origin.y / TILE_SIZE)
        else:
            row = int(distance_to_origin.y / TILE_SIZE) - 1

        return col, row

    # input
    def event_loop(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            # マウスによる原点の移動
            self.pan_input(event)

            # ホットキーによるアイテムの選択切り替え
            self.selection_hotkeys(event)

            # メニューがクリックされたか
            self.menu_click(event)

            # キャンバスがクリックされたか
            self.canvas_add()

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

    def selection_hotkeys(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RIGHT:
                self.selection_index += 1
            if event.key == pygame.K_LEFT:
                self.selection_index -= 1
        # 2-18の間に制限する
        self.selection_index = max(2, min(self.selection_index, 18))

    def menu_click(self, event):
        # まずはメニューエリアがクリックされたか調べる
        if event.type == pygame.MOUSEBUTTONDOWN and self.menu.rect.collidepoint(
            mouse_pos()
        ):
            self.selection_index = self.menu.click(mouse_pos(), mouse_buttons())

    def canvas_add(self):
        # 左クリックでメニュー以外の部分をクリックしたとき
        if mouse_buttons()[0] and not self.menu.rect.collidepoint(mouse_pos()):
            current_cell = self.get_current_cell()

            if current_cell != self.last_selected_cell:
                if current_cell in self.canvas_data:
                    # すでに何かあったらIDを追加する
                    self.canvas_data[current_cell].add_id(self.selection_index)
                else:
                    # 何もないセルだったら新しくCanvasTileを作る
                    self.canvas_data[current_cell] = CanvasTile(self.selection_index)
                self.last_selected_cell = current_cell

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

    def draw_level(self):
        for cell_pos, tile in self.canvas_data.items():
            pos = self.origin + vector(cell_pos) * TILE_SIZE

            # water
            if tile.has_water:
                test_surf = pygame.Surface((TILE_SIZE, TILE_SIZE))
                test_surf.fill("blue")
                self.display_surface.blit(test_surf, pos)

            # terrain
            if tile.has_terrain:
                test_surf = pygame.Surface((TILE_SIZE, TILE_SIZE))
                test_surf.fill("brown")
                self.display_surface.blit(test_surf, pos)

            # coins
            if tile.coin:
                test_surf = pygame.Surface((TILE_SIZE, TILE_SIZE))
                test_surf.fill("yellow")
                self.display_surface.blit(test_surf, pos)

            # enemies
            if tile.enemy:
                test_surf = pygame.Surface((TILE_SIZE, TILE_SIZE))
                test_surf.fill("red")
                self.display_surface.blit(test_surf, pos)

    def run(self, dt):
        self.event_loop()

        self.display_surface.fill("gray")
        self.draw_tile_lines()
        self.draw_level()
        pygame.draw.circle(
            self.display_surface, color="red", center=self.origin, radius=10
        )
        self.menu.display(self.selection_index)


class CanvasTile:
    def __init__(self, tile_id):
        # terrain
        self.has_terrain = False
        # 隣にタイルがあったら丸まった地形に表示するため
        self.terrain_neighbors = []

        # water
        self.has_water = False
        # 一番トップにある水は波打ったアニメーションにするため
        self.water_on_top = False

        # coin
        self.coin = None

        # enemy
        self.enemy = None

        # objects
        self.objects = []

        self.add_id(tile_id)

    def add_id(self, tile_id):
        options = {key: value["style"] for key, value in EDITOR_DATA.items()}
        match options[tile_id]:
            case "terrain":
                self.has_terrain = True
            case "water":
                self.has_water = True
            case "coin":
                self.coin = tile_id
            case "enemy":
                self.enemy = tile_id
