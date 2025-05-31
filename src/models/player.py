import pygame
import math
from models.bullet import Bullet
from constants import FPS, FIRE_DELAY, WIDTH, PLAYER_SPEED, DASH_DISTANCE, DASH_COOLDOWN, TRAIL_SPACING, HEIGHT

class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.base_img = pygame.Surface((64, 20))
        self.base_img.fill((200, 60, 40))
        self.turret_img = pygame.Surface((18, 18), pygame.SRCALPHA)
        pygame.draw.circle(self.turret_img, (90, 200, 90), (9, 9), 9)
        self.image = self._compose_image(0)
        self.rect = self.image.get_rect(midbottom=(WIDTH//6, HEIGHT-30))
        self.last_shot = 0.0
        self.last_dash = 0.0
        self.trails = []  # list of dicts {image, rect, alpha}

    def _compose_image(self, angle_deg):
        turret_rot = pygame.transform.rotate(self.turret_img, -angle_deg)
        img = self.base_img.copy()
        tr = turret_rot.get_rect(center=(self.base_img.get_width()//2,
                                         self.base_img.get_height()//2))
        img.blit(turret_rot, tr)
        return img

    def update(self, key_state, mouse_pos, dt, current_time, bullets, bullet_count=1, bullet_size=10, fire_delay=FIRE_DELAY):
        # Horizontal movement via keyboard
        move_dir = 0
        if key_state[pygame.K_a] or key_state[pygame.K_LEFT]:
            move_dir -= 1
        if key_state[pygame.K_d] or key_state[pygame.K_RIGHT]:
            move_dir += 1
        self.rect.x += move_dir * PLAYER_SPEED * dt
        # Dash with Shift
        dash_pressed = key_state[pygame.K_LSHIFT] or key_state[pygame.K_RSHIFT]
        if dash_pressed and current_time - self.last_dash >= DASH_COOLDOWN:
            start_x = self.rect.centerx  # before dash
            dash_dir = move_dir if move_dir != 0 else (1 if mouse_pos[0] > self.rect.centerx else -1)
            end_x = start_x + dash_dir * DASH_DISTANCE
            self.rect.x = end_x
            # generate multiple ghosts between start_x and end_x
            steps = abs(int(DASH_DISTANCE // TRAIL_SPACING))
            for i in range(1, steps + 1):
                ghost_x = start_x + dash_dir * i * TRAIL_SPACING
                trail_img = self.image.copy().convert_alpha()
                trail_img.set_alpha(180)
                trail_rect = trail_img.get_rect(center=(ghost_x, self.rect.centery))
                # fade rate proportional to distance: farther ghosts fade faster
                factor = (steps - i + 1) / steps  # 1 for farthest, down to ~0 for closest
                self.trails.append({'image': trail_img, 'rect': trail_rect, 'alpha': 180,
                                     'fade_rate': 600 * factor})
            self.last_dash = current_time
        # clamp inside screen (after movement and potential dash)
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > WIDTH:
            self.rect.right = WIDTH

        dx = mouse_pos[0] - self.rect.centerx
        dy = mouse_pos[1] - self.rect.centery
        angle = math.atan2(dy, dx)
        angle_deg = math.degrees(angle)
        self.image = self._compose_image(angle_deg)
        
        # Disparar balas según el fire_delay proporcionado (puede ser modificado por powerups)
        if current_time - self.last_shot >= fire_delay:
            self.last_shot = current_time
            
            # Disparo múltiple basado en bullet_count (powerup)
            if bullet_count == 1:
                # Disparo normal
                bullet = Bullet(self.rect.center, angle, bullet_size)
                bullets.add(bullet)
            elif bullet_count == 3:
                # Triple disparo (uno recto, dos laterales)
                angle_spread = 15  # grados de separación
                bullet_center = Bullet(self.rect.center, angle, bullet_size)
                bullet_left = Bullet(self.rect.center, angle + math.radians(angle_spread), bullet_size)
                bullet_right = Bullet(self.rect.center, angle - math.radians(angle_spread), bullet_size)
                bullets.add(bullet_center, bullet_left, bullet_right)
            else:
                # Cualquier otro número de disparos en abanico
                if bullet_count > 1:
                    angle_spread_total = 30  # ángulo total del abanico
                    for i in range(bullet_count):
                        if bullet_count > 1:
                            current_angle = angle - math.radians(angle_spread_total/2) + math.radians(angle_spread_total * i / (bullet_count-1))
                        else:
                            current_angle = angle
                        bullet = Bullet(self.rect.center, current_angle, bullet_size)
                        bullets.add(bullet)

        # fade trails with individual rates
        for t in self.trails[:]:
            t['alpha'] -= t.get('fade_rate', 600) * dt
            if t['alpha'] <= 0:
                self.trails.remove(t)
            else:
                t['image'].set_alpha(int(t['alpha']))

    def draw_trails(self, surface):
        for t in self.trails:
            surface.blit(t['image'], t['rect'])