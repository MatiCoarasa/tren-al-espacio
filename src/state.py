import pygame
from constants import FPS, LEVEL_TIME, FIRE_DELAY
from models.player import Player
from models.ufo import UFO

class Game:
    PLAYING, SHOP = range(2)

    def __init__(self, screen):
        self.screen = screen
        self.state = Game.PLAYING
        self.clock = pygame.time.Clock()
        self.bullets = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.player = Player()
        self.all_sprites = pygame.sprite.Group(self.player)
        self.level_start = 0
        self.spawn_timer = 0.0
        self.score = 0
        self.level = 1
        self.fire_delay = FIRE_DELAY

    def _spawn_enemy(self):
        u = UFO()
        self.enemies.add(u)
        self.all_sprites.add(u)

    def handle_events(self):
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                return False
            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                return False
        return True

    def update(self):
        dt = self.clock.tick(FPS) / 1000.0
        now = pygame.time.get_ticks() / 1000.0

        if self.state == Game.PLAYING:
            self.spawn_timer += dt
            if self.spawn_timer > 1.2:
                self.spawn_timer = 0.0
                self._spawn_enemy()
            self.player.update(pygame.mouse.get_pos(), now, self.bullets)
            self.bullets.update()
            self.enemies.update()
            for bullet in pygame.sprite.groupcollide(self.bullets, self.enemies, True, True):
                self.score += 10
            if now - self.level_start >= LEVEL_TIME:
                self.state = Game.SHOP

    def draw(self):
        self.screen.fill((15, 15, 40))
        self.all_sprites.draw(self.screen)
        font = pygame.font.SysFont(None, 20)
        txt = font.render(f"SCORE: {self.score}   LVL: {self.level}", True, (255,255,255))
        self.screen.blit(txt, (10, 10))
