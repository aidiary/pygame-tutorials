import sys

import pygame
from menu import Menu
from pygame.image import load
from pygame.math import Vector2 as vector
from pygame.mouse import get_pos as mouse_pos
from pygame.mouse import get_pressed as mouse_buttons
from settings import (
    ANIMATION_SPEED,
    EDITOR_DATA,
    LINE_COLOR,
    NEIGHBOR_DIRECTIONS,
    TILE_SIZE,
    WINDOW_HEIGHT,
    WINDOW_WIDTH,
)
from support import import_folder


class Editor:
    def __init__(self, land_tiles):
        # main setup
        # Main.__init__()で作成済みのDisplay Surfaceを取得
        self.display_surface = pygame.display.get_surface()
        self.canvas_data = {}

        # imports
        self.land_tiles = land_tiles
        self.imports()

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

    def check_neighbors(self, cell_pos):
        # create a local cluster
        # 自分を中心として周囲3x3のマスを調べる
        cluster_size = 3
        # 周囲3x3のマスの実座標を得る
        local_cluster = [
            (
                cell_pos[0] + col - int(cluster_size / 2),
                cell_pos[1] + row - int(cluster_size / 2),
            )
            for col in range(cluster_size)
            for row in range(cluster_size)
        ]

        # check neighbors
        # 周囲のマスすべてが影響を受けるので隣のセルをチェック
        for cell in local_cluster:
            if cell in self.canvas_data:
                # 隣のタイルに対する設定をリセット
                self.canvas_data[cell].terrain_neighbors = []
                self.canvas_data[cell].water_on_top = False

                # NEIGHBOR_DIRECTIONSには周囲8マスの相対位置が入っている
                # forループで全方位を調べる
                for name, side in NEIGHBOR_DIRECTIONS.items():
                    neighbor_cell = (cell[0] + side[0], cell[1] + side[1])

                    if neighbor_cell in self.canvas_data:
                        # water top neighbor
                        # 中心がwaterタイルで上のもwaterタイルがあった場合
                        if (
                            self.canvas_data[neighbor_cell].has_water
                            and self.canvas_data[cell].has_water
                            and name == "A"
                        ):
                            self.canvas_data[cell].water_on_top = True

                        # terrain neighbors
                        # 隣のセルにterrainがあるか？あったら方向のアルファベットを追加
                        if self.canvas_data[neighbor_cell].has_terrain:
                            self.canvas_data[cell].terrain_neighbors.append(name)

    def imports(self):
        self.water_bottom = load("./graphics/terrain/water/water_bottom.png")

        # animations
        self.animations = {}
        for key, value in EDITOR_DATA.items():
            # graphics属性があるデータはアニメーションするのですべてロード
            # アニメーション管理用の辞書も作成
            if value["graphics"]:
                graphics = import_folder(value["graphics"])
                self.animations[key] = {
                    "frame_index": 0,
                    "frames": graphics,
                    "length": len(graphics),
                }

    def animation_update(self, dt):
        for value in self.animations.values():
            value["frame_index"] += ANIMATION_SPEED * dt
            if value["frame_index"] >= value["length"]:
                value["frame_index"] = 0

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

                # 周囲のマスを調べて繋がりがあるか調べる
                self.check_neighbors(current_cell)
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
                if tile.water_on_top:
                    self.display_surface.blit(self.water_bottom, pos)
                else:
                    # 水のアニメーション
                    # Spriteは大量にあると遅くなるので作らない
                    # 描画時に画像の切り替えをすることでアニメーション化
                    frames = self.animations[3]["frames"]
                    index = int(self.animations[3]["frame_index"])
                    surf = frames[index]
                    self.display_surface.blit(surf, pos)

            # terrain
            if tile.has_terrain:
                # 周囲にTerrainがあって接続したら画像を変える処理
                terrain_string = "".join(tile.terrain_neighbors)
                terrain_style = (
                    terrain_string if terrain_string in self.land_tiles else "X"
                )
                self.display_surface.blit(self.land_tiles[terrain_style], pos)

            # coins
            if tile.coin:
                # コインのアニメーション
                frames = self.animations[tile.coin]["frames"]
                index = int(self.animations[tile.coin]["frame_index"])
                surf = frames[index]
                # コインをタイルの中央に配置するために少しずらす
                rect = surf.get_rect(
                    center=(pos[0] + TILE_SIZE // 2, pos[1] + TILE_SIZE // 2)
                )
                self.display_surface.blit(surf, rect)

            # enemies
            if tile.enemy:
                # 敵のアニメーション
                frames = self.animations[tile.enemy]["frames"]
                index = int(self.animations[tile.enemy]["frame_index"])
                surf = frames[index]
                # 敵が地面に立つように下側に合わせる
                rect = surf.get_rect(
                    midbottom=(pos[0] + TILE_SIZE // 2, pos[1] + TILE_SIZE)
                )
                self.display_surface.blit(surf, rect)

    def run(self, dt):
        self.event_loop()

        # updating
        self.animation_update(dt)

        # drawing
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
