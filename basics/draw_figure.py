import sys

import pygame

screen_size = (640, 480)

pygame.init()
screen = pygame.display.set_mode(screen_size)
pygame.display.set_caption("図形の描画")

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    screen.fill((0, 0, 0))

    # 黄色の長方形
    pygame.draw.rect(screen, color=(255, 255, 0), rect=pygame.Rect(10, 10, 300, 200))

    # 赤い円
    pygame.draw.circle(screen, color=(255, 0, 0), center=(320, 240), radius=100)

    # 紫の楕円
    pygame.draw.ellipse(screen, color=(255, 0, 255), rect=(400, 300, 200, 100))

    # 白い線
    pygame.draw.line(
        screen, color=(255, 255, 255), start_pos=(0, 0), end_pos=(640, 480), width=5
    )

    pygame.display.update()
