import customtkinter as ctk
from tkinter import messagebox
import chess
import time
import re
import os
import shutil
from typing import Optional, List, Callable
import threading

from config import (
    CHESS_USERNAME, CHESS_PASSWORD, DEFAULT_ENGINE_NAME,
    WINDOW_TITLE, DEFAULT_WINDOW_SIZE, DEBUG_WINDOW_SIZE,
    ENGINE_PATH_LOCAL, ENGINE_PATH_LOCAL_EXE, BASE_DIR,
    FAILSAFE_KEY
)
from browser_automation import BrowserManager # Remains the same
from engine_communication import ChessEngineCommunicator # Remains the same
from auto_player import AutoPlayer # Remains the same
from keyboard_listener import KeyboardListener # Remains the same

# No new direct imports needed here from chess_utils or input_automation
# as those are used internally by AutoPlayer and BrowserManager.

class ChessApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(WINDOW_TITLE)
        self.geometry(DEFAULT_WINDOW_SIZE)
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.internal_board: chess.Board = chess.Board()
        self.browser_manager: BrowserManager = BrowserManager(self.add_to_output)
        self.engine_communicator: Optional[ChessEngineCommunicator] = None
        self.auto_player_instance: Optional[AutoPlayer] = None
        self.auto_play_thread: Optional[threading.Thread] = None
        self.bot_color_for_auto_play: Optional[chess.Color] = None
        self.keyboard_listener_instance: Optional[KeyboardListener] = None

        self._setup_ui()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def _setup_ui(self) -> None:
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(pady=10, padx=10, fill="both", expand=True)
        button_frame = ctk.CTkFrame(self.main_frame)
        button_frame.pack(pady=5, padx=5, fill="x")

        self.btn_open_browser = ctk.CTkButton(button_frame, text="Open Browser", command=self._open_browser_command_handler)
        self.btn_open_browser.pack(pady=5, padx=5, fill="x")
        self.btn_login = ctk.CTkButton(button_frame, text="Login", command=self._login_command_handler, state="disabled")
        self.btn_login.pack(pady=5, padx=5, fill="x")
        self.btn_get_board = ctk.CTkButton(button_frame, text="Get Virtual Board", command=self._get_board_command_handler, state="disabled")
        self.btn_get_board.pack(pady=5, padx=5, fill="x")
        self.btn_get_fen = ctk.CTkButton(button_frame, text="Get FEN", command=self._get_fen_command_handler, state="disabled")
        self.btn_get_fen.pack(pady=5, padx=5, fill="x")
        self.btn_run_bot = ctk.CTkButton(button_frame, text=f"Run Bot ({DEFAULT_ENGINE_NAME})", command=self._run_bot_command_handler, state="disabled")
        self.btn_run_bot.pack(pady=5, padx=5, fill="x")

        auto_play_mode_frame = ctk.CTkFrame(button_frame)
        auto_play_mode_frame.pack(pady=5, padx=0, fill="x", expand=True)
        self.btn_bullet_bot = ctk.CTkButton(auto_play_mode_frame, text="Play Bullet", command=lambda: self._toggle_auto_play_mode_handler("bullet"), state="disabled")
        self.btn_bullet_bot.pack(side="left", pady=0, padx=(0,2.5), fill="x", expand=True)
        self.btn_blitz_bot = ctk.CTkButton(auto_play_mode_frame, text="Play Blitz", command=lambda: self._toggle_auto_play_mode_handler("blitz"), state="disabled")
        self.btn_blitz_bot.pack(side="right", pady=0, padx=(2.5,0), fill="x", expand=True)

        self.btn_clear_chat = ctk.CTkButton(button_frame, text="Clear Output", command=self._clear_output_command_handler)
        self.btn_clear_chat.pack(pady=5, padx=5, fill="x")

        output_frame = ctk.CTkFrame(self.main_frame)
        output_frame.pack(pady=5, padx=5, fill="both", expand=True)
        self.output_textbox = ctk.CTkTextbox(output_frame, wrap="word", state="disabled", height=150)
        self.output_textbox.pack(fill="both", expand=True, padx=5, pady=5)

        self.btn_toggle_debug_logs = ctk.CTkButton(self.main_frame, text="Show Debug Logs", command=self._toggle_debug_logs_command_handler, height=28)
        self.btn_toggle_debug_logs.pack(pady=(5,0), padx=5, fill="x")
        self.debug_logs_visible: bool = False
        self.debug_log_textbox_frame = ctk.CTkFrame(self.main_frame) # Created but not packed initially
        self.debug_log_textbox = ctk.CTkTextbox(self.debug_log_textbox_frame, wrap="word", state="disabled", height=150)
        self.debug_log_textbox.pack(fill="both", expand=True, padx=5, pady=5)


    def _toggle_debug_logs_command_handler(self) -> None:
        if self.debug_logs_visible:
            self.debug_log_textbox_frame.pack_forget()
            self.btn_toggle_debug_logs.configure(text="Show Debug Logs")
            self.geometry(DEFAULT_WINDOW_SIZE) # Revert to default size
        else:
            self.debug_log_textbox_frame.pack(pady=5, padx=5, fill="both", expand=True, before=self.btn_toggle_debug_logs) # Pack it before the button
            self.btn_toggle_debug_logs.configure(text="Hide Debug Logs")
            self.geometry(DEBUG_WINDOW_SIZE) # Expand to debug size
        self.debug_logs_visible = not self.debug_logs_visible

    def add_to_output(self, message: str, log_type: str = "user") -> None:
        # Ensure this method is thread-safe if called from non-main threads (which it is)
        formatted_message = f"{message}\n"
        target_textbox = self.output_textbox if log_type == "user" else self.debug_log_textbox

        def _update_textbox():
            target_textbox.configure(state="normal")
            target_textbox.insert("end", formatted_message)
            target_textbox.see("end")
            target_textbox.configure(state="disabled")

        if threading.current_thread() is threading.main_thread():
            _update_textbox()
        else:
            self.after(0, _update_textbox) # Schedule the update on the main thread
        self.update_idletasks() # Process pending idle tasks to ensure UI updates promptly


    def _clear_output_command_handler(self) -> None:
        for tb in [self.output_textbox, self.debug_log_textbox]:
            tb.configure(state="normal"); tb.delete("1.0", "end"); tb.configure(state="disabled")
        self.add_to_output("Output cleared.", log_type="user")

    def on_closing(self) -> None:
        self.add_to_output("Closing application...", log_type="debug")
        self._stop_auto_play_components(log_message=False) # Stop auto-play without verbose logging during shutdown
        if self.engine_communicator:
            self.engine_communicator.stop_engine()
        if self.browser_manager:
            self.browser_manager.quit_browser()
        self.destroy()

    def _ensure_engine_ready(self) -> bool:
        if not self.browser_manager.driver: # Basic check: browser must be open to imply a game context
            self.add_to_output("Browser not open. Engine not checked.", "user"); return False

        final_engine_path = None
        # Check bundled paths first (PyInstaller aware via config.py logic for BASE_DIR)
        if os.path.exists(ENGINE_PATH_LOCAL):
            final_engine_path = ENGINE_PATH_LOCAL
        elif os.name == 'nt' and os.path.exists(ENGINE_PATH_LOCAL_EXE):
            final_engine_path = ENGINE_PATH_LOCAL_EXE
        else:
            # Fallback to system PATH if not found in bundled locations
            self.add_to_output(f"Engine not found at primary bundled paths. Checking system PATH for '{DEFAULT_ENGINE_NAME}'...", "debug")
            path_from_shutil = shutil.which(DEFAULT_ENGINE_NAME) or \
                               (os.name == 'nt' and shutil.which(f"{DEFAULT_ENGINE_NAME}.exe"))
            if path_from_shutil:
                final_engine_path = path_from_shutil
                self.add_to_output(f"Warning: Using engine from system PATH: {final_engine_path}. Bundled engine preferred.", "user")

        if not final_engine_path:
            err_msg = f"Engine '{DEFAULT_ENGINE_NAME}' not found in expected locations or system PATH. Please ensure it's correctly placed or installed."
            self.add_to_output(err_msg, "user"); messagebox.showerror("Engine Not Found", err_msg); return False

        self.add_to_output(f"Attempting to use engine: {final_engine_path}", "debug")

        # Check if current engine instance is valid, running, and matches the determined path
        if self.engine_communicator is None or \
           not self.engine_communicator.engine_process or \
           self.engine_communicator.engine_process.poll() is not None or \
           self.engine_communicator.engine_path != final_engine_path: # Path check is important if it could change
            try:
                if self.engine_communicator: self.engine_communicator.stop_engine() # Stop old instance if any
                self.add_to_output(f"Initializing {DEFAULT_ENGINE_NAME} from {final_engine_path}...", "debug")
                self.engine_communicator = ChessEngineCommunicator(final_engine_path, self.add_to_output)
            except Exception as e: # pylint: disable=broad-except
                self.add_to_output(f"Failed to initialize {DEFAULT_ENGINE_NAME}: {e}", "user")
                messagebox.showerror("Engine Error", f"Failed to initialize {DEFAULT_ENGINE_NAME}: {e}")
                self.engine_communicator = None; return False # Clear invalid communicator

        # Final check on the (potentially new) engine communicator
        return bool(self.engine_communicator and self.engine_communicator.engine_process and \
               self.engine_communicator.engine_process.poll() is None)


    def _open_browser_command_handler(self) -> None:
        if self.browser_manager.open_browser():
            # Enable buttons that depend on the browser being open
            for btn in [self.btn_login, self.btn_get_board, self.btn_get_fen, self.btn_run_bot, self.btn_bullet_bot, self.btn_blitz_bot]:
                btn.configure(state="normal")
        else:
            messagebox.showerror("Browser Error", "Could not open or focus the browser. Check browser installation and ChromeDriver.")


    def _login_command_handler(self) -> None:
        if not CHESS_USERNAME or not CHESS_PASSWORD:
            self.add_to_output("Username/Password not set in .env file.", "user")
            env_path_info = os.path.join(BASE_DIR, ".env")
            messagebox.showerror("Config Error", f"Chess username/password not set in .env (expected at {env_path_info}).")
            return
        if not self.browser_manager.login(CHESS_USERNAME, CHESS_PASSWORD):
            # browser_manager.login already logs details
            messagebox.showwarning("Login Failed", "Login failed. Check credentials, website status, or selectors in browser_automation.py if the site structure changed.")


    def _update_internal_board_state(self) -> bool:
        self.internal_board.reset() # Reset to starting position before applying moves
        scraped_moves = self.browser_manager.get_scraped_moves()

        if not scraped_moves:
            self.add_to_output("No moves scraped from the website. Board reset to initial position.", "debug")
            return True # Successfully reset to an empty board

        parsed_count = 0
        for i, move_san_original in enumerate(scraped_moves):
            try:
                # Basic cleaning: remove move numbers like "1.", "1...", etc.
                move_san_cleaned = re.sub(r"^\d+\.*\s*", "", move_san_original).strip()
                if not move_san_cleaned: continue # Skip if empty after cleaning

                self.internal_board.push_san(move_san_cleaned)
                parsed_count += 1
            except Exception as e: # pylint: disable=broad-except
                self.add_to_output(f"Error parsing SAN move '{move_san_original}' (move #{i+1}): {e}. Board state might be incomplete.", "debug")
                # Decide if you want to stop on first error or try to parse as much as possible.
                # For now, it continues, which might lead to a partially correct board.
                # return False # Option: stop and report failure on first parsing error

        if parsed_count == len(scraped_moves) and parsed_count > 0 :
            self.add_to_output(f"Internal board updated successfully: {parsed_count} moves. Current FEN: {self.internal_board.fen()}", "debug")
            return True
        elif parsed_count > 0: # Some moves parsed, but not all
            self.add_to_output(f"Internal board partially updated: {parsed_count}/{len(scraped_moves)} moves parsed. Current FEN: {self.internal_board.fen()}", "debug")
            return True # Still return True as we have a partial (best-effort) board state
        else: # No moves parsed at all from the scraped list
            self.add_to_output("All scraped moves failed to parse. Board state remains initial but scraping was attempted.", "user")
            return False


    def _get_board_command_handler(self) -> None:
        if self._update_internal_board_state():
            if not self.internal_board.move_stack: # No moves made yet
                self.add_to_output("Board is in the initial state (no moves played or scraped).", "user")
            self.add_to_output("--- Virtual Board ---\n" + str(self.internal_board) + "\n-------------------", "user")
        else:
            self.add_to_output("Could not display board: Failed to update internal board state from website.", "user")


    def _get_fen_command_handler(self) -> None:
        if self._update_internal_board_state():
            if not self.internal_board.move_stack:
                self.add_to_output("Board is in the initial state (no moves played or scraped).", "user")
            self.add_to_output(f"Current FEN: {self.internal_board.fen()}", "user")
        else:
            self.add_to_output("Could not get FEN: Failed to update internal board state from website.", "user")


    def _run_bot_command_handler(self) -> None:
        self.add_to_output(f"Requesting single move suggestion from {DEFAULT_ENGINE_NAME}...", "user")
        if not self._ensure_engine_ready():
            self.add_to_output("Engine not ready. Cannot suggest move.", "user"); return

        board_updated = self._update_internal_board_state()
        if not board_updated and self.internal_board.move_stack: # If update failed but there were moves before
            self.add_to_output("Board update from website failed (parsing error). Cannot reliably suggest move.", "user"); return
        # If board_updated is False but move_stack is empty, it means it's initial state, which is fine.

        if self.internal_board.is_game_over():
            self.add_to_output(f"Game is over: {self.internal_board.result()}. No move to suggest.", "user"); return

        current_fen = self.internal_board.fen()
        self.add_to_output(f"FEN for engine analysis: {current_fen}", "debug")

        if self.engine_communicator and self.engine_communicator.engine_process and \
           self.engine_communicator.engine_process.poll() is None:
            try:
                # Dynamic movetime: more ply -> slightly more time, capped
                movetime_ms = min(max(self.internal_board.ply() * 70 + 1000, 500), 5000) # e.g., 0.5s to 5s
                self.add_to_output(f"Engine thinking for approximately {movetime_ms/1000:.1f}s...", "debug")
                best_move_uci = self.engine_communicator.get_best_move(current_fen, movetime_ms=movetime_ms)

                if best_move_uci and best_move_uci != "(none)":
                    try:
                        move_obj = self.internal_board.parse_uci(best_move_uci)
                        self.add_to_output(f"Engine Suggests: {self.internal_board.san(move_obj)} (UCI: {best_move_uci})", "user")
                    except ValueError: # Should not happen if engine is UCI compliant and board state is correct
                         self.add_to_output(f"Engine suggested an illegal move (UCI): {best_move_uci}. This might indicate a desync or engine issue.", "user")
                    except Exception as e: # pylint: disable=broad-except
                        self.add_to_output(f"Engine Suggested (UCI): {best_move_uci} (Error converting to SAN: {e})", "user")
                elif best_move_uci == "(none)": # (none) can mean stalemate/checkmate or no legal moves
                    self.add_to_output(f"{DEFAULT_ENGINE_NAME} returned (none). Game might be over or no legal moves available.", "user")
                else: # Timeout or other issue from engine
                    self.add_to_output(f"{DEFAULT_ENGINE_NAME} did not return a valid move (received: {best_move_uci}). Check engine logs.", "user")
            except Exception as e: # pylint: disable=broad-except
                self.add_to_output(f"Error communicating with {DEFAULT_ENGINE_NAME}: {e}", "user")
                messagebox.showerror("Engine Communication Error", f"Error: {e}")
        else:
            self.add_to_output(f"{DEFAULT_ENGINE_NAME} is not running or failed to initialize. Cannot suggest move.", "user")


    def _get_player_clock_time_stub(self, color_to_check: chess.Color) -> Optional[float]:
        """Passes through to the browser manager's clock time retrieval."""
        return self.browser_manager.get_player_clock_time(color_to_check)

    def _handle_auto_play_stop_request(self):
        """Called by keyboard listener or stop button to halt auto-play."""
        if self.auto_player_instance and self.auto_player_instance.is_playing:
            self.add_to_output(f"Auto-play stop requested (e.g., via '{FAILSAFE_KEY.upper()}' key or button press).", "user")
            self._stop_auto_play_components() # This will also update UI

    def _stop_auto_play_components(self, log_message: bool = True):
        """Stops all components related to auto-play and ensures thread cleanup."""
        if self.keyboard_listener_instance:
            if log_message: self.add_to_output("Stopping keyboard listener...", "debug")
            self.keyboard_listener_instance.stop()
            self.keyboard_listener_instance = None # Allow garbage collection

        if self.auto_player_instance and self.auto_player_instance.is_playing:
            if log_message: self.add_to_output(f"Stopping auto-play mode: {self.auto_player_instance.game_mode}...", "user")
            self.auto_player_instance.stop_playing() # Signal the auto_player loop to terminate

            if self.auto_play_thread and self.auto_play_thread.is_alive():
                if log_message: self.add_to_output("Waiting for auto-play thread to complete...", "debug")
                self.auto_play_thread.join(timeout=2.0) # Wait for thread to finish
                if self.auto_play_thread.is_alive(): # If still alive after timeout
                     if log_message: self.add_to_output("Auto-play thread did not terminate gracefully.", "debug")
        self.auto_player_instance = None # Allow garbage collection
        self.auto_play_thread = None

        # Ensure UI update happens on the main thread
        self.after(0, self.update_auto_play_ui_on_stop)


    def _toggle_auto_play_mode_handler(self, mode: str) -> None:
        if self.auto_player_instance and self.auto_player_instance.is_playing:
            # If already playing, this button acts as a stop button
            self._stop_auto_play_components()
            # UI update is handled by _stop_auto_play_components via update_auto_play_ui_on_stop
            return

        self.add_to_output(f"Attempting to start auto-play mode: {mode}...", "user")
        if not self._ensure_engine_ready():
            self.add_to_output("Engine not ready. Auto-play aborted.", "user"); return

        initial_board_updated = self._update_internal_board_state()
        # If board update fails AND there were moves (it's not an initial empty board), then abort.
        if not initial_board_updated and self.internal_board.move_stack:
            self.add_to_output("Board update from website failed. Auto-play aborted.", "user"); return

        if self.internal_board.is_game_over():
            self.add_to_output(f"Game is already over ({self.internal_board.result()}). Cannot start auto-play.", "user"); return

        self.bot_color_for_auto_play = self.internal_board.turn
        self.add_to_output(f"Bot will play as {'White' if self.bot_color_for_auto_play == chess.WHITE else 'Black'}.", "user")

        if not self.engine_communicator: # Should have been caught by _ensure_engine_ready
            self.add_to_output("Engine communicator not available. Auto-play aborted.", "user"); return

        # Create and start AutoPlayer instance and its thread
        self.auto_player_instance = AutoPlayer(
            self.engine_communicator,
            self.internal_board,
            self._update_internal_board_state,
            self.add_to_output,
            self._get_player_clock_time_stub,
            self.browser_manager.get_board_orientation # Pass the callback
        )
        self.auto_player_instance.set_ui_update_on_stop_cb(self.update_auto_play_ui_on_stop)
        self.auto_player_instance.start_playing(mode, self.bot_color_for_auto_play)

        self.auto_play_thread = threading.Thread(target=self.auto_player_instance.play_loop, daemon=True)
        self.auto_play_thread.start()

        # Start keyboard listener for failsafe
        self.keyboard_listener_instance = KeyboardListener(
            FAILSAFE_KEY, self._handle_auto_play_stop_request, self.add_to_output
        )
        self.keyboard_listener_instance.start()
        self.add_to_output(f"Keyboard failsafe active: Press '{FAILSAFE_KEY.upper()}' to stop auto-play.", "user")

        # Update UI to reflect auto-play state
        btn_clicked = self.btn_bullet_bot if mode == "bullet" else self.btn_blitz_bot
        btn_other = self.btn_blitz_bot if mode == "bullet" else self.btn_bullet_bot
        btn_clicked.configure(text=f"Stop {mode.capitalize()}")
        btn_other.configure(state="disabled") # Disable the other play mode button
        # Disable other actions that might interfere
        for btn in [self.btn_run_bot, self.btn_get_board, self.btn_get_fen]:
            btn.configure(state="disabled")


    def update_auto_play_ui_on_stop(self):
        """Resets UI elements related to auto-play to their non-playing state."""
        # Determine base state for buttons (enabled if browser is open)
        btn_state = "normal" if self.browser_manager.driver else "disabled"

        self.btn_bullet_bot.configure(text="Play Bullet", state=btn_state)
        self.btn_blitz_bot.configure(text="Play Blitz", state=btn_state)

        # Re-enable other action buttons
        for btn in [self.btn_run_bot, self.btn_get_board, self.btn_get_fen]:
            btn.configure(state=btn_state)

        self.add_to_output("Auto-play UI has been reset.", "debug")


if __name__ == "__main__":
    # This check is primarily for when ui.py might be run directly for testing,
    # though main.py is the standard entry point.
    # Ensure BASE_DIR from config.py is correctly determined.
    if not CHESS_USERNAME or not CHESS_PASSWORD:
        env_path_info = os.path.join(BASE_DIR, ".env")
        print(f"CRITICAL: Chess credentials (CHESS_USERNAME, CHESS_PASSWORD) not found in .env file (expected at {env_path_info}).")
        try:
            # Attempt to show a GUI error even if the main app hasn't started
            temp_root = ctk.CTk()
            temp_root.withdraw() # Hide the empty root window
            messagebox.showerror("Configuration Error", f"Chess credentials not found in .env file (expected at {env_path_info}). Please create this file and add your credentials, then restart the application.")
            temp_root.destroy()
        except Exception: # pylint: disable=broad-except
            # If GUI error fails (e.g., no display), console print is the fallback.
            pass
        # Consider exiting here if credentials are absolutely critical for any operation
        # sys.exit("Configuration error: Missing credentials.")
    app = ChessApp()
    app.mainloop()