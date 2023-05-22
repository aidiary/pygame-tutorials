import sys
from random import choice, randint

import pygame
from menu import Menu
from mytimer import Timer
from pygame.image import load
from pygame.math import Vector2 as vector
from pygame.mouse import get_pos as mouse_pos
from pygame.mouse import get_pressed as mouse_buttons
from settings import (
    ANIMATION_SPEED,
    EDITOR_DATA,
    HORIZON_COLOR,
    HORIZON_TOP_COLOR,
    LINE_COLOR,
    NEIGHBOR_DIRECTIONS,
    SEA_COLOR,
    SKY_COLOR,
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

        # clouds
        self.current_clouds = []
        self.cloud_surf = import_folder("./graphics/clouds")
        self.cloud_timer = pygame.USEREVENT + 1
        pygame.time.set_timer(self.cloud_timer, 2000)
        self.startup_clouds()

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

        # objects
        # タイルに制限されないオブジェクト
        self.canvas_objects = pygame.sprite.Group()
        self.foreground = pygame.sprite.Group()
        self.background = pygame.sprite.Group()

        # オブジェクトのドラッグ中か？
        self.object_drag_active = False

        self.object_timer = Timer(400)

        # player
        CanvasObject(
            pos=(200, WINDOW_HEIGHT / 2),
            frames=self.animations[0]["frames"],
            tile_id=0,
            origin=self.origin,
            group=[self.canvas_objects, self.foreground],
        )

        # sky
        self.sky_handle = CanvasObject(
            pos=(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2),
            frames=[self.sky_handle_surf],
            tile_id=1,
            origin=self.origin,
            group=[self.canvas_objects, self.background],
        )

    # support
    def get_current_cell(self, obj=None):
        """マウスまたはオブジェクトがある位置のセル（row, col）を取得する"""
        if not obj:
            distance_to_origin = vector(mouse_pos()) - self.origin
        else:
            distance_to_origin = vector(obj.distance_to_origin) - self.origin

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
        self.water_bottom = load(
            "./graphics/terrain/water/water_bottom.png"
        ).convert_alpha()
        self.sky_handle_surf = load("./graphics/cursors/handle.png").convert_alpha()

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

        # preview
        self.preview_surfs = {
            key: load(value["preview"])
            for key, value in EDITOR_DATA.items()
            if value["preview"]
        }

    def animation_update(self, dt):
        for value in self.animations.values():
            value["frame_index"] += ANIMATION_SPEED * dt
            if value["frame_index"] >= value["length"]:
                value["frame_index"] = 0

    def mouse_on_object(self):
        """マウスの位置にあるオブジェクトを返す"""
        for sprite in self.canvas_objects:
            if sprite.rect.collidepoint(mouse_pos()):
                return sprite

    def create_grid(self):
        # add objects to the tiles

        for tile in self.canvas_data.values():
            tile.objects = []

        for obj in self.canvas_objects:
            current_cell = self.get_current_cell(obj)
            # オブジェクトがあるセルの座標からオブジェクトの座標へのベクトル
            offset = vector(obj.distance_to_origin) - (vector(current_cell) * TILE_SIZE)

            # CanvasTileとしてオブジェクトを追加
            if current_cell in self.canvas_data:
                # タイルがすでにある場合
                self.canvas_data[current_cell].add_id(obj.tile_id, offset)
            else:
                self.canvas_data[current_cell] = CanvasTile(obj.tile_id, offset)

        # create an empty grid
        layers = {
            "water": {},
            "bg palms": {},
            "terrain": {},
            "enemies": {},
            "coins": {},
            "fg objects": {},
        }

        # grid offset
        # 一番左にあるタイルやオブジェクトのx座標を取得
        left = sorted(self.canvas_data.keys(), key=lambda tile: tile[0])[0][0]
        # 一番上にあるタイルやオブジェクトのy座標を取得
        top = sorted(self.canvas_data.keys(), key=lambda tile: tile[1])[0][1]

        # fill the grid
        for tile_pos, tile in self.canvas_data.items():
            # 一番左上にあるタイルを (0, 0) になるように調整する
            row_adjusted = tile_pos[1] - top
            col_adjusted = tile_pos[0] - left
            x = col_adjusted * TILE_SIZE
            y = row_adjusted * TILE_SIZE

            if tile.has_water:
                layers["water"][(x, y)] = tile.get_water()

            if tile.has_terrain:
                layers["terrain"][(x, y)] = (
                    tile.get_terrain() if tile.get_terrain() in self.land_tiles else "X"
                )

            if tile.coin:
                layers["coins"][(x + TILE_SIZE // 2, y + TILE_SIZE // 2)] = tile.coin

            if tile.enemy:
                layers["enemies"][(x, y)] = tile.enemy

            if tile.objects:
                for obj, offset in tile.objects:
                    if obj in [
                        key
                        for key, value in EDITOR_DATA.items()
                        if value["style"] == "palm_bg"
                    ]:
                        layers["bg palms"][(int(x + offset.x), int(y + offset.y))] = obj
                    else:
                        layers["fg objects"][
                            (int(x + offset.x), int(y + offset.y))
                        ] = obj

        return layers

    # input
    def event_loop(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                print(self.create_grid())

            # マウスによる原点の移動
            self.pan_input(event)

            # ホットキーによるアイテムの選択切り替え
            self.selection_hotkeys(event)

            # メニューがクリックされたか
            self.menu_click(event)

            # オブジェクトがドラッグして移動されたか
            self.object_drag(event)

            # キャンバスが左クリックされてオブジェクトが追加されたか
            self.canvas_add()

            # キャンバスが右クリックされてオブジェクトが削除されたか
            self.canvas_remove()

            # 雲を作る
            self.create_clouds(event)

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

            # オブジェクトもoriginに合わせて移動させる
            for sprite in self.canvas_objects:
                sprite.pan_pos(self.origin)

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
        # ドラッグ中は追加しない
        if (
            mouse_buttons()[0]
            and not self.menu.rect.collidepoint(mouse_pos())
            and not self.object_drag_active
        ):
            current_cell = self.get_current_cell()

            if EDITOR_DATA[self.selection_index]["type"] == "tile":
                if current_cell != self.last_selected_cell:
                    if current_cell in self.canvas_data:
                        # すでに何かあったらIDを追加する
                        self.canvas_data[current_cell].add_id(self.selection_index)
                    else:
                        # 何もないセルだったら新しくCanvasTileを作る
                        self.canvas_data[current_cell] = CanvasTile(
                            self.selection_index
                        )

                    # 周囲のマスを調べて繋がりがあるか調べる
                    self.check_neighbors(current_cell)
                    self.last_selected_cell = current_cell
            else:  # object
                # タイマーがアクティブでなかったら新しいオブジェクトを追加する
                # 連続してオブジェクトが配置されないための工夫
                # 次に配置されるのはタイマーが終了してから
                if not self.object_timer.active:
                    groups = (
                        [self.canvas_objects, self.background]
                        if EDITOR_DATA[self.selection_index]["style"] == "palm_bg"
                        else [self.canvas_objects, self.foreground]
                    )

                    CanvasObject(
                        pos=mouse_pos(),
                        frames=self.animations[self.selection_index]["frames"],
                        tile_id=self.selection_index,
                        origin=self.origin,
                        group=groups,
                    )
                    self.object_timer.activate()

    def canvas_remove(self):
        # 右クリックでメニュー以外の部分をクリックしたときに
        if mouse_buttons()[2] and not self.menu.rect.collidepoint(mouse_pos()):
            # オブジェクトを削除する
            selected_object = self.mouse_on_object()
            if selected_object:
                # 削除できるのはplayerとsky以外にする
                if EDITOR_DATA[selected_object.tile_id]["style"] not in (
                    "player",
                    "sky",
                ):
                    selected_object.kill()

            # タイルを削除する
            if self.canvas_data:
                current_cell = self.get_current_cell()
                if current_cell in self.canvas_data:
                    # ターゲットのオブジェクトを削除
                    self.canvas_data[current_cell].remove_id(self.selection_index)

                    # もしすべてのオブジェクトがなかったらエントリ自体を削除
                    if self.canvas_data[current_cell].is_empty:
                        del self.canvas_data[current_cell]

                    # オブジェクトを削除すると画像が変わるケースがあるので更新
                    self.check_neighbors(current_cell)

    def object_drag(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and mouse_buttons()[0]:
            for sprite in self.canvas_objects:
                if sprite.rect.collidepoint(mouse_pos()):
                    sprite.start_drag()
                    self.object_drag_active = True

        if event.type == pygame.MOUSEBUTTONUP and self.object_drag_active:
            for sprite in self.canvas_objects:
                if sprite.selected:
                    sprite.drag_end(self.origin)
                    self.object_drag_active = False

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
        self.background.draw(self.display_surface)

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

        self.foreground.draw(self.display_surface)

    def preview(self):
        """オブジェクトやタイルのプレビューを表示する"""
        selected_object = self.mouse_on_object()
        if not self.menu.rect.collidepoint(mouse_pos()):
            # 選択しているオブジェクトはSpriteより少し広めの範囲をカッコで囲む
            if selected_object:
                rect = selected_object.rect.inflate(10, 10)
                color = "black"
                width = 3
                size = 15

                # 左上のカッコ
                pygame.draw.lines(
                    self.display_surface,
                    color,
                    False,
                    (
                        (rect.left, rect.top + size),
                        rect.topleft,
                        (rect.left + size, rect.top),
                    ),
                    width,
                )

                # 右上のカッコ
                pygame.draw.lines(
                    self.display_surface,
                    color,
                    False,
                    (
                        (rect.right - size, rect.top),
                        rect.topright,
                        (rect.right, rect.top + size),
                    ),
                    width,
                )

                # 右下のカッコ
                pygame.draw.lines(
                    self.display_surface,
                    color,
                    False,
                    (
                        (rect.right - size, rect.bottom),
                        rect.bottomright,
                        (rect.right, rect.bottom - size),
                    ),
                    width,
                )

                # 左下のカッコ
                pygame.draw.lines(
                    self.display_surface,
                    color,
                    False,
                    (
                        (rect.left, rect.bottom - size),
                        rect.bottomleft,
                        (rect.left + size, rect.bottom),
                    ),
                    width,
                )
            else:
                # オブジェクト以外はプレビュー（すこし薄め）のオブジェクトやタイルを描画する
                type_dict = {key: value["type"] for key, value in EDITOR_DATA.items()}
                surf = self.preview_surfs[self.selection_index].copy()
                surf.set_alpha(200)

                # tile
                if type_dict[self.selection_index] == "tile":
                    current_cell = self.get_current_cell()
                    rect = surf.get_rect(
                        topleft=self.origin + vector(current_cell) * TILE_SIZE
                    )
                # object
                else:
                    rect = surf.get_rect(center=mouse_pos())

                self.display_surface.blit(surf, rect)

    def display_sky(self, dt):
        self.display_surface.fill(SKY_COLOR)
        y = self.sky_handle.rect.centery

        if y > 0:
            # 地平線
            horizon_rect1 = pygame.Rect(0, y - 10, WINDOW_WIDTH, 10)
            horizon_rect2 = pygame.Rect(0, y - 16, WINDOW_WIDTH, 4)
            horizon_rect3 = pygame.Rect(0, y - 20, WINDOW_WIDTH, 2)
            pygame.draw.rect(self.display_surface, HORIZON_TOP_COLOR, horizon_rect1)
            pygame.draw.rect(self.display_surface, HORIZON_TOP_COLOR, horizon_rect2)
            pygame.draw.rect(self.display_surface, HORIZON_TOP_COLOR, horizon_rect3)

            # 雲
            self.display_clouds(dt, y)

        # 海
        if 0 < y < WINDOW_HEIGHT:
            sea_rect = pygame.Rect(0, y, WINDOW_WIDTH, WINDOW_HEIGHT)
            pygame.draw.rect(self.display_surface, SEA_COLOR, sea_rect)
            # 地平線
            pygame.draw.line(
                self.display_surface, HORIZON_COLOR, (0, y), (WINDOW_WIDTH, y), 3
            )

        # 地平線が画面の上にはみ出したら下はすべて海扱いにする
        if y < 0:
            self.display_surface.fill(SEA_COLOR)

    def display_clouds(self, dt, horizon_y):
        for cloud in self.current_clouds:  # [{surf, pos, speed}]
            cloud["pos"][0] -= cloud["speed"] * dt
            x = cloud["pos"][0]
            y = horizon_y - cloud["pos"][1]
            self.display_surface.blit(cloud["surf"], (x, y))

    def create_clouds(self, event):
        if event.type == self.cloud_timer:
            surf = choice(self.cloud_surf)
            # 50%の確率で雲サイズを2倍する
            surf = pygame.transform.scale2x(surf) if randint(0, 4) < 2 else surf
            pos = [WINDOW_WIDTH + randint(50, 100), randint(0, WINDOW_HEIGHT)]
            self.current_clouds.append(
                {"surf": surf, "pos": pos, "speed": randint(20, 50)}
            )

            # 画面外の雲は削除 = 画面内の雲のみ残す
            self.current_clouds = [
                cloud for cloud in self.current_clouds if cloud["pos"][0] > -400
            ]

    def startup_clouds(self):
        for i in range(20):
            surf = choice(self.cloud_surf)
            surf = pygame.transform.scale2x(surf) if randint(0, 4) < 2 else surf
            pos = [randint(0, WINDOW_WIDTH), randint(0, WINDOW_HEIGHT)]
            self.current_clouds.append(
                {"surf": surf, "pos": pos, "speed": randint(20, 50)}
            )

    def run(self, dt):
        self.event_loop()

        # updating
        self.animation_update(dt)
        self.canvas_objects.update(dt)
        self.object_timer.update()

        # drawing
        self.display_surface.fill("gray")
        self.display_sky(dt)
        self.draw_level()
        self.draw_tile_lines()
        # pygame.draw.circle(
        #     self.display_surface, color="red", center=self.origin, radius=10
        # )
        self.preview()
        self.menu.display(self.selection_index)


class CanvasTile:
    def __init__(self, tile_id, offset=vector()):
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

        self.add_id(tile_id, offset=offset)
        self.is_empty = False

    def add_id(self, tile_id, offset=vector()):
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
            case _:  # objects
                if (tile_id, offset) not in self.objects:
                    self.objects.append((tile_id, offset))

    def remove_id(self, tile_id):
        options = {key: value["style"] for key, value in EDITOR_DATA.items()}
        match options[tile_id]:
            case "terrain":
                self.has_terrain = False
            case "water":
                self.has_water = False
            case "coin":
                self.coin = None
            case "enemy":
                self.enemy = None
        self.check_content()

    def check_content(self):
        # すべてのオブジェクトがなくなったかチェックする
        if (
            not self.has_terrain
            and not self.has_water
            and not self.coin
            and not self.enemy
        ):
            self.is_empty = True

    def get_water(self):
        return "bottom" if self.water_on_top else "top"

    def get_terrain(self):
        return "".join(self.terrain_neighbors)


class CanvasObject(pygame.sprite.Sprite):
    def __init__(self, pos, frames, tile_id, origin, group):
        super().__init__(group)

        self.tile_id = tile_id

        # animation
        self.frames = frames
        self.frame_index = 0

        self.image = self.frames[self.frame_index]
        self.rect = self.image.get_rect(center=pos)

        # movement
        self.distance_to_origin = vector(self.rect.topleft) - origin
        self.selected = False
        self.mouse_offset = vector()

    def start_drag(self):
        self.selected = True
        # Spriteの左上からユーザがクリックした座標へのoffset
        self.mouse_offset = vector(mouse_pos()) - vector(self.rect.topleft)

    def drag(self):
        if self.selected:
            self.rect.topleft = mouse_pos() - self.mouse_offset

    def drag_end(self, origin):
        self.selected = False
        self.distance_to_origin = vector(self.rect.topleft) - origin

    def animate(self, dt):
        self.frame_index += ANIMATION_SPEED * dt
        self.frame_index = (
            0 if self.frame_index >= len(self.frames) else self.frame_index
        )
        self.image = self.frames[int(self.frame_index)]
        self.rect = self.image.get_rect(midbottom=self.rect.midbottom)

    def pan_pos(self, origin):
        self.rect.topleft = origin + self.distance_to_origin

    def update(self, dt):
        self.animate(dt)
        self.drag()
