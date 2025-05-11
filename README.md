# Chess.com AI Helper

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

**1. Running the Packaged Single-File Release (Recommended for most users):**

This version is a standalone single-file executable (`.exe`) and does not require Python or any other dependencies to be installed (other than Google Chrome). The chess engine is bundled within the executable.

*   **Prerequisites:**
    *   Windows Operating System (currently packaged for Windows).
    *   Google Chrome browser installed.
*   **Installation & Usage:**
    1.  Go to the [**Releases Page**](https://github.com/WalkingDevFlag/Chess_Bot/releases) of this repository.
    2.  Download the latest `.exe` file (e.g., `ChessAIHelper-vX.X.X.exe`).
    3.  Place the `ChessAIHelper.exe` file in a folder on your computer.
    4.  **Important:** In the same folder as `ChessAIHelper.exe`, create a new file named `.env`.
    5.  Open the `.env` file with a text editor and add your chess.com credentials:
        ```env
        CHESS_USERNAME="YOUR_CHESS.COM_USERNAME"
        CHESS_PASSWORD="YOUR_CHESS.COM_PASSWORD"
        ```
        Replace the placeholder text with your actual username and password.
    6.  Run `ChessAIHelper.exe`.
    7.  **Crucial for Auto-Play:** Configure your screen/board dimensions as described in the "Screen and Board Configuration for Auto-Play" section below by editing the `src/config.py` file *before building if you build from source*, or understand that the release build uses default values that might need source-level adjustment if they don't match your setup. (For released `.exe`, these are fixed at build time. If they don't work, you'll need to build from source with your custom values.)

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
        *(All subsequent commands for running from source should be from within the `src` directory)*
    3.  **Create a Virtual Environment (Recommended):**
        ```bash
        python -m venv venv
        # On Windows
        venv\Scripts\activate
        # On macOS/Linux
        source venv/bin/activate
        ```
    4.  **Install Dependencies:**
        The `requirements.txt` is in the root of the cloned repository.
        ```bash
        pip install -r ../requirements.txt 
        ```
    5.  **Create `.env` File:**
        In the `src/` directory, create a file named `.env` and add your chess.com credentials:
        ```env
        CHESS_USERNAME="your_chess_com_username"
        CHESS_PASSWORD="your_chess_com_password"
        ```
    6.  **Place Your Chess Engine:**
        *   The application defaults to looking for an engine named `Ethereal-9.00`.
        *   Place the engine executable (e.g., `Ethereal-9.00` for Linux/macOS, or `Ethereal-9.00.exe` for Windows) in the `src/` directory.
        *   Alternatively, ensure the engine is in your system's PATH.
        *   You can change `DEFAULT_ENGINE_NAME` in `src/config.py`.
    7.  **Configure Auto-Play Coordinates (Crucial):**
        *   Edit `src/config.py` and accurately set `BOARD_OFFSET_X`, `BOARD_OFFSET_Y`, and `SQUARE_PIXEL_SIZE` as described in the "Screen and Board Configuration for Auto-Play" section below.
    8.  **Run the Application:**
        From the `src/` directory:
        ```bash
        python main.py
        ```

## Screen and Board Configuration for Auto-Play

For the "Play Bullet" and "Play Blitz" auto-play features to work correctly, you **must** accurately configure three constants in the `src/config.py` file:

*   `BOARD_OFFSET_X`: The horizontal distance (in pixels) from the absolute left edge of your primary screen to the left edge of the chessboard element on chess.com.
*   `BOARD_OFFSET_Y`: The vertical distance (in pixels) from the absolute top edge of your primary screen to the top edge of the chessboard element on chess.com.
*   `SQUARE_PIXEL_SIZE`: The width (and height) of a single square on the chessboard in pixels.

**How to Measure These Values:**

1.  **Open a game on Chess.com** in your browser. Ensure your browser is not maximized in a way that hides window borders if you're using a tool that captures relative to the window. It's often best to have it as a normal, sizable window.
2.  **Disable OS Display Scaling (or account for it):** For the most accurate pixel measurements, it's best if your operating system's display scaling is set to 100%. If you use a different scaling (e.g., 125%, 150%), measurements can become tricky. The provided examples below account for scaling.
3.  **Measuring `BOARD_OFFSET_X` and `BOARD_OFFSET_Y`:**
    *   You need to find the pixel coordinates of the top-left corner of the actual 8x8 grid of squares.
    *   **Method 1 (Screenshot & Image Editor):** Take a full-screen screenshot. Open it in an image editor (like GIMP, Photoshop, Paint.NET, or even MS Paint). Zoom in and use the editor's tools to find the pixel coordinates (X, Y) of the very top-left corner of square a8. `X` is your `BOARD_OFFSET_X`, and `Y` is your `BOARD_OFFSET_Y`.
    *   **Method 2 (Browser Developer Tools - Approximate):** You can inspect the board element using your browser's developer tools (F12). Hover over the board or specific squares to see their dimensions and positions. This might give you dimensions relative to the viewport, which you'd then need to adjust for the browser window's own offset from the screen edge. This method is generally less direct for absolute screen coordinates.
4.  **Measuring `SQUARE_PIXEL_SIZE`:**
    *   **Method 1 (Screenshot & Image Editor):** In your screenshot, measure the width (or height) of any single square. For better accuracy, measure the full width of the 8 squares and divide by 8.
    *   **Method 2 (Browser Developer Tools):** Inspect a square element (e.g., class `square-51` for a1). The computed width/height in the developer tools should give you this value.

**Examples (for a 2560x1560 screen resolution):**

*   **At 100% OS Display Scaling:**
    *   Top-left of board might be at screen coordinates (X=355, Y=153).
    *   Each square might be 163x163 pixels.
    *   In `config.py`, you would set:
        ```python
        BOARD_OFFSET_X = 355
        BOARD_OFFSET_Y = 153
        SQUARE_PIXEL_SIZE = 163 
        ```
*   **At 150% OS Display Scaling:**
    *   Top-left of board might be at screen coordinates (X=312, Y=272).
    *   Each square might be 144x144 pixels (these are the *effective* pixels the application will use for `pyautogui`).
    *   In `config.py`, you would set:
        ```python
        BOARD_OFFSET_X = 312
        BOARD_OFFSET_Y = 272
        SQUARE_PIXEL_SIZE = 144
        ```

**Note:** These values are highly dependent on your screen resolution, browser window size and position, zoom level within the browser, and OS display scaling. The examples are illustrative. **You must measure them for your own setup.** Incorrect values will cause the auto-play mouse clicks to be inaccurate.

## Usage Guide

1.  **Launch:** Run `ChessAIHelper.exe` (packaged release) or `python main.py` from the `src` directory (from source).
2.  **Configure (if running from source):** Ensure `src/config.py` has the correct board offsets and square size for your screen if you plan to use auto-play.
3.  **Open Browser:** Launches Google Chrome and navigates to chess.com.
4.  **Login:** Automatically logs you into chess.com.
5.  **Navigate to a Game:** In the browser, start or open any game (vs. Bot, live game, or analysis board).
6.  **Get Virtual Board / Get FEN:** Use these to verify the application is correctly seeing the board state.
7.  **Run Bot (Suggest Move):** Gets an engine suggestion for the current position.
8.  **Play Bullet / Play Blitz (Auto-Play):**
    *   Click when it's **your turn** in the game.
    *   The bot will take over playing moves for your color.
    *   **Failsafe:** Press the `ESC` key (or the key defined in `FAILSAFE_KEY` in `config.py`) to immediately stop auto-play.
9.  **Clear Output / Show/Hide Debug Logs:** For managing displayed information.

## Building From Source (Creating Your Own Executable)

If you've made changes to the source code or want to create your own executable:

*   **Prerequisites:** Python and PyInstaller installed (`pip install pyinstaller`).
*   **Ensure `src/config.py` is PyInstaller-Aware:** The `config.py` in this repository should already be set up to correctly find resources (like `.env` and the engine) when bundled. It uses `sys._MEIPASS`.
*   **Prepare Files:** Make sure `src/.env` (with your credentials) and your chess engine (e.g., `src/Ethereal-9.00.exe`) are correctly placed in the `src/` directory. Your application icon should be at `src/assets/app_icon.ico`.

All PyInstaller commands should be run from the **root directory of the project** (e.g., `Chess_Bot/`).

**A. Creating a One-Folder Executable (for local use/testing):**

This creates a folder containing your executable and all its dependencies.

```bash
# For Windows (from Chess_Bot/ directory):
pyinstaller --noconsole --name "ChessAIHelper_Local" ^
--icon="src/assets/app_icon.ico" ^
--add-data "src/.env:." ^
--add-data "src/Ethereal-9.00.exe:." ^
src/main.py

# For Linux/macOS (from Chess_Bot/ directory):
# pyinstaller --noconsole --name "ChessAIHelper_Local" \
# --icon="src/assets/app_icon.ico" \
# --add-data "src/.env:." \
# --add-data "src/Ethereal-9.00:." \
# src/main.py
```
*   `--add-data "source:destination_in_bundle"`:
    *   `src/.env:.` copies your `.env` file from the `src` directory to the root (`.`) of the output folder.
    *   `src/Ethereal-9.00.exe:.` copies your engine from the `src` directory to the root (`.`) of the output folder.
*   The output will be in `Chess_Bot/dist/ChessAIHelper_Local/`. You can run the executable from there.

**B. Creating a Single-File Executable (for distribution):**

This bundles everything into a single `.exe` file.

```bash
# For Windows (from Chess_Bot/ directory):
pyinstaller --onefile --noconsole --name "ChessAIHelper" --icon="src/assets/app_icon.ico" --add-data "src/.env:." --add-binary "src/Ethereal-9.00.exe:." src/main.py

# For Linux/macOS (from Chess_Bot/ directory):
# pyinstaller --onefile --noconsole --name "ChessAIHelper" \
# --icon="src/assets/app_icon.ico" \
# --add-data "src/.env:." \
# --add-binary "src/Ethereal-9.00:." \
# src/main.py
```
*   `--add-binary` is often preferred for executables like the chess engine.
*   The output will be `Chess_Bot/dist/ChessAIHelper.exe`.
*   **Note on `chromedriver`:** For a truly portable single-file executable, you might also consider bundling `chromedriver.exe` (see PyInstaller documentation and modify `browser_automation.py` to use the bundled version). The current setup relies on `webdriver-manager` to download it if needed.

For more complex scenarios or to save these settings, you can use a `.spec` file. Generate one with `pyi-makespec --onefile --noconsole src/main.py` (from `Chess_Bot/`) and then edit the `main.spec` file to add your `datas`, `binaries`, icon, and other options. Then build with `pyinstaller main.spec`.

## Project Structure (Source Code)

```
Chess_Bot/
├── src/                    # Main source code directory
│   ├── assets/
│   │   └── app_icon.ico    # Application icon
│   ├── .env                # .env file (user-created)
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
└── requirements.txt        # Python dependencies```

## Modules Overview

*   **`main.py`**: Entry point, initializes and runs the `ChessApp`.
*   **`config.py`**: Manages loading of `.env` variables, global constants, and PyInstaller path resolution.
*   **`ui.py` (`ChessApp` class)**: Defines and controls the GUI, handling user interactions and orchestrating calls.
*   **`browser_automation.py` (`BrowserManager` class)**: Handles Selenium WebDriver operations (browser launch, login, web scraping).
*   **`engine_communication.py` (`ChessEngineCommunicator` class)**: Manages communication with the UCI chess engine.
*   **`auto_player.py` (`AutoPlayer` class)**: Implements the logic for automated move execution, including timing and `pyautogui` interactions.
*   **`keyboard_listener.py` (`KeyboardListener` class)**: Listens for a global hotkey (e.g., ESC) to provide a failsafe to stop auto-play.

## TO-DO / Future Enhancements

1.  **Improving Logic for Move Delay:** Further refine move timing in auto-play modes to more closely mimic human hesitation, thought processes, and reactions to time pressure.
2.  **Stealth Improvements:** Investigate and implement strategies to make bot interaction less detectable by anti-cheating systems (for ethical use against computer opponents or analysis only). This could involve more randomized mouse paths, variable click durations, and less predictable interaction patterns.
3.  **Code Cleanup & Refactoring:** Continuously review and refactor the codebase for better readability, maintainability, and performance.

## Contributing

Contributions, bug reports, and feature requests are welcome! Please feel free to:
*   Open an issue to discuss a bug or feature.
*   Fork the repository and submit a pull request with your improvements.

When contributing, please try to follow the existing coding style and ensure your changes are well-tested.