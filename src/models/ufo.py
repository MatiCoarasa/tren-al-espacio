import pygame
import random
from constants import WIDTH, HEIGHT, FPS

class UFO(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((32, 16))
        self.image.fill((140, 180, 255))
        y = random.randint(40, HEIGHT // 2)
        self.rect = self.image.get_rect(midleft=(-32, y))
        self.speed = random.uniform(60, 120) / FPS

    def update(self):
        self.rect.x += self.speed
        if self.rect.left > WIDTH + 32:
            self.kill()