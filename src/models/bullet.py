import pygame
import math
from constants import BULLET_SPEED, FPS, WIDTH, HEIGHT

class Bullet(pygame.sprite.Sprite):
    def __init__(self, pos, angle):
        super().__init__()
        self.image = pygame.Surface((10, 10))
        self.image.fill((255, 255, 255))
        self.rect = self.image.get_rect(center=pos)
        self.vx = math.cos(angle) * BULLET_SPEED / FPS
        self.vy = math.sin(angle) * BULLET_SPEED / FPS

    def update(self):
        self.rect.x += self.vx
        self.rect.y += self.vy
        if (self.rect.right < 0 or self.rect.left > WIDTH or
                self.rect.bottom < 0 or self.rect.top > HEIGHT):
            self.kill()
