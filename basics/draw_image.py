import sys

import pygame

screen_size = (640, 480)

pygame.init()
screen = pygame.display.set_mode(screen_size)
pygame.display.set_caption("画像の描画")

back_img = pygame.image.load("./assets/moriyama.jpg").convert()
python_img = pygame.image.load("./assets/python.png").convert_alpha()

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    screen.blit(back_img, dest=(0, 0))
    screen.blit(python_img, dest=(320, 400))

    pygame.display.update()
