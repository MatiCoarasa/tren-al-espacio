import pygame
import random
import math
from constants import WIDTH, FPS, MAX_SPAWN_HEIGHT, MIN_SPAWN_HEIGHT

class UFO(pygame.sprite.Sprite):
    
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((32, 16))
        self.image.fill((140, 180, 255))
        y = random.randint(MAX_SPAWN_HEIGHT, MIN_SPAWN_HEIGHT)
        self.rect = self.image.get_rect(midleft=(-32, y))
        self.base_speed = random.uniform(60, 120) / FPS
        self.amp = random.uniform(20, 40) / FPS  # amplitude of speed oscillation
        self.spawn_time = pygame.time.get_ticks() / 1000.0  # seconds
        print(self)

    def update(self):
        now = pygame.time.get_ticks() / 1000.0
        t = now - self.spawn_time
        # Speed oscillates with time
        self._update_movement(t)

        # Remove UFO if it goes off-screen
        if self.rect.left > WIDTH + 32:
            self.kill()

    def _update_movement(self, t):
        x_speed = self.base_speed + self.amp * math.sin(2 * math.pi * t)
        y_speed = math.cos(2 * math.pi * t)
        self.rect.x += x_speed
        self.rect.y += y_speed

    def __str__(self):
        return f"UFO at {self.rect.topleft} with speed {self.base_speed:.2f} and amplitude {self.amp:.2f}"
