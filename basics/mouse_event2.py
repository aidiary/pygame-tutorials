import sys

import pygame

screen_size = (640, 480)

pygame.init()
screen = pygame.display.set_mode(screen_size)
pygame.display.set_caption("マウスイベント2")

back_img = pygame.image.load("./assets/moriyama.jpg").convert()
python_img = pygame.image.load("./assets/python.png").convert_alpha()

cur_pos = (0, 0)
pythons_pos = []

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    screen.blit(back_img, dest=(0, 0))

    mouse_pressed = pygame.mouse.get_pressed()
    if mouse_pressed[0]:
        x, y = pygame.mouse.get_pos()
        x -= python_img.get_width() / 2
        y -= python_img.get_height() / 2
        pythons_pos.append((x, y))

    x, y = pygame.mouse.get_pos()
    x -= python_img.get_width() / 2
    y -= python_img.get_height() / 2
    cur_pos = (x, y)

    screen.blit(python_img, dest=cur_pos)
    for pos in pythons_pos:
        screen.blit(python_img, pos)

    pygame.display.update()
