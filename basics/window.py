import sys

import pygame

screen_size = (640, 480)

pygame.init()
screen = pygame.display.set_mode(screen_size)
pygame.display.set_caption("ウィンドウの作成")

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    screen.fill((0, 0, 255))
    pygame.display.update()
