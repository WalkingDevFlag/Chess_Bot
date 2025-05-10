# Chess.com AI Helper

This Python application provides a graphical user interface (GUI) to interact with chess.com, extract game information, and get move suggestions from an external UCI-compliant chess engine (defaulting to Ethereal-9.00). It's designed as a tool for analysis, experimentation, and potentially assisting with puzzles or fast-paced games against computer opponents.

**Disclaimer:** Using this tool to cheat in rated games on chess.com or any other platform is against their terms of service and can lead to account suspension or other penalties. This project is intended for educational purposes and personal use against computer opponents or for analyzing your own games. **Please use responsibly and ethically.**

## Features

*   **Browser Automation:** Opens chess.com in a browser window (defaults to Incognito mode for privacy).
*   **Automatic Login:** Securely logs into your chess.com account using credentials stored locally in a `.env` file.
*   **Real-time Game Scraping:**
    *   Extracts the move list from an ongoing game on chess.com.
    *   Reconstructs a virtual board (`python-chess` Board object) based on the scraped moves.
*   **FEN Generation:** Displays the Forsyth-Edwards Notation (FEN) for the current virtual board state.
*   **UCI Engine Integration:**
    *   Communicates with any UCI-compliant chess engine (defaults to Ethereal-9.00).
    *   Sends the current FEN to the engine and retrieves the suggested best move.
*   **User-Friendly Interface:**
    *   Built with CustomTkinter for a modern and responsive look and feel.
    *   Clear separation of user-facing messages and detailed debug logs.
    *   Dedicated buttons for each core functionality: Open Browser, Login, Get Board, Get FEN, Run Bot, Clear Output, Show/Hide Debug Logs.

## Getting Started

There are two ways to use this application:

**1. Running the Packaged Release (Recommended for most users):**

This version is a standalone executable and does not require Python or any dependencies to be installed (other than Google Chrome).

*   **Prerequisites:**
    *   Windows Operating System (currently packaged for Windows).
    *   Google Chrome browser installed.
*   **Installation & Usage:**
    1.  Go to the [**Releases Page**](https://github.com/WalkingDevFlag/Chess_Bot/releases) of this repository.
    2.  Download the latest `.zip` file (e.g., `ChessAIHelper-vX.X.X-windows.zip`).
    3.  Extract the ZIP file to a folder on your computer.
    4.  **Important:** Inside the extracted `ChessAIHelper` folder (the one containing `ChessAIHelper.exe`), create a new file named `.env`.
    5.  Open the `.env` file with a text editor and add your chess.com credentials. You can copy the structure from the included `.env.example` file:
        ```env
        CHESS_USERNAME="YOUR_CHESS.COM_USERNAME"
        CHESS_PASSWORD="YOUR_CHESS.COM_PASSWORD"
        ```
        Replace the placeholder text with your actual username and password.
    6.  Run `ChessAIHelper.exe`.

**2. Running from Source (For developers or advanced users):**

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
        The `requirements.txt` should be in the root of the cloned repository, not directly in `src`. If you are in `src`, you might need to refer to it as `../requirements.txt`.
        ```bash
        pip install -r ../requirements.txt 
        ```
        (If `requirements.txt` is missing, install manually from `src`):
        ```bash
        pip install customtkinter selenium webdriver-manager python-chess beautifulsoup4 python-dotenv
        ```
    5.  **Create `.env` File:**
        In the `src/` directory, create a file named `.env` (or copy and rename `src/.env.example`) and add your chess.com credentials:
        ```env
        CHESS_USERNAME="your_chess_com_username"
        CHESS_PASSWORD="your_chess_com_password"
        ```
    6.  **Place Your Chess Engine:**
        *   The application defaults to looking for an engine named `Ethereal-9.00`.
        *   Place the engine executable (e.g., `Ethereal-9.00` for Linux/macOS, or `Ethereal-9.00.exe` for Windows) in the `src/` directory.
        *   Alternatively, ensure the engine is in your system's PATH.
        *   You can change the `DEFAULT_ENGINE_NAME` constant in `src/config.py` if your engine has a different name or path.
    7.  **Run the Application:**
        From the `src/` directory:
        ```bash
        python main.py
        ```

## Usage Guide

1.  **Open Browser:** Launches Google Chrome (in Incognito mode) and navigates to chess.com.
2.  **Login:** Automatically logs you into chess.com using the credentials from your `.env` file.
3.  **Navigate to a Game:** In the browser, start or open any game (vs. Bot, online, or analysis board) where the move list is visible.
4.  **Get Virtual Board:** Scrapes the moves from the active game on chess.com and displays the current board state in the application.
5.  **Get FEN:** Displays the FEN string for the current board state shown in the application.
6.  **Run Bot:**
    *   Updates the internal board representation.
    *   Sends the current FEN to your configured UCI chess engine (Ethereal-9.00 by default).
    *   Displays the engine's suggested best move.
7.  **Clear Output:** Clears the main output and debug log text areas.
8.  **Show/Hide Debug Logs:** Toggles a secondary text area showing detailed operational logs, useful for troubleshooting.

## Project Structure (Source Code)

```
Chess_Bot/
├── src/                    # Main source code directory
│   ├── assets/
│   │   └── app_icon.ico    # Application icon
│   ├── .env                # .env file
│   ├── main.py             # Main application entry point
│   ├── config.py           # Configurations and constants
│   ├── ui.py               # GUI logic (ChessApp class)
│   ├── browser_automation.py # Selenium logic (BrowserManager class)
│   ├── engine_communication.py # UCI engine logic (ChessEngineCommunicator class)
│   └── Ethereal-9.00       # Default engine (or Ethereal-9.00.exe)
├── .gitignore
├── LICENSE
├── README.md               # This file
└── requirements.txt        # Python dependencies
```

## Modules Overview

*   **`main.py`**: Entry point, initializes and runs the `ChessApp`.
*   **`config.py`**: Manages loading of `.env` variables and global constants.
*   **`ui.py` (`ChessApp` class)**: Defines and controls the CustomTkinter GUI, handling user interactions and orchestrating calls to other modules.
*   **`browser_automation.py` (`BrowserManager` class)**: Handles all Selenium WebDriver operations: browser launch, login, and web page scraping for moves using BeautifulSoup.
*   **`engine_communication.py` (`ChessEngineCommunicator` class)**: Manages communication with the UCI chess engine via subprocesses, sending commands and parsing responses.

## Troubleshooting Common Issues

*   **`[WinError 193] %1 is not a valid Win32 application`**: You are likely trying to run a Linux-compiled engine on Windows (or vice-versa). Ensure your engine executable is compatible with your OS. For Windows, you need an `.exe` version of Ethereal.
*   **Engine Not Found**:
    *   If running from source: Place the engine executable (e.g., `Ethereal-9.00` or `Ethereal-9.00.exe`) in the `src/` directory, or ensure it's in your system's PATH.
    *   If running the packaged release: The engine should be bundled with the `.exe` in the extracted folder.
    *   Verify `DEFAULT_ENGINE_NAME` in `src/config.py` matches your engine's filename.
*   **Login Issues**:
    *   Confirm credentials in your `.env` file are correct.
    *   Chess.com login page structure can change. If login fails repeatedly, HTML element IDs/selectors in `src/browser_automation.py` might need updating.
*   **Move Scraping Fails ("No moves extracted")**:
    *   The HTML structure of chess.com's move list can change. Selectors in `src/browser_automation.py` (methods `_get_moves_from_page` and `_extract_san_from_ply_div`) might require updates. Use browser developer tools to inspect the live HTML.
    *   Make sure a game with a visible move list is active in the browser tab being controlled.
*   **Debug Logs**: The "Show Debug Logs" button is your best friend for diagnosing issues. It provides detailed insight into the app's operations.

## TO-DO / Future Enhancements

*   Implement more sophisticated logic for different game phases (e.g., bullet games, puzzles).
*   For Bullet Games, will be adding auto move maker with a random time from 0.1 to 5 sec based on how much time is left.
*   Option for automatic move execution on the chess.com board.
*   More robust error handling and user feedback mechanisms.
*   Cross-platform packaging (e.g., for macOS, Linux).

## Contributing

Contributions, bug reports, and feature requests are welcome! Please feel free to:
*   Open an issue to discuss a bug or feature.
*   Fork the repository and submit a pull request with your improvements.

When contributing, please try to follow the existing coding style and ensure your changes are well-tested.
