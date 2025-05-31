import pygame
from constants import WIDTH, HEIGHT


class ScrollingBackground:
    """Manages a scrolling background with parallax effect"""
    
    def __init__(self, background_path, scroll_speed=50):
        """
        Initialize a scrolling background
        
        Args:
            background_path: Path to the background image
            scroll_speed: Scrolling speed in pixels per second
        """
        self.scroll_speed = scroll_speed
        self.offset = 0
        
        # Load the background image
        try:
            self.original_bg = pygame.image.load(str(background_path)).convert()
            self.bg_height = HEIGHT
            
            # Para imágenes panorámicas, preservar la relación de aspecto
            orig_width = self.original_bg.get_width()
            orig_height = self.original_bg.get_height()
            
            # Si es una imagen muy ancha (panorámica), mantenemos su ancho original
            # y ajustamos solo la altura
            if orig_width > WIDTH * 1.5:  # Es panorámica (más de 1.5 veces el ancho de la pantalla)
                scale_factor = HEIGHT / orig_height
                scaled_width = int(orig_width * scale_factor)
                self.background = pygame.transform.scale(self.original_bg, (scaled_width, HEIGHT))
                print(f"Usando imagen panorámica: {scaled_width}x{HEIGHT}")
            else:
                # Imagen normal, ajustar a tamaño de pantalla
                self.background = pygame.transform.scale(self.original_bg, (WIDTH, HEIGHT))
            
            # Creamos un surface más ancho para el desplazamiento continuo
            self.bg_width = self.background.get_width()
            repeat_count = max(2, (WIDTH * 2) // self.bg_width + 1)
            self.double_bg = pygame.Surface((self.bg_width * repeat_count, HEIGHT))
            
            # Repetimos la imagen tantas veces como sea necesario para cubrir el doble del ancho
            for i in range(repeat_count):
                self.double_bg.blit(self.background, (i * self.bg_width, 0))
            
        except pygame.error as e:
            print(f"Error loading background: {e}")
            # Create a simple background as fallback
            self.background = pygame.Surface((WIDTH, HEIGHT))
            self.background.fill((10, 10, 30))
            self.bg_width = WIDTH
            self.double_bg = pygame.Surface((WIDTH * 2, HEIGHT))
            self.double_bg.fill((10, 10, 30))
    
    def update(self, dt):
        """Update the background position"""
        self.offset = (self.offset + self.scroll_speed * dt) % self.bg_width
        
    def draw(self, screen):
        """Draw the scrolling background to the screen"""
        screen.blit(self.double_bg, (-self.offset, 0))
