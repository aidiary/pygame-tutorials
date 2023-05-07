import sys

import pygame

screen_size = (640, 480)

pygame.init()
screen = pygame.display.set_mode(screen_size)
pygame.display.set_caption("透明色の指定")

plane_img = pygame.image.load("./assets/plane.png").convert()

# 左上の色を透明色に
colorkey = plane_img.get_at((0, 0))
print(colorkey)
plane_img.set_colorkey(colorkey, pygame.RLEACCEL)

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    screen.fill((0, 0, 0))
    screen.blit(plane_img, dest=(100, 100))

    pygame.display.update()
