# Chess.com AI Helper

This Python application provides a graphical user interface (GUI) to interact with chess.com, extract game information, and get move suggestions from an external UCI-compliant chess engine (defaulting to Ethereal). It's designed as a tool for analysis and experimentation.

**Disclaimer:** Using this tool to cheat in rated games on chess.com or any other platform is against their terms of service and can lead to account suspension or other penalties. This project is intended for educational and personal use with computer opponents or for analyzing your own games. Please use responsibly.

## Features

*   **Browser Automation:** Opens chess.com in a browser window (defaults to Incognito).
*   **Automatic Login:** Logs into your chess.com account using credentials stored in a `.env` file.
*   **Game Scraping:**
    *   Extracts the move list from an ongoing game on chess.com.
    *   Reconstructs a virtual board based on the scraped moves.
*   **FEN Generation:** Displays the Forsyth-Edwards Notation (FEN) for the current virtual board state.
*   **Engine Integration:**
    *   Communicates with a UCI-compliant chess engine (e.g., Ethereal).
    *   Sends the current FEN to the engine to get the best move suggestion.
*   **User Interface:**
    *   Built with CustomTkinter for a modern look and feel.
    *   Separate output areas for user-facing messages and detailed debug logs.
    *   Buttons for each core functionality.

## Project Structure

```
chess_ai_helper/
├── .env                  # Stores chess.com credentials (create this yourself)
├── main.py               # Main application entry point
├── config.py             # Loads configurations and constants
├── ui.py                 # CustomTkinter GUI (ChessApp class)
├── browser_automation.py # Selenium browser interactions (BrowserManager class)
└── engine_communication.py # UCI engine interaction (ChessEngineCommunicator class)
└── Ethereal-9.00         # (or Ethereal-9.00.exe for Windows) Your engine executable
```

## Setup and Installation

### Prerequisites

*   Python 3.8 or higher
*   Google Chrome browser installed
*   A UCI-compliant chess engine (e.g., Ethereal, Stockfish). The script defaults to looking for `Ethereal-9.00` (or `Ethereal-9.00.exe` on Windows) in the project's root directory or your system PATH.

### Steps

1.  **Clone the Repository (or download files):**
    ```bash
    git clone https://github.com/WalkingDevFlag/Chess_Bot.git
    cd Chess_Bot
    ```

2.  **Create a Virtual Environment (Recommended):**
    ```bash
    python -m venv venv
    # On Windows
    venv\Scripts\activate
    # On macOS/Linux
    source venv/bin/activate
    ```

3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    (If a `requirements.txt` is not present, install manually):
    ```bash
    pip install customtkinter selenium webdriver-manager python-chess beautifulsoup4 python-dotenv
    ```

4.  **Create `.env` File:**
    In the root directory of the project (`chess_ai_helper/`), create a file named `.env` and add your chess.com credentials:
    ```env
    CHESS_USERNAME="your_chess_com_username"
    CHESS_PASSWORD="your_chess_com_password"
    ```
    Replace `"your_chess_com_username"` and `"your_chess_com_password"` with your actual login details.

5.  **Place Your Chess Engine:**
    *   Download or compile your chosen UCI chess engine.
    *   The application defaults to looking for an engine named `Ethereal-9.00`.
    *   Place the engine executable (e.g., `Ethereal-9.00` for Linux/macOS, or `Ethereal-9.00.exe` for Windows) in the root directory of the project (`chess_ai_helper/`).
    *   Alternatively, ensure the engine is in your system's PATH.
    *   You can change the `DEFAULT_ENGINE_NAME` constant in `config.py` if your engine has a different name.

## Running the Application

Navigate to the project's root directory in your terminal and run:

```bash
python main.py
```

## Usage

1.  **Open Browser:** Click this button to launch Google Chrome (Incognito by default) and navigate to chess.com.
2.  **Login:** Once the browser is open, click this to automatically log in using the credentials from your `.env` file.
3.  **Navigate to a Game:** In the browser, go to a live game, a game against a bot, or open an analysis board where a move list is displayed.
4.  **Get Virtual Board:** Click to scrape the moves from the current game and display the reconstructed board in the main output area.
5.  **Get FEN:** Click to get the FEN string of the current virtual board.
6.  **Run Bot:**
    *   This will update the internal board based on the current game.
    *   It then sends the FEN to the configured chess engine.
    *   The engine's suggested move (in SAN and UCI format) will be displayed in the main output area.
7.  **Show/Hide Debug Logs:** Click this button to toggle the visibility of a secondary textbox containing detailed logs from browser automation, engine communication, and move scraping. This is useful for troubleshooting.

## Modules Overview

*   **`main.py`**: The entry point of the application. Initializes and runs the `ChessApp`.
*   **`config.py`**: Handles loading of environment variables (like username/password) and stores application-wide constants (like engine name, window titles).
*   **`ui.py` (`ChessApp` class)**: Manages the entire CustomTkinter graphical user interface, including button actions, text outputs, and interactions between other modules.
*   **`browser_automation.py` (`BrowserManager` class)**: Encapsulates all Selenium WebDriver logic for opening the browser, logging into chess.com, and scraping game moves from the web page using BeautifulSoup.
*   **`engine_communication.py` (`ChessEngineCommunicator` class)**: Handles the low-level communication with an external UCI-compliant chess engine via subprocesses. It sends commands (like `uci`, `isready`, `position fen`, `go`) and parses the engine's output to get the best move.

## Troubleshooting

*   **`[WinError 193] %1 is not a valid Win32 application`**: This means you're trying to run a Linux-compiled engine on Windows (or vice-versa). Ensure your engine executable is compiled for your operating system.
*   **Engine Not Found**: Make sure the engine executable (e.g., `Ethereal-9.00` or `Ethereal-9.00.exe`) is in the same directory as `main.py` or in your system's PATH. Check the `DEFAULT_ENGINE_NAME` in `config.py`.
*   **Login Issues**:
    *   Double-check your credentials in the `.env` file.
    *   Chess.com might change its login page structure. If login fails, the selectors in `browser_automation.py` (specifically in the `login` method) might need updating. Use browser developer tools to inspect the element IDs.
*   **Move Scraping Fails ("No moves extracted")**:
    *   Chess.com frequently updates its website. The HTML structure of the move list might have changed.
    *   The BeautifulSoup selectors in `browser_automation.py` (specifically in `_get_moves_from_page` and `_extract_san_from_ply_div`) would need to be adjusted. Inspect the game page's HTML to find the correct elements.
    *   Ensure you are on a page where a game and its move list are visible.
*   **Debug Logs**: Use the "Show Debug Logs" button to get more detailed information about what the application is doing, which can help pinpoint issues.

## TO-DO

## Contributing

*   Add Logic for Bullet Games, Puzzles etc

Contributions are welcome! If you'd like to improve the application, feel free to fork the repository and submit a pull request. Areas for improvement could include:

*   More robust web scraping selectors.
*   UI for selecting different chess engines.
*   Automatic move execution on the board (use with extreme caution and not for cheating).
*   Enhanced error handling and user feedback.
*   Support for other chess platforms.
