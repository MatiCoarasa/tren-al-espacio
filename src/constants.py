import math
from pathlib import Path


# Setup constants
ASSETS = Path(__file__).parent.parent / "assets"
WIDTH, HEIGHT = 1280, 720
FPS = 60

# Gameplay constants
LEVEL_TIME = 30

# Player constants
FIRE_DELAY = 0.35
BULLET_SPEED = 480
PLAYER_SPEED = 280  # pixels per second for train horizontal movement
DASH_DISTANCE = 150  # pixels per dash
DASH_COOLDOWN = 0.8  # seconds between dashes
TRAIL_SPACING = 30  # px spacing between dash ghosts

# UFOs constants
MAX_SPAWN_HEIGHT = 40  # max spawn height for UFOs
MIN_SPAWN_HEIGHT = int(HEIGHT * 0.6)  # min spawn height for UFOs
TIME_BETWEEN_SPAWNS = 0.2  # seconds between UFO spawns
UFO_MIN_SPEED = 120  # base speed of UFOs in pixels per second
UFO_MAX_SPEED = 240  # max speed of UFOs in pixels per second