# Chess.com AI Helper (ChessCheater HEHEHEHEHE)

This Python application provides a graphical user interface (GUI) to interact with chess.com, extract game information, get move suggestions from an external UCI-compliant chess engine (defaulting to Ethereal-9.00), and automatically play moves in fast-paced games. It's designed as a tool for analysis, experimentation, and potentially assisting with puzzles or playing against computer opponents.

**Disclaimer:** Using this tool to cheat in rated games on chess.com or any other platform is against their terms of service and can lead to account suspension or other penalties. This project is intended for educational purposes and personal use against computer opponents or for analyzing your own games. **Please use responsibly and ethically.**

## Features

*   **Browser Automation:** Opens chess.com in a browser window (defaults to Incognito mode).
*   **Automatic Login:** Securely logs into your chess.com account using credentials stored locally in a `.env` file.
*   **Real-time Game Scraping:**
    *   Extracts the move list from an ongoing game on chess.com.
    *   Reconstructs a virtual board (`python-chess` Board object) based on the scraped moves.
*   **FEN Generation:** Displays the Forsyth-Edwards Notation (FEN) for the current virtual board state.
*   **UCI Engine Integration:**
    *   Communicates with any UCI-compliant chess engine (defaults to Ethereal-9.00).
    *   Sends the current FEN to the engine and retrieves the suggested best move.
*   **Auto-Play Functionality:**
    *   Dedicated "Play Bullet" and "Play Blitz" modes.
    *   Scrapes board state, gets engine's best move, and automatically executes the move on the chess.com board using `pyautogui`.
    *   Dynamic move delays to mimic human-like play, adjusting based on game mode and (attempted) remaining clock time.
    *   Detects board orientation (White/Black at bottom) for accurate mouse control.
    *   Keyboard Failsafe: Press `ESC` (configurable) to immediately stop auto-play.
*   **User-Friendly Interface:**
    *   Built with CustomTkinter for a modern look and feel.
    *   Clear separation of user-facing messages and detailed debug logs.
    *   Buttons for: Open Browser, Login, Get Board, Get FEN, Run Bot (suggest move), Play Bullet, Play Blitz, Clear Output, Show/Hide Debug Logs.

## Getting Started

There are two ways to use this application:

**1. Running the Packaged One-Folder Release (Recommended for most users):**

This version provides a folder containing the executable and necessary files. It does not require Python to be installed (other than Google Chrome).

*   **Prerequisites:**
    *   Windows Operating System (currently packaged for Windows).
    *   Google Chrome browser installed.
*   **Installation & Usage:**
    1.  Go to the [**Releases Page**](https://github.com/WalkingDevFlag/Chess_Bot/releases) of this repository.
    2.  Download the latest `ChessCheater_HEHEHEHEHE-vX.X.X-windows-folder.zip` (or similar named ZIP for one-folder release).
    3.  Extract the ZIP file to a location on your computer. This will create a folder (e.g., `ChessCheater HEHEHEHEHE`).
    4.  Navigate into the extracted folder. You will see `ChessCheater HEHEHEHEHE.exe`, an `.env` file (or an example to rename), and the chess engine (e.g., `Ethereal-9.00.exe`).
    5.  **Crucial:** Open the `.env` file (located inside the extracted folder, next to the `.exe`) with a text editor.
    6.  Add your chess.com credentials:
        ```env
        CHESS_USERNAME="YOUR_CHESS.COM_USERNAME"
        CHESS_PASSWORD="YOUR_CHESS.COM_PASSWORD"
        ```
        Replace the placeholder text with your actual username and password. Save the file.
    7.  Run `ChessCheater HEHEHEHEHE.exe` from within this folder.
    8.  **Auto-Play Configuration:** If the default auto-play screen coordinates don't work for your setup, you'll need to run from source and modify `src/config.py` with your specific values (see "Screen and Board Configuration" below), then rebuild the application.

**2. Running from Source (For developers or to customize configurations):**

*   **Prerequisites:**
    *   Python 3.8 or higher.
    *   Google Chrome browser installed.
    *   Git (for cloning).
*   **Setup Steps:**
    1.  **Clone the Repository:**
        ```bash
        git clone https://github.com/WalkingDevFlag/Chess_Bot.git
        cd Chess_Bot
        ```
    2.  **Navigate to Source Directory:**
        ```bash
        cd src 
        ```
    3.  **Create a Virtual Environment (Recommended):**
        ```bash
        python -m venv venv
        # On Windows
        venv\Scripts\activate
        # On macOS/Linux
        source venv/bin/activate
        ```
    4.  **Install Dependencies:**
        ```bash
        pip install -r ../requirements.txt 
        ```
    5.  **Create `.env` File:**
        In the `src/` directory, create `src/.env` with your chess.com credentials:
        ```env
        CHESS_USERNAME="your_chess_com_username"
        CHESS_PASSWORD="your_chess_com_password"
        ```
    6.  **Place Your Chess Engine:**
        *   Place the engine executable (e.g., `Ethereal-9.00.exe`) in the `src/` directory.
        *   Or ensure it's in your system's PATH and update `DEFAULT_ENGINE_NAME` in `src/config.py`.
    7.  **Configure Auto-Play Coordinates (Crucial):**
        *   Edit `src/config.py`. Accurately set `BOARD_OFFSET_X`, `BOARD_OFFSET_Y`, and `SQUARE_PIXEL_SIZE` as described below.
    8.  **Run the Application:**
        From the `src/` directory:
        ```bash
        python main.py
        ```

## Screen and Board Configuration for Auto-Play

For the "Play Bullet" and "Play Blitz" auto-play features to make accurate mouse clicks, you **must** accurately configure three constants in the `src/config.py` file if you are running from source or building your own executable:

*   `BOARD_OFFSET_X`: The horizontal distance (in pixels) from the absolute left edge of your primary screen to the left edge of the chessboard element on chess.com.
*   `BOARD_OFFSET_Y`: The vertical distance (in pixels) from the absolute top edge of your primary screen to the top edge of the chessboard element on chess.com.
*   `SQUARE_PIXEL_SIZE`: The width (and height) of a single square on the chessboard in pixels.

**How to Measure These Values:**

1.  **Open a game on Chess.com.**
2.  **Set OS Display Scaling to 100%** for easiest measurement, or be aware of how scaling affects coordinates.
3.  **Measure `BOARD_OFFSET_X` and `BOARD_OFFSET_Y`:**
    *   Use a full-screen screenshot and an image editor (like GIMP, Photoshop, Paint.NET) to find the (X, Y) pixel coordinates of the top-left corner of square `a8`.
4.  **Measure `SQUARE_PIXEL_SIZE`:**
    *   In the screenshot, measure the width of a single square, or for better accuracy, the full width of the 8 squares and divide by 8.

**Examples (for a 2560x1560 screen resolution):**

*   **At 100% OS Display Scaling:**
    *   Board offset might be (X=355, Y=153). Square size might be 163px.
    *   Set in `config.py`: `BOARD_OFFSET_X = 355`, `BOARD_OFFSET_Y = 153`, `SQUARE_PIXEL_SIZE = 163`
*   **At 150% OS Display Scaling:**
    *   Board offset might be (X=312, Y=272). Square size might be 144px.
    *   Set in `config.py`: `BOARD_OFFSET_X = 312`, `BOARD_OFFSET_Y = 272`, `SQUARE_PIXEL_SIZE = 144`

**Note:** These values are highly dependent on your individual setup. **You must measure them for your own screen.** Packaged releases will use the default values from `config.py` at the time of building.

## Usage Guide

1.  **Launch:** Run `ChessCheater HEHEHEHEHE.exe` (packaged release) or `python main.py` (from source).
2.  **Open Browser & Login.**
3.  **Navigate to a Game** on chess.com.
4.  **Use "Get Board" / "Get FEN"** to check board state.
5.  **"Run Bot"** for an engine move suggestion.
6.  **"Play Bullet" / "Play Blitz" (Auto-Play):**
    *   Click when it's **your turn**. The bot will play for your color.
    *   **Failsafe:** Press `ESC` (or configured key) to stop auto-play.
7.  **Clear Output / Show/Hide Debug Logs.**

## Building From Source (Creating Your Own Executable Folder)

If you've modified the source or want to package it for local use with an editable `.env`:

*   **Prerequisites:** Python and PyInstaller installed (`pip install pyinstaller`).
*   **Setup:**
    *   Ensure `src/config.py` is correctly configured (especially board offsets if defaults don't match).
    *   Place your `src/.env` file with credentials.
    *   Place your engine (e.g., `src/Ethereal-9.00.exe`) in the `src/` directory.
    *   Icon at `src/assets/app_icon.ico`.

Run PyInstaller commands from the **root directory of the project** (`Chess_Bot/`).

**Creating a One-Folder Executable:**

This creates a folder containing your executable and all its dependencies, allowing easy modification of the `.env` file.

```bash
# For Windows (from Chess_Bot/ directory):
pyinstaller --noconsole --name "ChessCheater HEHEHEHEHE" ^
--icon="src/assets/app_icon.ico" ^
--add-data "src/.env:." ^
--add-data "src/Ethereal-9.00.exe:." ^
src/main.py

# For Linux/macOS (from Chess_Bot/ directory, adjust engine name):
# pyinstaller --noconsole --name "ChessCheater HEHEHEHEHE" \
# --icon="src/assets/app_icon.ico" \
# --add-data "src/.env:." \
# --add-data "src/Ethereal-9.00:." \
# src/main.py
```
*   `--add-data "source:destination_in_bundle"`:
    *   `src/.env:.` copies your `.env` file to the root (`.`) of the output folder.
    *   `src/Ethereal-9.00.exe:.` copies your engine to the root (`.`) of the output folder.
*   The output will be in `Chess_Bot/dist/ChessCheater HEHEHEHEHE/`. You can run the executable from this folder, and edit the `.env` file within it directly.
*   You can also use a `.spec` file for more complex configurations (generate with `pyi-makespec src/main.py` and edit).

## Project Structure (Source Code)

```
Chess_Bot/
├── src/                    # Main source code directory
│   ├── assets/
│   │   └── app_icon.ico    # Application icon
│   ├── .env                # .env file (user-created in src for development)
│   ├── auto_player.py      # Auto-play logic
│   ├── browser_automation.py # Selenium logic
│   ├── config.py           # Configurations and constants
│   ├── engine_communication.py # UCI engine logic
│   ├── keyboard_listener.py  # Keyboard failsafe logic
│   ├── main.py             # Main application entry point
│   ├── ui.py               # GUI logic (ChessApp class)
│   └── Ethereal-9.00       # Default engine (e.g., Ethereal-9.00 or Ethereal-9.00.exe)
├── .gitignore
├── LICENSE
├── README.md               # This file
└── requirements.txt        # Python dependencies
```

## Modules Overview

*   **`main.py`**: Entry point.
*   **`config.py`**: Configurations, constants, PyInstaller path resolution.
*   **`ui.py`**: GUI logic.
*   **`browser_automation.py`**: Selenium interactions.
*   **`engine_communication.py`**: UCI engine communication.
*   **`auto_player.py`**: Auto-play move execution.
*   **`keyboard_listener.py`**: Keyboard failsafe.

## TO-DO / Future Enhancements

1.  **Improving Logic for Move Delay:** Further refine move timing in auto-play modes to more closely mimic human hesitation, thought processes, and reactions to time pressure.
2.  **Stealth Improvements:** Investigate and implement strategies to make bot interaction less detectable by anti-cheating systems (for ethical use against computer opponents or analysis only). This could involve more randomized mouse paths, variable click durations, and less predictable interaction patterns.
3.  **Code Cleanup & Refactoring:** Continuously review and refactor the codebase for better readability, maintainability, and performance.

## Contributing

Contributions, bug reports, and feature requests are welcome! Please feel free to:
*   Open an issue to discuss a bug or feature.
*   Fork the repository and submit a pull request with your improvements.

When contributing, please try to follow the existing coding style and ensure your changes are well-tested.