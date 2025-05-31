import asyncio
import sys
import pygame
from constants import WIDTH, HEIGHT
from state import Game

async def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Train vs UFOs – Jam MVP")
    game = Game(screen)
    game.level_start = pygame.time.get_ticks() / 1000.0
    running = True
    while running:
        running = game.handle_events()
        game.update()
        game.draw()
        pygame.display.flip()
        await asyncio.sleep(0)
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    asyncio.run(main())
