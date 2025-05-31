import pygame
import json
import os
import random
import threading
from constants import FPS, FIRE_DELAY, LEVEL_DURATION, WIDTH, HEIGHT, BG_SCROLL_SPEED, USE_DALLE_BG, USE_OPENAI_API, POWERUP_DROP_CHANCE, ASSETS, TIME_BETWEEN_SPAWNS
from models.player import Player
from models.ufo import UFO
from models.powerup import Powerup
from background_generator import BackgroundGenerator
from scrolling_background import ScrollingBackground
from powerup_generator import PowerupGenerator

class Game:
    DIMENSION_SELECT, LOADING, PLAYING, HIGHSCORE, GAME_OVER = range(5)

    def __init__(self, screen):
        self.screen = screen
        # Iniciar con selección de dimensión si USE_DALLE_BG o USE_OPENAI_API están activados
        self.state = Game.DIMENSION_SELECT if (USE_DALLE_BG or USE_OPENAI_API) else Game.PLAYING
        self.clock = pygame.time.Clock()
        self.bullets = pygame.sprite.Group()
        self.ufo_bullets = pygame.sprite.Group()  # UFO bullets group
        self.enemies = pygame.sprite.Group()
        self.powerups = pygame.sprite.Group()  # Grupo para powerups
        self.player = Player()
        self.all_sprites = pygame.sprite.Group(self.player)
        self.level_start = pygame.time.get_ticks() / 1000.0
        self.spawn_timer = 0.0
        self.score = 0
        self.level = 1
        self.fire_delay = FIRE_DELAY
        
        # Variables para pantalla de carga
        self.loading_start_time = 0
        self.loading_dots = 0
        self.loading_dot_timer = 0
        self.loading_message = "Generando nivel"
        self.background_generated = False
        self.powerups_generated = False
        
        # Variables para animación de carga aleatoria
        self.loading_progress = 0
        self.loading_progress_target = 0
        self.loading_progress_speed = 0
        self.loading_messages = [
            "Creando dimensión",
            "Generando objetos",
            "Calculando física",
            "Ajustando colores",
            "Generando powerups",
            "Haciendo cosas",
            "Haciendo otras cosas",
        ]
        self.current_loading_message_index = 0
        self.message_change_timer = 0
        
        # Powerup system
        self.powerup_generator = PowerupGenerator()
        self.active_powerups = []  # Lista de powerups activos y su tiempo restante
        self.player_default_speed = self.player.speed if hasattr(self.player, 'speed') else 280
        self.bullet_default_size = 10
        self.bullet_count = 1
        self.score_multiplier = 1  # Multiplicador de puntuación por powerups
        self.has_shield = False
        self.is_invincible = False
        
        # --- Score rank system ---
        self.categories = ["D", "C", "B", "A", "S", "SS", "SSS"]
        self.category_index = 0          # Start at rank D
        self.multiplier = 1              # Score multiplier (1x,2x,...)
        self.PROGRESS_MAX = 100          # Full bar value for rank-up
        self.progress = 0                # Current bar value
        self.PROGRESS_PER_KILL = 20      # Bar increase per UFO destroyed
        self.DECAY_RATE = 10             # Bar decrease per second without kills
        
        # --- Time and highscore system ---
        self.time_elapsed = 0
        self.highscores = self._load_highscores()
        self.input_name = ""
        self.input_active = False
        self.input_cursor_visible = True
        self.input_cursor_time = 0
        
        # --- Background and dimension system ---
        self.bg_generator = BackgroundGenerator()
        self.background = None
        self.scrolling_bg = None
        self.dimension_prompt = ""
        self.dimension_input_active = True
        self.dimension_text = ""
        self.dimension_cursor_visible = True
        self.dimension_cursor_time = 0
        self.dimension_suggestions = [
            "un desierto espacial",
            "una nebulosa cósmica",
            "un paisaje alienígena",
            "una ciudad futurista",
            "un bosque de cristal"
        ]

        self.cursor_img = pygame.image.load(str(ASSETS / "projectiles" / "gun_sight" / "white_sight.png")).convert_alpha()

    def _spawn_enemy(self):
        u = UFO(len(self.enemies) + 1)
        self.enemies.add(u)
        self.all_sprites.add(u)

    def handle_events(self):
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                return False
            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                return False
            
            # Handle dimension selection input
            if self.state == Game.DIMENSION_SELECT:
                if e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_RETURN and self.dimension_text:
                        # Si no usamos ni DALL-E ni OpenAI API, comenzar directamente
                        if not USE_DALLE_BG and not USE_OPENAI_API:
                            self.state = Game.PLAYING
                            self.level_start = pygame.time.get_ticks() / 1000.0
                        else:
                            # Cambiar a pantalla de carga
                            self.state = Game.LOADING
                            self.loading_start_time = pygame.time.get_ticks() / 1000.0
                            self.background_generated = not USE_DALLE_BG  # Marcar como generado si no lo usamos
                            self.powerups_generated = not USE_OPENAI_API  # Marcar como generado si no lo usamos
                            # Iniciar generación en un thread separado
                            self._start_generation_thread()
                    elif e.key == pygame.K_BACKSPACE:
                        self.dimension_text = self.dimension_text[:-1]
                    elif e.key == pygame.K_TAB:
                        # Select from suggestions with Tab
                        if not self.dimension_suggestions:
                            continue
                        # Find the next suggestion
                        if not self.dimension_text:
                            self.dimension_text = self.dimension_suggestions[0]
                        else:
                            for i, suggestion in enumerate(self.dimension_suggestions):
                                if self.dimension_text in suggestion and self.dimension_text != suggestion:
                                    self.dimension_text = suggestion
                                    break
                            else:
                                self.dimension_text = self.dimension_suggestions[0]
                    elif e.unicode.isprintable() and len(self.dimension_text) < 50:
                        self.dimension_text += e.unicode
                
            # Handle highscore name input
            elif self.state == Game.HIGHSCORE:
                if e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_RETURN and self.input_name:
                        self._save_highscore()
                        self.state = Game.GAME_OVER
                    elif e.key == pygame.K_BACKSPACE:
                        self.input_name = self.input_name[:-1]
                    elif len(self.input_name) < 3 and e.unicode.isalpha():
                        self.input_name += e.unicode.upper()
        return True

    def _start_generation_thread(self):
        """Inicia la generación de fondo y powerups en un hilo separado"""
        def generation_thread():
            # Generar fondo con DALL-E si está activado
            if USE_DALLE_BG:
                print("Generando fondo con DALL-E para la dimensión: " + self.dimension_text)
                background_path = self.bg_generator.generate_background(self.dimension_text)
                if background_path:
                    self.scrolling_bg = ScrollingBackground(background_path, BG_SCROLL_SPEED)
                else:
                    background_path = self.bg_generator.load_default_background()
                    if background_path:
                        self.scrolling_bg = ScrollingBackground(background_path, BG_SCROLL_SPEED)
                self.background_generated = True
            elif not self.background_generated:  # Si ya está marcado como generado, no hacer nada
                # Si DALL-E está desactivado, cargar fondo por defecto
                background_path = self.bg_generator.load_default_background()
                if background_path:
                    self.scrolling_bg = ScrollingBackground(background_path, BG_SCROLL_SPEED)
                self.background_generated = True
                
            # Generar powerups temáticos si la API está activada
            if USE_OPENAI_API and not self.powerups_generated:
                print("Generando powerups temáticos para la dimensión: " + self.dimension_text)
                self.powerup_generator.set_dimension(self.dimension_text)
                self.powerups_generated = True
            elif not self.powerups_generated:
                self.powerups_generated = True
        
        # Iniciar thread
        thread = threading.Thread(target=generation_thread)
        thread.daemon = True  # El thread se cerrará cuando el programa principal termine
        thread.start()
    
    def update(self):
        dt = self.clock.tick(FPS) / 1000.0
        now = pygame.time.get_ticks() / 1000.0

        if self.state == Game.DIMENSION_SELECT:
            # Blink the cursor for dimension input
            self.dimension_cursor_time += dt
            if self.dimension_cursor_time >= 0.5:
                self.dimension_cursor_time = 0
                self.dimension_cursor_visible = not self.dimension_cursor_visible
                
        elif self.state == Game.LOADING:
            # Animar los puntos de carga
            self.loading_dot_timer += dt
            if self.loading_dot_timer >= 0.5:
                self.loading_dot_timer = 0
                self.loading_dots = (self.loading_dots + 1) % 4
                
            # Cambiar mensajes de carga aleatoriamente
            self.message_change_timer += dt
            if self.message_change_timer >= random.uniform(1.0, 2.5):
                self.message_change_timer = 0
                self.current_loading_message_index = random.randint(0, len(self.loading_messages) - 1)
                self.loading_message = self.loading_messages[self.current_loading_message_index]
                
            # Animar la barra de progreso aleatoriamente
            if random.random() < 0.03:  # Ocasionalmente cambiar la velocidad
                self.loading_progress_speed = random.uniform(0.1, 0.5)
                
            if random.random() < 0.05:  # Ocasionalmente establecer un nuevo objetivo
                # No permitir retroceder demasiado
                min_target = max(0.1, self.loading_progress - 0.1)  
                # No permitir llegar al 100% hasta que esté listo
                max_target = 0.95 if not (self.background_generated and self.powerups_generated) else 1.0
                self.loading_progress_target = random.uniform(min_target, max_target)
                
            # Avanzar hacia el objetivo gradualmente
            if self.loading_progress < self.loading_progress_target:
                self.loading_progress = min(self.loading_progress_target, 
                                           self.loading_progress + self.loading_progress_speed * dt)
            elif self.loading_progress > self.loading_progress_target:
                self.loading_progress = max(self.loading_progress_target, 
                                           self.loading_progress - self.loading_progress_speed * dt * 0.5)
                
            # Verificar si la generación ha terminado
            if self.background_generated and self.powerups_generated:
                # Asegurar que la barra llegue al 100% antes de continuar
                self.loading_progress_target = 1.0
                if self.loading_progress >= 0.99:
                    self.state = Game.PLAYING
                    self.level_start = pygame.time.get_ticks() / 1000.0
                
        elif self.state == Game.PLAYING:
            # Update scrolling background
            if self.scrolling_bg:
                self.scrolling_bg.update(dt)
            else:
                self.screen.fill((15, 15, 40))
            # Update level timer
            self.time_elapsed = now - self.level_start
            remaining_time = max(0, LEVEL_DURATION - self.time_elapsed)
            # Check if level is over
            if remaining_time <= 0:
                self.state = Game.HIGHSCORE
                self.input_active = True
                self.input_name = ""
                return
            # Game logic
            self.spawn_timer += dt
            if self.spawn_timer > TIME_BETWEEN_SPAWNS / self.level:
                self.spawn_timer = 0.0
                self._spawn_enemy()
            key_state = pygame.key.get_pressed()
            # Pasar parámetros de powerups al actualizar el jugador
            self.player.update(key_state, pygame.mouse.get_pos(), dt, now, self.bullets,
                               bullet_count=self.bullet_count,
                               bullet_size=self.bullet_default_size,
                               fire_delay=self.fire_delay)
            self.bullets.update()
            self.ufo_bullets.update()
            # UFOs shoot at player
            for ufo in self.enemies:
                ufo.update(self.player.rect.center, self.ufo_bullets)
            self.enemies.update()
            # Colisiones entre balas y enemigos
            hits = pygame.sprite.groupcollide(self.bullets, self.enemies, True, True)
            if hits:
                for bullet, ufos in hits.items():
                    for ufo in ufos:
                        # Posibilidad de soltar powerup al derrotar un UFO
                        if random.random() < POWERUP_DROP_CHANCE:
                            self._spawn_powerup(ufo.rect.center)
                kills = sum(len(v) for v in hits.values())
                self._increase_progress(kills)
                # Aplicar multiplicador de powerup y multiplicador de rango
                self.score += int(10 * self.multiplier * self.score_multiplier * kills)
            # UFO bullet hits player
            if pygame.sprite.spritecollide(self.player, self.ufo_bullets, True):
                if not self.is_invincible and not self.has_shield:
                    self.state = Game.HIGHSCORE
            # Actualizar powerups y verificar colisiones con jugador
            self.powerups.update()
            powerup_hits = pygame.sprite.spritecollide(self.player, self.powerups, True)
            for powerup in powerup_hits:
                self._apply_powerup(powerup)
            # Actualizar efectos de powerups activos
            self._update_active_powerups(dt)
            # Decay progress bar each frame
            self._decay_progress(dt)
            
        elif self.state == Game.HIGHSCORE:
            # Blink the cursor
            self.input_cursor_time += dt
            if self.input_cursor_time >= 0.5:
                self.input_cursor_time = 0
                self.input_cursor_visible = not self.input_cursor_visible
                
        elif self.state == Game.GAME_OVER:
            # Restart game if space is pressed
            if pygame.key.get_pressed()[pygame.K_SPACE]:
                self.__init__(self.screen)
                # Reiniciar el tiempo del nivel
                self.level_start = pygame.time.get_ticks() / 1000.0

    # ----- Powerup methods -----
    def _spawn_powerup(self, position):
        """Genera un powerup en la posición especificada"""
        # Obtener datos de powerup aleatorio
        powerup_data = self.powerup_generator.get_random_powerup()
        
        # Crear sprite de powerup
        powerup = Powerup(position, powerup_data)
        self.powerups.add(powerup)
        
    def _apply_powerup(self, powerup):
        """Aplica el efecto de un powerup al jugador"""
        # Mostrar texto de powerup obtenido
        print(f"Powerup activado: {powerup.name} - {powerup.description}")
        
        # Agregar a la lista de powerups activos
        self.active_powerups.append({
            'id': powerup.id,
            'name': powerup.name,
            'effect': powerup.effect,
            'value': powerup.value,
            'time_remaining': powerup.duration,
            'color': powerup.color
        })
        
        # Aplicar el efecto inmediatamente
        if powerup.effect == "bullet_count":
            self.bullet_count = int(powerup.value)
        elif powerup.effect == "player_speed":
            if hasattr(self.player, 'speed'):
                self.player.speed = self.player_default_speed * powerup.value
        elif powerup.effect == "shield":
            self.has_shield = True
        elif powerup.effect == "fire_rate":
            self.fire_delay = FIRE_DELAY * powerup.value
        elif powerup.effect == "score_multiplier":
            self.score_multiplier = powerup.value
        elif powerup.effect == "bullet_size":
            self.bullet_default_size = int(10 * powerup.value)
        elif powerup.effect == "invincibility":
            self.is_invincible = True
    
    def _update_active_powerups(self, dt):
        """Actualiza el tiempo restante de los powerups activos y elimina los que expiraron"""
        # Lista para almacenar powerups que siguen activos
        still_active = []
        
        for powerup in self.active_powerups:
            # Reducir tiempo restante
            powerup['time_remaining'] -= dt
            
            # Si aún tiene tiempo, mantenerlo activo
            if powerup['time_remaining'] > 0:
                still_active.append(powerup)
            else:
                # El powerup expiró, restaurar valores por defecto
                if powerup['effect'] == "bullet_count":
                    self.bullet_count = 1
                elif powerup['effect'] == "player_speed" and hasattr(self.player, 'speed'):
                    self.player.speed = self.player_default_speed
                elif powerup['effect'] == "shield":
                    self.has_shield = False
                elif powerup['effect'] == "fire_rate":
                    self.fire_delay = FIRE_DELAY
                elif powerup['effect'] == "score_multiplier":
                    self.score_multiplier = 1
                elif powerup['effect'] == "bullet_size":
                    self.bullet_default_size = 10
                elif powerup['effect'] == "invincibility":
                    self.is_invincible = False
                    
                print(f"Powerup {powerup['name']} ha expirado")
        
        # Actualizar lista de powerups activos
        self.active_powerups = still_active
    
    def draw(self):
        font_small = pygame.font.SysFont(None, 24)
        font_large = pygame.font.SysFont(None, 48)
        font_title = pygame.font.SysFont(None, 72)

        # Draw custom cursor
        mouse_pos = pygame.mouse.get_pos()
        cursor_rect = self.cursor_img.get_rect(center=mouse_pos)
        self.screen.blit(self.cursor_img, cursor_rect)
        
        if self.state == Game.LOADING:
            # Pantalla de carga
            self.screen.fill((10, 10, 30))  # Fondo oscuro
            
            # Dibujar estrellas en el fondo para que no sea tan vacío
            for i in range(100):
                x = WIDTH * ((i * 13) % 100) / 100
                y = HEIGHT * ((i * 17) % 100) / 100
                size = 1 + ((i * 7) % 3)
                brightness = 100 + ((i * 11) % 155)
                pygame.draw.circle(self.screen, (brightness, brightness, brightness), (x, y), size)
            
            # Mensaje de carga con puntos animados
            dots = '.' * self.loading_dots
            loading_text = font_large.render(f"{self.loading_message}{dots}", True, (255, 255, 255))
            loading_rect = loading_text.get_rect(center=(WIDTH//2, HEIGHT//2))
            self.screen.blit(loading_text, loading_rect)
            
            # Texto de la dimensión seleccionada
            dimension_txt = font_small.render(f"Preparando dimensión: {self.dimension_text}", True, (200, 200, 200))
            dimension_rect = dimension_txt.get_rect(center=(WIDTH//2, HEIGHT//2 + 80))
            self.screen.blit(dimension_txt, dimension_rect)
            
            # Barra de progreso animada
            bar_width, bar_height = 300, 10
            bar_rect = pygame.Rect(WIDTH//2 - bar_width//2, HEIGHT//2 + 120, bar_width, bar_height)
            pygame.draw.rect(self.screen, (50, 50, 50), bar_rect)  # Fondo de la barra
            
            # Usar el progreso animado aleatoriamente
            fill_width = int(bar_width * self.loading_progress)
                
            # Dibujar barra de progreso principal
            progress_rect = pygame.Rect(bar_rect.left, bar_rect.top, fill_width, bar_height)
            pygame.draw.rect(self.screen, (0, 180, 255), progress_rect)
            
            # Añadir algunos detalles para que parezca más técnico
            for i in range(1, 10):
                marker_x = bar_rect.left + (bar_width / 10) * i
                pygame.draw.line(self.screen, (70, 70, 70), 
                                (marker_x, bar_rect.top), 
                                (marker_x, bar_rect.bottom))
                
            # Dibujar pequeños bloques de "carga" aleatorios
            for i in range(3):
                if random.random() < 0.3:
                    block_width = random.randint(5, 20)
                    block_x = bar_rect.left + random.randint(0, bar_width - block_width)
                    block_color = (0, 255, 255) if random.random() < 0.3 else (0, 220, 255)
                    mini_rect = pygame.Rect(block_x, bar_rect.top, block_width, bar_height)
                    pygame.draw.rect(self.screen, block_color, mini_rect)
            pygame.draw.rect(self.screen, (255, 255, 255), bar_rect, 1)  # Borde
            
        elif self.state == Game.DIMENSION_SELECT:
            # Background for dimension selection
            self.screen.fill((10, 10, 30))
            
            # Draw stars in background
            for i in range(100):
                x = pygame.Rect(0, 0, WIDTH, HEIGHT).width * ((i * 13) % 100) / 100
                y = pygame.Rect(0, 0, WIDTH, HEIGHT).height * ((i * 17) % 100) / 100
                size = 1 + ((i * 7) % 3)
                brightness = 100 + ((i * 11) % 155)
                pygame.draw.circle(self.screen, (brightness, brightness, brightness), (x, y), size)
            
            # Title
            title = font_title.render("TREN AL ESPACIO", True, (255, 220, 0))
            title_rect = title.get_rect(center=(WIDTH//2, HEIGHT//4))
            self.screen.blit(title, title_rect)
            
            # Dimension prompt
            prompt = font_large.render("¿Qué tipo de dimensión te gustaría navegar?", True, (255, 255, 255))
            prompt_rect = prompt.get_rect(center=(WIDTH//2, HEIGHT//2 - 50))
            self.screen.blit(prompt, prompt_rect)
            
            # Draw input box
            input_box = pygame.Rect(WIDTH//2 - 300, HEIGHT//2, 600, 50)
            pygame.draw.rect(self.screen, (30, 30, 60), input_box)
            pygame.draw.rect(self.screen, (100, 100, 200), input_box, 2)
            
            # Draw input text with blinking cursor
            input_text = self.dimension_text
            if self.dimension_cursor_visible:
                input_text += "_"
            text_surf = font_large.render(input_text, True, (200, 200, 255))
            text_rect = text_surf.get_rect(center=input_box.center)
            self.screen.blit(text_surf, text_rect)
            
            # Draw suggestions
            y_pos = HEIGHT//2 + 70
            suggestion_txt = font_small.render("Sugerencias (presiona TAB para navegar):", True, (180, 180, 180))
            self.screen.blit(suggestion_txt, (WIDTH//2 - 200, y_pos))
            
            for i, suggestion in enumerate(self.dimension_suggestions):
                y_pos += 30
                is_highlighted = self.dimension_text in suggestion and self.dimension_text
                color = (255, 255, 0) if is_highlighted else (150, 150, 150)
                sugg_txt = font_small.render(suggestion, True, color)
                self.screen.blit(sugg_txt, (WIDTH//2 - 180, y_pos))
            
            # Instructions
            instruct = font_small.render("Presiona ENTER para comenzar", True, (200, 200, 200))
            instruct_rect = instruct.get_rect(center=(WIDTH//2, HEIGHT - 50))
            self.screen.blit(instruct, instruct_rect)
            
        elif self.state == Game.PLAYING:
            # Draw scrolling background if available
            if self.scrolling_bg:
                self.scrolling_bg.draw(self.screen)
            else:
                self.screen.fill((15, 15, 40))
            
            # Draw game elements
            self.all_sprites.draw(self.screen)
            self.player.draw_trails(self.screen)
            self.bullets.draw(self.screen)
            self.ufo_bullets.draw(self.screen)
            
            # Dibujar powerups (usando su método draw personalizado)
            for powerup in self.powerups:
                powerup.draw(self.screen)
            
            # Draw time remaining
            remaining_time = max(0, LEVEL_DURATION - self.time_elapsed)
            time_txt = font_small.render(f"TIME: {int(remaining_time)}", True, (255, 255, 255))
            self.screen.blit(time_txt, (WIDTH - 120, 10))
            
            # Numerical score
            score_txt = font_small.render(f"SCORE: {self.score}", True, (255, 255, 255))
            self.screen.blit(score_txt, (10, 10))
            
            # Smaller progress bar dimensions (defined first)
            bar_w, bar_h = 200, 10
            bar_x, bar_y = 12, 90
            
            # Category prominently displayed and centered
            rank_category = self.categories[self.category_index]
            rank_txt = font_large.render(f"{rank_category}", True, (255, 255, 0))
            # Center horizontally
            rank_x = bar_x + (bar_w - rank_txt.get_width()) // 2
            self.screen.blit(rank_txt, (rank_x, 40))
            pygame.draw.rect(self.screen, (60, 60, 60), (bar_x, bar_y, bar_w, bar_h))
            
            # Fill based on current progress
            fill_w = int(bar_w * self.progress / self.PROGRESS_MAX)
            
            # Color gradient based on rank
            color_map = {
                0: (150, 150, 150),  # D - gray
                1: (150, 100, 50),   # C - bronze
                2: (180, 180, 180),  # B - silver
                3: (212, 175, 55),   # A - gold
                4: (255, 50, 50),    # S - red
                5: (255, 80, 255),   # SS - pink
                6: (50, 220, 255)    # SSS - blue
            }
            bar_color = color_map.get(self.category_index, (50, 220, 50))
            pygame.draw.rect(self.screen, bar_color, (bar_x, bar_y, fill_w, bar_h))
            
            # Border
            pygame.draw.rect(self.screen, (255, 255, 255), (bar_x, bar_y, bar_w, bar_h), 1)
            
        elif self.state == Game.HIGHSCORE:
            # Highscore screen
            self.screen.fill((10, 10, 30))  # Dark background
            
            title = font_title.render("¡NIVEL COMPLETADO!", True, (255, 220, 0))
            subtitle = font_large.render(f"Puntuación: {self.score}", True, (255, 255, 255))
            
            # Center the title and subtitle
            title_rect = title.get_rect(center=(WIDTH//2, HEIGHT//3))
            subtitle_rect = subtitle.get_rect(center=(WIDTH//2, HEIGHT//3 + 70))
            
            self.screen.blit(title, title_rect)
            self.screen.blit(subtitle, subtitle_rect)
            
            # Input prompt
            prompt = font_large.render("Ingresa tus iniciales:", True, (255, 255, 255))
            prompt_rect = prompt.get_rect(center=(WIDTH//2, HEIGHT//2 + 30))
            self.screen.blit(prompt, prompt_rect)
            
            # Draw input box with blinking cursor
            input_txt = font_large.render(self.input_name, True, (255, 255, 0))
            cursor = ""
            if self.input_cursor_visible and len(self.input_name) < 3:
                cursor = "_"
            cursor_txt = font_large.render(cursor, True, (255, 255, 0))
            
            # Center the input text
            input_rect = input_txt.get_rect(center=(WIDTH//2, HEIGHT//2 + 100))
            self.screen.blit(input_txt, input_rect)
            
            # Add cursor at end of text
            cursor_x = input_rect.right + 5
            self.screen.blit(cursor_txt, (cursor_x, input_rect.y))
            
            # Instructions
            instruct = font_small.render("Presiona ENTER para guardar", True, (200, 200, 200))
            instruct_rect = instruct.get_rect(center=(WIDTH//2, HEIGHT//2 + 150))
            self.screen.blit(instruct, instruct_rect)
            
        elif self.state == Game.GAME_OVER:
            # Game over screen with highscores
            self.screen.fill((10, 10, 30))  # Dark background
            
            title = font_title.render("HIGHSCORES", True, (255, 220, 0))
            title_rect = title.get_rect(center=(WIDTH//2, 100))
            self.screen.blit(title, title_rect)
            
            # Draw highscore list
            y_pos = 180
            for i, (name, score) in enumerate(self.highscores[:10]):
                entry = font_large.render(f"{i+1}. {name} - {score}", True, (255, 255, 255))
                entry_rect = entry.get_rect(center=(WIDTH//2, y_pos))
                self.screen.blit(entry, entry_rect)
                y_pos += 50
            
            # Restart prompt
            restart = font_small.render("Presiona ESPACIO para jugar de nuevo", True, (200, 200, 200))
            restart_rect = restart.get_rect(center=(WIDTH//2, HEIGHT - 50))
            self.screen.blit(restart, restart_rect)

    # ----- Rank / Progress bar helpers -----
    def _increase_progress(self, kills: int = 1):
        """Increase the progress bar based on kills and handle rank up."""
        # Don't increase if already at max rank and full progress
        if self.category_index == len(self.categories) - 1 and self.progress >= self.PROGRESS_MAX:
            self.progress = self.PROGRESS_MAX
            return
            
        self.progress += self.PROGRESS_PER_KILL * kills
        while self.progress >= self.PROGRESS_MAX:
            # If at max rank, cap the progress
            if self.category_index == len(self.categories) - 1:
                self.progress = self.PROGRESS_MAX
                break
            self.progress -= self.PROGRESS_MAX
            self._change_category(1)

    def _decay_progress(self, dt: float):
        """Decrease progress bar over time; handle rank down when empty."""
        if self.category_index == 0 and self.progress <= 0:
            self.progress = 0
            return
        self.progress -= self.DECAY_RATE * dt
        if self.progress < 0:
            self._change_category(-1)
            self.progress += self.PROGRESS_MAX

    def _change_category(self, delta: int):
        """Change rank category by delta (+1 or -1) and update multiplier."""
        new_idx = max(0, min(len(self.categories) - 1, self.category_index + delta))
        if new_idx != self.category_index:
            self.category_index = new_idx
            # Simple multiplier: rank index +1 (D=1x, C=2x ...)
            self.multiplier = self.category_index + 1
            
    # ----- Background and dimension helpers -----
    def _generate_background(self):
        """Generate a background image using DALL-E based on the dimension prompt"""
        # Si DALL-E está desactivado, solo cargar fondo por defecto
        if not USE_DALLE_BG:
            background_path = self.bg_generator.load_default_background()
            if background_path:
                self.scrolling_bg = ScrollingBackground(background_path, BG_SCROLL_SPEED)
            return
            
        # Continuar con generación DALL-E si está activado
        if not self.dimension_text:
            self.dimension_text = "espacio exterior" # Default if empty
        
        print(f"Generating background for dimension: {self.dimension_text}")
        
        # Try to generate with DALL-E
        background_path = self.bg_generator.generate_background(self.dimension_text)
        
        # If generation failed, use default
        if not background_path:
            background_path = self.bg_generator.load_default_background()
            
        # Create scrolling background
        if background_path:
            self.scrolling_bg = ScrollingBackground(background_path, BG_SCROLL_SPEED)
        
        # Generar powerups temáticos basados en la dimensión
        self.powerup_generator.set_dimension(self.dimension_text)
        
    # ----- Highscore helpers -----
    def _load_highscores(self):
        """Load highscores from file or return empty list if file doesn't exist."""
        highscore_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "highscores.json")
        try:
            if os.path.exists(highscore_path):
                with open(highscore_path, "r") as f:
                    return json.load(f)
            else:
                return []
        except Exception as e:
            print(f"Error loading highscores: {e}")
            return []
    
    def _save_highscore(self):
        """Save current score with player initials to highscores file."""
        if not self.input_name or len(self.input_name) < 1:
            self.input_name = "AAA"  # Default if empty
            
        # Add new score
        self.highscores.append((self.input_name, self.score))
        
        # Sort by score (descending)
        self.highscores.sort(key=lambda x: x[1], reverse=True)
        
        # Save to file
        highscore_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "highscores.json")
        try:
            with open(highscore_path, "w") as f:
                json.dump(self.highscores, f)
        except Exception as e:
            print(f"Error saving highscores: {e}")
            
        # Reiniciar el temporizador para que no se vuelva a disparar el cambio de estado
        self.level_start = pygame.time.get_ticks() / 1000.0
