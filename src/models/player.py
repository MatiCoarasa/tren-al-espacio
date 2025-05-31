import pygame
import math
from models.bullet import Bullet
from constants import FPS, FIRE_DELAY

class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.base_img = pygame.Surface((64, 20))
        self.base_img.fill((200, 60, 40))
        self.turret_img = pygame.Surface((18, 18), pygame.SRCALPHA)
        pygame.draw.circle(self.turret_img, (90, 200, 90), (9, 9), 9)
        self.image = self._compose_image(0)
        self.rect = self.image.get_rect(midbottom=(640//6, 360-30))
        self.last_shot = 0.0

    def _compose_image(self, angle_deg):
        turret_rot = pygame.transform.rotate(self.turret_img, -angle_deg)
        img = self.base_img.copy()
        tr = turret_rot.get_rect(center=(self.base_img.get_width()//2,
                                         self.base_img.get_height()//2))
        img.blit(turret_rot, tr)
        return img

    def update(self, mouse_pos, current_time, bullets):
        dx = mouse_pos[0] - self.rect.centerx
        dy = mouse_pos[1] - self.rect.centery
        angle = math.atan2(dy, dx)
        angle_deg = math.degrees(angle)
        self.image = self._compose_image(angle_deg)
        if current_time - self.last_shot >= FIRE_DELAY:
            self.last_shot = current_time
            bullet = Bullet(self.rect.center, angle)
            bullets.add(bullet)