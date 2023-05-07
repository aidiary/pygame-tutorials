import random
import sys

import pygame


class Crosshair(pygame.sprite.Sprite):
    def __init__(self, picture_path):
        super().__init__()
        self.image = pygame.image.load(picture_path)
        self.rect = self.image.get_rect()
        self.gunshot = pygame.mixer.Sound("gunshot.wav")

    def shoot(self, target_group):
        self.gunshot.play()
        pygame.sprite.spritecollide(self, target_group, dokill=True)

    def update(self):
        self.rect.center = pygame.mouse.get_pos()


class Target(pygame.sprite.Sprite):
    def __init__(self, picture_path, pos_x, pos_y):
        super().__init__()
        self.image = pygame.image.load(picture_path)
        self.rect = self.image.get_rect()
        self.rect.center = (pos_x, pos_y)


pygame.init()
clock = pygame.time.Clock()

# Game Screen
screen_width = 1024
screen_height = 768
screen = pygame.display.set_mode((screen_width, screen_height))

background = pygame.image.load("BG.png")
pygame.mouse.set_visible(False)

# Crosshair
crosshair = Crosshair("crosshair.png")
crosshair_group = pygame.sprite.Group()
crosshair_group.add(crosshair)

# Target
target_group = pygame.sprite.Group()
for _ in range(20):
    target = Target(
        "target.png",
        random.randrange(0, screen_width),
        random.randrange(0, screen_height),
    )
    target_group.add(target)

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        if event.type == pygame.MOUSEBUTTONDOWN:
            crosshair.shoot(target_group)

    screen.blit(background, (0, 0))

    target_group.draw(screen)
    crosshair_group.draw(screen)
    crosshair_group.update()

    pygame.display.flip()
    clock.tick(60)
