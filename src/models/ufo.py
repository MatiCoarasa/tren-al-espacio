import pygame
import random
import math
from constants import WIDTH, HEIGHT, FPS, ASSETS, MIN_SIZE, MAX_SIZE

class UFO(pygame.sprite.Sprite):

    _cached_img = None  # Class variable to cache the image
    
    def __init__(self, n):
        super().__init__()
        # Load sprite image
        img_path = ASSETS / "enemies" / "blue_ufo" / "blue_ufo1.png"
        if not UFO._cached_img:
            UFO._cached_img = pygame.image.load(str(img_path)).convert_alpha()
        self.image = UFO._cached_img

        # Randomly scale the image to a size between MIN_SIZE and MAX_SIZE
        scale_factor = random.uniform(MIN_SIZE / self.image.get_width(), MAX_SIZE / self.image.get_width())
        self.image = pygame.transform.scale(self.image, 
                                            (int(self.image.get_width() * scale_factor), 
                                             int(self.image.get_height() * scale_factor)))

        y = random.randint(40, HEIGHT // 2)
        self.rect = self.image.get_rect(midleft=(-self.image.get_width(), y))
        self.base_speed = random.uniform(60, 120) / FPS
        self.amp = random.uniform(20, 40) / FPS  # amplitude of speed oscillation
        self.spawn_time = pygame.time.get_ticks() / 1000.0  # seconds
        self.id = n

    def update(self):
        now = pygame.time.get_ticks() / 1000.0
        t = now - self.spawn_time
        # Speed oscillates with time
        self._update_movement(t)

        # Remove UFO if it goes off-screen
        if self.rect.left > WIDTH + 32:
            self.kill()

    def _update_movement(self, t):
        x_speed = self.base_speed + self.base_speed * self.amp * math.sin(2 * math.pi * t)
        self.rect.x += x_speed
        
        y_speed = 2 * math.cos(2 * math.pi * t)
        self.rect.y += y_speed

    def __str__(self):
        return f"[{self.id}] UFO at {self.rect.topleft} with speed {self.base_speed:.2f} and amplitude {self.amp:.2f}"
