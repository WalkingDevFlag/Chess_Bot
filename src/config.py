import os
from dotenv import dotenv_values
import sys # Import sys

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
ENGINE_PATH_LOCAL: str = DEFAULT_ENGINE_NAME 
ENGINE_PATH_LOCAL_EXE: str = f"{DEFAULT_ENGINE_NAME}.exe"

WINDOW_TITLE: str = "Chess.com Cheater HEHEHEHEHEHEHE" 
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

if __name__ == "__main__":
    print(f"Runtime BASE_DIR: {BASE_DIR}") 
    print(f"Dotenv Path: {dotenv_path}")
    print(f"CHESS_USERNAME: {CHESS_USERNAME}")
    print(f"FAILSAFE_KEY: {FAILSAFE_KEY}")
    print(f"BOARD_OFFSET_X: {BOARD_OFFSET_X}, BOARD_OFFSET_Y: {BOARD_OFFSET_Y}")
    print(f"SQUARE_PIXEL_SIZE: {SQUARE_PIXEL_SIZE}")
    print(f"BOARD_PIXEL_SIZE (calculated): {BOARD_PIXEL_SIZE}")
    print(f"PLAYER_PERSPECTIVE_DEFAULT_FALLBACK: {PLAYER_PERSPECTIVE_DEFAULT_FALLBACK}")