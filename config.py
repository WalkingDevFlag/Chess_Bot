import os
from dotenv import dotenv_values

# Base directory of the application
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
dotenv_path = os.path.join(BASE_DIR, ".env")

# Load .env file
config_env = dotenv_values(dotenv_path)

CHESS_USERNAME: str | None = config_env.get("CHESS_USERNAME")
CHESS_PASSWORD: str | None = config_env.get("CHESS_PASSWORD")

# --- Engine Configuration ---
DEFAULT_ENGINE_NAME: str = "Ethereal-9.00"
ENGINE_PATH_LOCAL: str = os.path.join(BASE_DIR, DEFAULT_ENGINE_NAME)
ENGINE_PATH_LOCAL_EXE: str = os.path.join(BASE_DIR, f"{DEFAULT_ENGINE_NAME}.exe")

# --- UI Constants ---
WINDOW_TITLE: str = "Chess.com AI Helper"
DEFAULT_WINDOW_SIZE: str = "700x600"
DEBUG_WINDOW_SIZE: str = "700x800" # When debug logs are visible

# --- Web Scraping Selectors (example, might need adjustment) ---
# These are better kept here if they become complex or numerous
# LOGIN_USERNAME_ID: str = "login-username"
# LOGIN_PASSWORD_ID: str = "login-password"
# LOGIN_BUTTON_ID: str = "login"


if __name__ == "__main__":
    # For testing the config loading
    print(f"BASE_DIR: {BASE_DIR}")
    print(f"CHESS_USERNAME: {CHESS_USERNAME}")
    print(f"CHESS_PASSWORD: {CHESS_PASSWORD}")
    print(f"DEFAULT_ENGINE_NAME: {DEFAULT_ENGINE_NAME}")
    print(f"ENGINE_PATH_LOCAL: {ENGINE_PATH_LOCAL}")