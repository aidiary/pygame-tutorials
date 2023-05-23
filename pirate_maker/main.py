import pygame
from editor import Editor
from level import Level
from pygame.image import load
from pygame.math import Vector2 as vector
from settings import WINDOW_HEIGHT, WINDOW_WIDTH
from support import import_folder_dict


class Main:
    def __init__(self):
        pygame.init()
        self.display_surface = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.clock = pygame.time.Clock()
        self.imports()

        self.editor_active = True
        self.transition = Transition(self.toggle)

        # ステージの編集ができるエディタモード
        self.editor = Editor(self.land_tiles, self.switch)

        # マウスカーソルを変更
        surf = load("graphics/cursors/mouse.png").convert_alpha()
        # カーソル画像の (0, 0) をクリックできるエリアとして指定
        cursor = pygame.cursors.Cursor((0, 0), surf)
        pygame.mouse.set_cursor(cursor)

    def imports(self):
        self.land_tiles = import_folder_dict("graphics/terrain/land")

    def switch(self, grid=None):
        # モード切り替えを開始する
        self.transition.active = True

        # エディタモードからswitchしたときにgrid（レベルの情報が入った辞書）が渡される
        # レベルモードからswitchしたときはgrid=NoneなのでLevelは作られない
        if grid:
            self.level = Level(grid, self.switch)

    def toggle(self):
        """エディタモードとレベルモードを切り替える"""
        self.editor_active = not self.editor_active

    def run(self):
        while True:
            # 前回実行されてからの経過時間を返す
            dt = self.clock.tick() / 1000

            if self.editor_active:
                self.editor.run(dt)
            else:
                self.level.run(dt)

            self.transition.display(dt)
            pygame.display.update()


class Transition:
    """エディタとレベルを切り替えるアニメーション"""

    def __init__(self, toggle):
        self.display_surface = pygame.display.get_surface()
        self.toggle = toggle
        self.active = False

        self.border_width = 0
        self.direction = 1
        self.center = (WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2)
        # 中心とスクリーンの間の半径
        self.radius = vector(self.center).magnitude()
        # 少し広めに取る
        self.threshold = self.radius + 100

    def display(self, dt):
        if self.active:
            # activeになったらborder_widthを大きくしていって画面を塗りつぶす
            self.border_width += 1000 * dt * self.direction

            # 画面を閉じ終わったら
            if self.border_width >= self.threshold:
                self.direction = -1
                # モード切り替え
                self.toggle()

            # 画面が開き終わったら
            if self.border_width < 0:
                self.active = False
                self.border_width = 0
                self.direction = 1

            pygame.draw.circle(
                self.display_surface,
                "black",
                self.center,
                self.radius,
                int(self.border_width),
            )


if __name__ == "__main__":
    main = Main()
    main.run()
