import sys

import pygame

screen_size = (640, 480)

pygame.init()
screen = pygame.display.set_mode(screen_size)
pygame.display.set_caption("Hello, world!")

# フォントの作成
sysfont = pygame.font.SysFont(None, 80)

# テキストを描画したSurfaceを作成
hello1 = sysfont.render("Hello, world!", False, (0, 0, 0))
hello2 = sysfont.render("Hello, world!", True, (0, 0, 0))
hello3 = sysfont.render("Hello, world!", True, (255, 0, 0), (255, 255, 0))


while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    screen.fill((0, 0, 255))

    # テキストを描画する
    screen.blit(hello1, (20, 50))
    screen.blit(hello2, (20, 150))
    screen.blit(hello3, (20, 250))
    pygame.display.update()
