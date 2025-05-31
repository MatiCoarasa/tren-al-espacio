import pygame
import math
import random
from constants import HEIGHT, FPS

class Powerup(pygame.sprite.Sprite):
    """Clase que representa un powerup que cae y puede ser recogido por el jugador"""
    
    def __init__(self, position, powerup_data):
        super().__init__()
        
        # Guardar datos del powerup
        self.id = powerup_data.get("id", "unknown")
        self.name = powerup_data.get("name", "Powerup")
        self.description = powerup_data.get("description", "")
        self.duration = powerup_data.get("duration", 10)
        self.color = powerup_data.get("color", (200, 200, 200))
        self.effect = powerup_data.get("effect", "")
        self.value = powerup_data.get("value", 1)
        
        # Crear imagen del powerup
        self.size = 20
        self.image = self._create_powerup_image()
        self.rect = self.image.get_rect(center=position)
        
        # Variables de movimiento
        self.speed = random.randint(80, 120) / FPS
        self.oscillation_speed = random.uniform(2, 4)
        self.oscillation_width = random.randint(20, 40)
        self.start_x = position[0]
        self.time_alive = 0
        
        # Tiempo de vida
        self.max_lifetime = 10  # segundos antes de desaparecer
        self.spawn_time = pygame.time.get_ticks() / 1000.0
        self.flash_start = self.max_lifetime - 3  # comenzar a parpadear 3 segundos antes de desaparecer
        self.visible = True
        
    def _create_powerup_image(self):
        """Crea una imagen para el powerup basada en su efecto y color"""
        base_img = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        
        # Dibujar caja base
        color_dark = tuple(max(0, c - 70) for c in self.color)
        
        # Sombra
        pygame.draw.rect(base_img, (20, 20, 20, 100), 
                        pygame.Rect(2, 2, self.size-2, self.size-2), 0, 3)
        
        # Cuerpo principal
        pygame.draw.rect(base_img, self.color, 
                        pygame.Rect(0, 0, self.size-2, self.size-2), 0, 3)
        
        # Brillo superior
        pygame.draw.rect(base_img, (255, 255, 255, 80), 
                        pygame.Rect(2, 2, self.size-8, 4), 0, 2)
        
        # Borde
        pygame.draw.rect(base_img, color_dark, 
                        pygame.Rect(0, 0, self.size-2, self.size-2), 1, 3)
        
        # Icono interior basado en el efecto
        if self.effect == "bullet_count":
            # Tres puntos para triple disparo
            for i in range(3):
                x = self.size//2 + (i-1) * 4
                pygame.draw.circle(base_img, (255, 255, 255), (x, self.size//2), 2)
        elif self.effect == "player_speed":
            # Flecha de velocidad
            points = [(5, self.size//2), (self.size-8, self.size//2-4), 
                    (self.size-8, self.size//2+4)]
            pygame.draw.polygon(base_img, (255, 255, 255), points)
        elif self.effect == "shield":
            # Escudo
            pygame.draw.arc(base_img, (255, 255, 255), 
                        pygame.Rect(4, 4, self.size-10, self.size-10), 
                        math.radians(30), math.radians(330), 2)
        elif self.effect == "fire_rate":
            # Símbolo de rayo
            points = [(self.size//2, 4), (self.size//2-4, self.size//2), 
                    (self.size//2+2, self.size//2), (self.size//2-2, self.size-6)]
            pygame.draw.polygon(base_img, (255, 255, 255), points)
        elif self.effect == "score_multiplier":
            # Símbolo de x2
            font = pygame.font.SysFont(None, 14)
            txt = font.render("x" + str(int(self.value)), True, (255, 255, 255))
            txt_rect = txt.get_rect(center=(self.size//2, self.size//2))
            base_img.blit(txt, txt_rect)
        elif self.effect == "bullet_size":
            # Círculo grande
            pygame.draw.circle(base_img, (255, 255, 255), 
                            (self.size//2, self.size//2), self.size//4)
        elif self.effect == "invincibility":
            # Estrella
            points = []
            for i in range(5):
                angle = math.radians(i * 72 - 90)
                points.append((self.size//2 + 6 * math.cos(angle), 
                            self.size//2 + 6 * math.sin(angle)))
                angle = math.radians(i * 72 - 90 + 36)
                points.append((self.size//2 + 3 * math.cos(angle), 
                            self.size//2 + 3 * math.sin(angle)))
            pygame.draw.polygon(base_img, (255, 255, 255), points)
            
        return base_img
        
    def update(self):
        """Actualiza la posición y estado del powerup"""
        now = pygame.time.get_ticks() / 1000.0
        dt = 1/FPS
        self.time_alive += dt
        
        # Movimiento: caída con oscilación horizontal
        self.rect.y += self.speed
        self.rect.x = self.start_x + self.oscillation_width * math.sin(self.time_alive * self.oscillation_speed)
        
        # Verificar tiempo de vida
        lifetime = now - self.spawn_time
        if lifetime > self.max_lifetime:
            self.kill()
            return
            
        # Parpadeo cuando está a punto de desaparecer
        if lifetime > self.flash_start:
            if (lifetime * 5) % 1 > 0.5:  # Parpadeo más rápido hacia el final
                self.visible = False
            else:
                self.visible = True
                
        # Salir de la pantalla
        if self.rect.top > HEIGHT:
            self.kill()
            
    def draw(self, surface):
        """Dibuja el powerup si es visible"""
        if self.visible:
            surface.blit(self.image, self.rect)
