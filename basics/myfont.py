import sys

import pygame

screen_size = (640, 480)

pygame.init()
screen = pygame.display.set_mode(screen_size)
pygame.display.set_caption("フォントファイルのロード")

# フォントの作成
myfont = pygame.font.Font("./assets/x12y16pxMaruMonica.ttf", 64)

# テキストを描画したSurfaceを作成
hello = myfont.render("こんにちは！世界", True, (255, 0, 0))
print(hello)

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    screen.fill((0, 0, 255))

    # テキストを描画する
    screen.blit(hello, (20, 50))
    pygame.display.update()
