import pygame
import random
import math
from constants import WIDTH, HEIGHT, FPS, ASSETS
from PIL import Image, ImageDraw


class UFO(pygame.sprite.Sprite):
    
    def __init__(self):
        super().__init__()
        # Load sprite image
        img_path = ASSETS / "enemies" / "blue_ufo" / "blue_ufo1.png"
        try:
            w, h = 64, 32
            img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            draw.ellipse([(0, h//4), (w, h)], fill=(80, 160, 255, 255))
            draw.ellipse([(w*0.25, 0), (w*0.75, h*0.6)], fill=(120, 200, 255, 255))
            UFO._cached_img = pygame.image.load(str(img_path)).convert_alpha()
        except Exception as ex:
            print(f"[ERROR] Could not generate sprite: {ex}. Using pygame rect.")
            fallback = pygame.Surface((32, 16))
            fallback.fill((140, 180, 255))
            UFO._cached_img = fallback
        self.image = UFO._cached_img
        y = random.randint(40, HEIGHT // 2)
        self.rect = self.image.get_rect(midleft=(-self.image.get_width(), y))
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
