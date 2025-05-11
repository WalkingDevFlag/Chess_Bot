# config.py
import os
from dotenv import dotenv_values

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
dotenv_path = os.path.join(BASE_DIR, ".env")
config_env = dotenv_values(dotenv_path)

CHESS_USERNAME: str | None = config_env.get("CHESS_USERNAME")
CHESS_PASSWORD: str | None = config_env.get("CHESS_PASSWORD")

DEFAULT_ENGINE_NAME: str = "Ethereal-9.00" # Example, user should configure
ENGINE_PATH_LOCAL: str = os.path.join(BASE_DIR, DEFAULT_ENGINE_NAME)
ENGINE_PATH_LOCAL_EXE: str = os.path.join(BASE_DIR, f"{DEFAULT_ENGINE_NAME}.exe")

WINDOW_TITLE: str = "Chess.com Cheater HEHEHEHEHEHEHE"
DEFAULT_WINDOW_SIZE: str = '450x700'#"700x650" 
DEBUG_WINDOW_SIZE: str = '450x850'#"700x850"

# --- Auto-Player Configuration ---
# Screen and board coordinates for PyAutoGUI
SCREEN_WIDTH: int = 2560  # User's screen width (reference, not directly used by core logic but good for context)
SCREEN_HEIGHT: int = 1560 # User's screen height (reference)

# Top-left corner of the CHESSBOARD (not the browser window) on screen
# These values are CRITICAL and must be accurately measured by the user.
BOARD_OFFSET_X: int = 312  # Pixels from the left edge of the screen to the board's left edge
BOARD_OFFSET_Y: int = 272  # Pixels from the top edge of the screen to the board's top edge

# The pixel size (width and height) of the playable area of the chessboard.
# If each square is 144x144 pixels, then the board is 144 * 8 = 1152 pixels.
# This value is CRITICAL for accurate mouse clicks.
SQUARE_PIXEL_SIZE: int = 144 # Pixel dimension of a single square
BOARD_PIXEL_SIZE: int = SQUARE_PIXEL_SIZE * 8 # Total pixel dimension of the 8x8 board

# Key for keyboard failsafe (uses pynput string format for special keys, e.g. 'esc', 'f12')
# Case-insensitive for letters, for special keys use pynput.keyboard.Key.xxx.name
FAILSAFE_KEY: str = "esc" # Example: Escape key

# Player's perspective for coordinate calculation.
# This is DETECTED by BrowserManager.get_board_orientation() which looks for a "flipped" state.
# It returns "white_bottom" (White's pieces/rank 1 are at the bottom of the screen for the user)
# or "black_bottom" (Black's pieces/rank 8 are at the bottom of the screen for the user, board is flipped).
# AutoPlayer uses this detected orientation to calculate mouse click coordinates correctly.
# The default value below is only used if detection fails catastrophically, which is unlikely.
PLAYER_PERSPECTIVE_DEFAULT_FALLBACK: str = "white_bottom" 

if __name__ == "__main__":
    print(f"BASE_DIR: {BASE_DIR}")
    print(f"CHESS_USERNAME: {CHESS_USERNAME}")
    print(f"FAILSAFE_KEY: {FAILSAFE_KEY}")
    print(f"BOARD_OFFSET_X: {BOARD_OFFSET_X}, BOARD_OFFSET_Y: {BOARD_OFFSET_Y}")
    print(f"SQUARE_PIXEL_SIZE: {SQUARE_PIXEL_SIZE}")
    print(f"BOARD_PIXEL_SIZE (calculated): {BOARD_PIXEL_SIZE}")
    print(f"PLAYER_PERSPECTIVE_DEFAULT_FALLBACK: {PLAYER_PERSPECTIVE_DEFAULT_FALLBACK}")