import ctypes
import ctypes.wintypes # For POINT structure
import time
import random
from typing import Tuple, Callable

# ctypes constants for mouse events
MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_ABSOLUTE = 0x8000
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004

class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

def _set_cursor_pos(x: int, y: int):
    """Sets the cursor position using ctypes."""
    ctypes.windll.user32.SetCursorPos(x, y)

def _mouse_click():
    """Simulates a mouse left-click using ctypes."""
    ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    time.sleep(random.uniform(0.03, 0.07)) # Short delay between down and up
    ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)

def make_move_on_screen(from_sq_coord: Tuple[int, int], to_sq_coord: Tuple[int, int], logger: Callable[[str, str], None]):
    """
    Simulates making a chess move on the screen by moving the mouse and clicking.
    """
    try:
        # Move to the start square and click
        _set_cursor_pos(from_sq_coord[0], from_sq_coord[1])
        time.sleep(random.uniform(0.05, 0.15)) # Simulates pyautogui.moveTo duration
        _mouse_click()

        time.sleep(random.uniform(0.05, 0.1)) # Pause between clicks

        # Move to the end square and click
        _set_cursor_pos(to_sq_coord[0], to_sq_coord[1])
        time.sleep(random.uniform(0.05, 0.15)) # Simulates pyautogui.moveTo duration
        _mouse_click()

    except Exception as e: # pylint: disable=broad-except
        logger(f"ctypes mouse control error making move: {e}", "user")