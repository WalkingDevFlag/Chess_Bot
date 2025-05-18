import ctypes
import ctypes.wintypes # For POINT structure
import time
import random
from typing import Tuple, Callable, Optional, Dict, Any
import numpy as np # Required if GLOBAL_NOISE_MAP is here

# Import from the new helpers module
from perlin_noise_helpers import perform_perlin_move
from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, # Needed for perform_perlin_move
    PERLIN_ENABLED # To easily toggle Perlin movement
)


# ctypes constants for mouse events
MOUSEEVENTF_MOVE = 0x0001       # Not used by Perlin move directly, but good to keep
MOUSEEVENTF_ABSOLUTE = 0x8000   # Not used by Perlin move directly
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004

class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

# --- Module-level globals for Perlin Noise ---
# These will be initialized by ui.py at startup
GLOBAL_PERLIN_NOISE_MAP: Optional[np.ndarray] = None
PERLIN_CONFIGS: Optional[Dict[str, Any]] = None
GLOBAL_LOGGER: Optional[Callable[[str, str], None]] = None


def init_perlin_globals(noise_map: np.ndarray, configs: Dict[str, Any], logger: Callable[[str, str], None]):
    """Initializes global variables for Perlin noise movement."""
    global GLOBAL_PERLIN_NOISE_MAP, PERLIN_CONFIGS, GLOBAL_LOGGER
    GLOBAL_PERLIN_NOISE_MAP = noise_map
    PERLIN_CONFIGS = configs
    GLOBAL_LOGGER = logger
    if GLOBAL_LOGGER:
        GLOBAL_LOGGER("Perlin globals initialized in input_automation.", "debug")

def _set_cursor_pos_ctypes(x: int, y: int):
    """Sets the cursor position using ctypes."""
    ctypes.windll.user32.SetCursorPos(x, y)

def _get_cursor_pos_ctypes() -> Tuple[int, int]:
    """Gets the current cursor position using ctypes."""
    pt = POINT()
    ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
    return pt.x, pt.y

def _mouse_click_ctypes():
    """Simulates a mouse left-click using ctypes."""
    ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    time.sleep(random.uniform(0.03, 0.07))
    ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)


def move_mouse_to_target(target_x: int, target_y: int):
    """
    Moves the mouse to the target coordinates.
    Uses Perlin noise if enabled and initialized, otherwise moves directly.
    """
    if not GLOBAL_LOGGER: # Should always be initialized
        print("ERROR: Global logger not initialized in input_automation!")
        _set_cursor_pos_ctypes(target_x, target_y) # Fallback to direct move
        return

    if PERLIN_ENABLED and GLOBAL_PERLIN_NOISE_MAP is not None and PERLIN_CONFIGS is not None:
        start_x, start_y = _get_cursor_pos_ctypes()
        GLOBAL_LOGGER(f"Perlin move from ({start_x},{start_y}) to ({target_x},{target_y})", "debug")
        try:
            perform_perlin_move(
                start_pos=(start_x, start_y),
                end_pos=(target_x, target_y),
                noise_map=GLOBAL_PERLIN_NOISE_MAP,
                screen_width=SCREEN_WIDTH, # Conceptual screen width for noise mapping
                screen_height=SCREEN_HEIGHT, # Conceptual screen height for noise mapping
                perlin_cfg=PERLIN_CONFIGS,
                set_cursor_func=_set_cursor_pos_ctypes,
                logger=GLOBAL_LOGGER
            )
        except Exception as e:
            GLOBAL_LOGGER(f"Error during Perlin move: {e}. Falling back to direct move.", "user")
            _set_cursor_pos_ctypes(target_x, target_y) # Fallback
    else:
        if not PERLIN_ENABLED:
            GLOBAL_LOGGER(f"Perlin movement disabled. Direct move to ({target_x},{target_y})", "debug")
        else:
            GLOBAL_LOGGER("Perlin noise map/config not ready. Direct move.", "debug")
        _set_cursor_pos_ctypes(target_x, target_y)


# Public interface for AutoPlayer (replaces the old make_move_on_screen in this file)
def perform_mouse_action_at(x: int, y: int, action: str = "move_and_click"):
    """
    Moves mouse to (x,y) and optionally clicks.
    Uses Perlin movement if enabled.
    Args:
        x: Target x-coordinate.
        y: Target y-coordinate.
        action: "move_only" or "move_and_click".
    """
    move_mouse_to_target(x, y) # This now handles Perlin or direct based on globals
    
    if action == "move_and_click":
        time.sleep(random.uniform(0.03, 0.08)) # Small pause after move, before click
        _mouse_click_ctypes()