import pygame
from editor import Editor
from settings import WINDOW_HEIGHT, WINDOW_WIDTH


class Main:
    def __init__(self):
        pygame.init()
        self.display_surface = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.clock = pygame.time.Clock()

        self.editor = Editor()

    def run(self):
        while True:
            # 前回実行されてからの経過時間を返す
            dt = self.clock.tick() / 1000

            self.editor.run(dt)
            pygame.display.update()


if __name__ == "__main__":
    main = Main()
    main.run()
