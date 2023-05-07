import sys

import pygame

screen_size = (640, 480)

pygame.init()
screen = pygame.display.set_mode(screen_size)
pygame.display.set_caption("マウスイベント")

back_img = pygame.image.load("./assets/moriyama.jpg").convert()
python_img = pygame.image.load("./assets/python.png").convert_alpha()

cur_pos = (0, 0)
pythons_pos = []

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            x, y = event.pos
            x -= python_img.get_width() / 2
            y -= python_img.get_width() / 2
            pythons_pos.append((x, y))

        if event.type == pygame.MOUSEMOTION:
            x, y = event.pos
            x -= python_img.get_width() / 2
            y -= python_img.get_width() / 2
            cur_pos = x, y

    screen.blit(back_img, dest=(0, 0))
    screen.blit(python_img, dest=cur_pos)
    for pos in pythons_pos:
        screen.blit(python_img, pos)

    pygame.display.update()
