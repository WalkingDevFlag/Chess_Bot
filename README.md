# Chess Bot

GUI tool to interact with chess.com, get engine move suggestions (Ethereal-9.00 default), and auto-play moves for analysis and experimentation.

**Disclaimer:** Using this tool against human opponents or in rated games violates chess.com's terms of service. Use ethically and responsibly for learning, analysis, or against computer opponents only.

## Features

*   Opens chess.com (Incognito mode) & logs in automatically via `.env` file.
*   Scrapes game moves, reconstructs board state, and generates FEN.
*   Integrates with UCI chess engines (like Ethereal) for move suggestions.
*   **Auto-Play:** Plays Bullet/Blitz moves automatically using `pyautogui`.
    *   Includes dynamic "human-like" move delays.
    *   Detects board orientation (White/Black at bottom).
    *   Keyboard Failsafe (`ESC` key) to stop auto-play.
*   Modern UI (CustomTkinter) with user and debug outputs.

## Getting Started

**Option 1: Packaged Release (Recommended)**

*   **Requires:** Windows, Google Chrome.
*   **Setup:**
    1.  Download the latest `ChessCheater_HEHEHEHEHE-...-folder.zip` from [Releases](https://github.com/WalkingDevFlag/Chess_Bot/releases).
    2.  Extract the ZIP.
    3.  Navigate into the extracted folder.
    4.  Edit the `.env` file inside this folder with your chess.com username and password.
    5.  Run `ChessCheater HEHEHEHEHE.exe`.
*   **Note:** Auto-play coordinates are pre-set. If they don't match your screen, you must build from source after configuring `src/config.py`.

**Option 2: Running from Source (Developers / Custom Config)**

*   **Requires:** Python 3.8+, Chrome, Git.
*   **Setup:**
    1.  `git clone https://github.com/WalkingDevFlag/Chess_Bot.git && cd Chess_Bot`
    2.  `cd src`
    3.  *(Optional)* Create and activate virtual environment (`python -m venv venv`, then activate).
    4.  `pip install -r ../requirements.txt`
    5.  Create `src/.env` with `CHESS_USERNAME` and `CHESS_PASSWORD`.
    6.  Place engine executable (e.g., `Ethereal-9.00.exe`) in `src/`.
    7.  **Crucial:** Edit `src/config.py` to set your screen coordinates (see next section).
    8.  Run: `python main.py` (from `src/` directory).

## Screen and Board Configuration for Auto-Play

Accurate auto-play requires setting these in `src/config.py` (if running from source):

*   `BOARD_OFFSET_X`: Pixels from screen left edge to board left edge.
*   `BOARD_OFFSET_Y`: Pixels from screen top edge to board top edge.
*   `SQUARE_PIXEL_SIZE`: Pixel width/height of one board square.

**How to Measure:** Use a full-screen screenshot of a chess.com game and an image editor. Measure the pixel distance to the top-left corner of square `a8` (gives X/Y offsets) and the width of a single square. Set OS display scaling to 100% for easiest measurement.

*   **Example (2560x1560 screen @ 150% scaling):**
    *   Offset might be (X=312, Y=272). Square size might be 144px.
    *   Set: `BOARD_OFFSET_X = 312`, `BOARD_OFFSET_Y = 272`, `SQUARE_PIXEL_SIZE = 144`

**Note:** You *must* measure for your specific setup.

## Usage Guide

1.  Launch the app.
2.  Click "Open Browser", then "Login".
3.  Navigate to a game on chess.com.
4.  Use "Get Board", "Get FEN", "Run Bot" (suggests move) as needed.
5.  For **Auto-Play**: Click "Play Bullet" or "Play Blitz" when it's **your turn**.
6.  **Stop Auto-Play:** Press `ESC` or click the "Stop..." button.

## Building From Source (One-Folder Executable)

Package your modified source into a distributable folder (includes editable `.env`):

*   **Prerequisites:** Python, PyInstaller (`pip install pyinstaller`).
*   **Setup:** Ensure `src/config.py` (with your coords), `src/.env`, engine in `src/`, and icon at `src/assets/app_icon.ico` are ready.
*   **Command (from `Chess_Bot/` root directory):**

    ```bash
    # Windows:
    pyinstaller --noconsole --name "ChessCheater HEHEHEHEHE" ^
    --icon="src/assets/app_icon.ico" ^
    --add-data "src/.env:." ^
    --add-data "src/Ethereal-9.00.exe:." ^
    src/main.py

    # Linux/macOS (adjust engine name):
    # pyinstaller --noconsole --name "ChessCheater HEHEHEHEHE" \
    # --icon="src/assets/app_icon.ico" \
    # --add-data "src/.env:." \
    # --add-data "src/Ethereal-9.00:." \
    # src/main.py
    ```
*   Output is in `dist/ChessCheater HEHEHEHEHE/`. Run the `.exe` from there.

## Project Structure (Source Code)

```
Chess_Bot/
├── src/
│   ├── assets/app_icon.ico
│   ├── .env
│   ├── auto_player.py
│   ├── browser_automation.py
│   ├── config.py
│   ├── engine_communication.py
│   ├── keyboard_listener.py
│   ├── main.py
│   ├── ui.py
│   └── Ethereal-9.00(.exe) # Engine
├── .gitignore
├── LICENSE
├── README.md
└── requirements.txt
```

## Modules Overview

*   **`main.py`**: Entry point.
*   **`config.py`**: Settings, constants, PyInstaller path logic.
*   **`ui.py`**: GUI and main application logic.
*   **`browser_automation.py`**: Web interaction (Selenium).
*   **`engine_communication.py`**: UCI engine interaction.
*   **`auto_player.py`**: Auto-play logic (`pyautogui`).
*   **`keyboard_listener.py`**: Failsafe key listener (`pynput`).

## TO-DO / Future Enhancements

1.  **Advanced Stealth & Humanization:** Replace `pyautogui` with direct API calls (e.g., `ctypes`), add randomized mouse paths (Bezier curves), variable click timings, less predictable interactions. Improve move delay logic.
2.  **Robustness & UX:** Add login check, potential puzzle solver mode, investigate alternative FEN retrieval methods (JS/memory reading - *use ethically*).
3.  **Advanced AI:** Hybrid model switching between custom NN and traditional engine.
4.  **Code & UI:** Refactoring, UI updates for new features, cross-platform support.

## Contributing

Issues and Pull Requests welcome! Please fork and submit PRs following existing style.
