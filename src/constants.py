import math
from pathlib import Path


# Setup constants
ASSETS = Path(__file__).parent.parent / "assets"
WIDTH, HEIGHT = 1280, 720
FPS = 60
LEVEL_DURATION = 60  # seconds per level
BG_SCROLL_SPEED = 50  # pixels per second for background scrolling

# Feature toggles
USE_DALLE_BG = 0  # 0: No utilizar DALL-E, 1: Generar fondos con DALL-E
USE_OPENAI_API = 1  # 0: No usar OpenAI para powerups, 1: Generar powerups con OpenAI

# Powerup constants
POWERUP_DROP_CHANCE = 0.8  # Probabilidad de que un UFO deje un powerup (0-1)
POWERUP_MAX_LIFETIME = 8  # Segundos que permanece un powerup en pantalla

# Player constants
FIRE_DELAY = 0.3
BULLET_SPEED = 480
PLAYER_SPEED = 280  # pixels per second for train horizontal movement
DASH_DISTANCE = 150  # pixels per dash
DASH_COOLDOWN = 0.8  # seconds between dashes
TRAIL_SPACING = 30  # px spacing between dash ghosts

# UFOs constants
MAX_SPAWN_HEIGHT = 40  # max spawn height for UFOs
MIN_SPAWN_HEIGHT = int(HEIGHT * 0.6)  # min spawn height for UFOs
TIME_BETWEEN_SPAWNS = 1  # seconds between UFO spawns
UFO_MIN_SPEED = 120  # base speed of UFOs in pixels per second
UFO_MAX_SPEED = 240  # max speed of UFOs in pixels per second
MIN_SIZE = 20  # min size of UFOs in pixels
MAX_SIZE = 40  # max size of UFOs in pixels

OA_API_KEY = ""
