import os
from dotenv import dotenv_values
import sys 

# Determine base directory
if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    BASE_DIR = sys._MEIPASS
    dotenv_path = os.path.join(BASE_DIR, ".env")
else:
    # Running as a normal script
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    dotenv_path = os.path.join(BASE_DIR, ".env")

config_env = {}
if os.path.exists(dotenv_path):
    config_env = dotenv_values(dotenv_path)
else:
    # Fallback or error if .env is critical and not found
    print(f"Warning: .env file not found at {dotenv_path}. Credentials will be missing.")


CHESS_USERNAME: str | None = config_env.get("CHESS_USERNAME")
CHESS_PASSWORD: str | None = config_env.get("CHESS_PASSWORD")

DEFAULT_ENGINE_NAME: str = "Ethereal-9.00" 
ENGINE_PATH_LOCAL: str = f'src/{DEFAULT_ENGINE_NAME}' 
ENGINE_PATH_LOCAL_EXE: str = f"src/{DEFAULT_ENGINE_NAME}.exe"

WINDOW_TITLE: str = "Chess_Bot_v1.3.2" 
DEFAULT_WINDOW_SIZE: str = '450x700'
DEBUG_WINDOW_SIZE: str = '450x850'

SCREEN_WIDTH: int = 2560
SCREEN_HEIGHT: int = 1560
BOARD_OFFSET_X: int = 312
BOARD_OFFSET_Y: int = 272
SQUARE_PIXEL_SIZE: int = 144
BOARD_PIXEL_SIZE: int = SQUARE_PIXEL_SIZE * 8

FAILSAFE_KEY: str = "esc"
PLAYER_PERSPECTIVE_DEFAULT_FALLBACK: str = "white_bottom"

# --- Perlin Noise Configuration ---
PERLIN_ENABLED: bool = True 
PERLIN_RES_SCALE: float = 1     # Resolution scale for noise map (0.1 to 1.0). Smaller = coarser noise map, less detail but faster gen.
PERLIN_NOISE_SCALE: float = 100.0 # Scale of the noise features (e.g., 50-200)
PERLIN_SPEED_MIN: float = 20.0    # Min pixels per step (e.g., 5-50)
PERLIN_SPEED_MAX_MUL: float = 2.0 # Multiplier for noise influence on speed (e.g., 1.0-3.0)
PERLIN_JITTER_MUL: float = 35.0   # Multiplier for noise influence on jitter (e.g., 5-30)
PERLIN_DEV_DEG: float = 45.0      # Max deviation from target angle in degrees (e.g., 15-45)
PERLIN_SLEEP_INTERVAL: float = 0.008 # Sleep time between steps in seconds (e.g., 0.005 - 0.03)
PERLIN_MIN_DIST_SQ: float = 1.0 * 1.0 # Squared distance to target to stop (e.g., 0.5*0.5 to 2*2 pixels)


if __name__ == "__main__":
    print(f"Runtime BASE_DIR: {BASE_DIR}")
    print(f"Dotenv Path: {dotenv_path}")
    print(f"CHESS_USERNAME: {CHESS_USERNAME}")
    print(f"SCREEN_WIDTH: {SCREEN_WIDTH}, SCREEN_HEIGHT: {SCREEN_HEIGHT}")
    print(f"PERLIN_ENABLED: {PERLIN_ENABLED}")
    print(f"PERLIN_RES_SCALE for noise map: {PERLIN_RES_SCALE}")
    # Calculate noise map dimensions for info
    noise_map_w_calc = int(SCREEN_WIDTH * PERLIN_RES_SCALE)
    noise_map_h_calc = int(SCREEN_HEIGHT * PERLIN_RES_SCALE)
    print(f"Calculated Perlin noise map dimensions: {noise_map_w_calc}x{noise_map_h_calc}")