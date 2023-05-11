import pygame
from editor import Editor
from pygame.image import load
from settings import WINDOW_HEIGHT, WINDOW_WIDTH
from support import import_folder_dict


class Main:
    def __init__(self):
        pygame.init()
        self.display_surface = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.clock = pygame.time.Clock()
        self.imports()

        self.editor = Editor(self.land_tiles)

        # マウスカーソルを変更
        surf = load("graphics/cursors/mouse.png").convert_alpha()
        # カーソル画像の (0, 0) をクリックできるエリアとして指定
        cursor = pygame.cursors.Cursor((0, 0), surf)
        pygame.mouse.set_cursor(cursor)

    def imports(self):
        self.land_tiles = import_folder_dict("graphics/terrain/land")

    def run(self):
        while True:
            # 前回実行されてからの経過時間を返す
            dt = self.clock.tick() / 1000

            self.editor.run(dt)
            pygame.display.update()


if __name__ == "__main__":
    main = Main()
    main.run()
