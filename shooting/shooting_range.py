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


class GameState:
    def __init__(self):
        self.state = "intro"

    def intro(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                self.state = "main_game"

        # Drawing
        screen.blit(background, (0, 0))
        screen.blit(ready_text, (screen_width / 2 - 115, screen_height / 2 - 33))
        player_group.draw(screen)
        player_group.update()

        pygame.display.flip()

    def main_game(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN:
                crosshair.shoot(target_group)

        # Drawing
        screen.blit(background, (0, 0))
        target_group.draw(screen)
        player_group.draw(screen)
        player_group.update()

        pygame.display.flip()

    def state_manager(self):
        if self.state == "intro":
            self.intro()
        if self.state == "main_game":
            self.main_game()


pygame.init()
clock = pygame.time.Clock()
game_state = GameState()

# Game Screen
screen_width = 1024
screen_height = 768
screen = pygame.display.set_mode((screen_width, screen_height))

background = pygame.image.load("BG.png")
ready_text = pygame.image.load("ready_text.png")
pygame.mouse.set_visible(False)

# Crosshair
crosshair = Crosshair("crosshair.png")
player_group = pygame.sprite.Group()
player_group.add(crosshair)

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
    game_state.state_manager()
    clock.tick(60)
