import pygame
import math
from constants import BULLET_SPEED, FPS, WIDTH, HEIGHT

class Bullet(pygame.sprite.Sprite):
    
    def __init__(self, pos, angle, size=10, color=(255, 255, 255)):
        super().__init__()
        self.image = pygame.Surface((size, size))
        self.image.fill(color)
        # Agregar un brillo central para que se vea mejor
        if size > 5:
            inner_size = max(4, int(size * 0.6))
            inner_rect = pygame.Rect((size-inner_size)//2, (size-inner_size)//2, inner_size, inner_size)
            pygame.draw.rect(self.image, (255, 255, 200), inner_rect)
        self.rect = self.image.get_rect(center=pos)
        self.vx = math.cos(angle) * BULLET_SPEED / FPS
        self.vy = math.sin(angle) * BULLET_SPEED / FPS

    def update(self):
        self.rect.x += self.vx
        self.rect.y += self.vy
        if (self.rect.right < 0 or self.rect.left > WIDTH or
                self.rect.bottom < 0 or self.rect.top > HEIGHT):
            self.kill()
