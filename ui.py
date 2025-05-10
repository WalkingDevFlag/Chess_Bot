import customtkinter as ctk
from tkinter import messagebox
import chess
import time
import os # For joining paths
import shutil # For finding engine in PATH
import re
# Import from other modules
from config import (
    CHESS_USERNAME, CHESS_PASSWORD, DEFAULT_ENGINE_NAME, 
    WINDOW_TITLE, DEFAULT_WINDOW_SIZE, DEBUG_WINDOW_SIZE,
    ENGINE_PATH_LOCAL, ENGINE_PATH_LOCAL_EXE, BASE_DIR
)
from browser_automation import BrowserManager
from engine_communication import ChessEngineCommunicator
from typing import Optional


class ChessApp(ctk.CTk):
    """
    Main application class for the Chess.com AI Helper GUI.
    """
    def __init__(self):
        super().__init__()
        self.title(WINDOW_TITLE)
        self.geometry(DEFAULT_WINDOW_SIZE)
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.internal_board: chess.Board = chess.Board()
        
        # Initialize managers, passing self.add_to_output as the logger
        self.browser_manager: BrowserManager = BrowserManager(self.add_to_output)
        self.engine_communicator: Optional[ChessEngineCommunicator] = None

        self._setup_ui()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def _setup_ui(self) -> None:
        """Creates and packs all UI widgets."""
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
        
        output_frame = ctk.CTkFrame(self.main_frame)
        output_frame.pack(pady=5, padx=5, fill="both", expand=True)
        self.output_textbox = ctk.CTkTextbox(output_frame, wrap="word", state="disabled", height=150)
        self.output_textbox.pack(fill="both", expand=True, padx=5, pady=5)

        self.btn_toggle_debug_logs = ctk.CTkButton(self.main_frame, text="Show Debug Logs", command=self._toggle_debug_logs_command_handler, height=28)
        self.btn_toggle_debug_logs.pack(pady=(5,0), padx=5, fill="x")

        self.debug_logs_visible: bool = False
        self.debug_log_textbox_frame = ctk.CTkFrame(self.main_frame)
        self.debug_log_textbox = ctk.CTkTextbox(self.debug_log_textbox_frame, wrap="word", state="disabled", height=150)
        self.debug_log_textbox.pack(fill="both", expand=True, padx=5, pady=5)
        # debug_log_textbox_frame is not packed initially

    def _toggle_debug_logs_command_handler(self) -> None:
        """Shows or hides the debug log textbox."""
        if self.debug_logs_visible:
            self.debug_log_textbox_frame.pack_forget()
            self.btn_toggle_debug_logs.configure(text="Show Debug Logs")
            self.geometry(DEFAULT_WINDOW_SIZE)
        else:
            self.debug_log_textbox_frame.pack(pady=5, padx=5, fill="both", expand=True, before=self.btn_toggle_debug_logs) # Pack before the toggle button
            self.btn_toggle_debug_logs.configure(text="Hide Debug Logs")
            self.geometry(DEBUG_WINDOW_SIZE)
        self.debug_logs_visible = not self.debug_logs_visible

    def add_to_output(self, message: str, log_type: str = "user") -> None:
        """Adds a message to the appropriate output textbox."""
        current_time = time.strftime('%H:%M:%S')
        formatted_message = f"{current_time} - {message}\n"
        
        target_textbox = self.output_textbox
        if log_type == "debug":
            target_textbox = self.debug_log_textbox
        
        target_textbox.configure(state="normal")
        target_textbox.insert("end", formatted_message)
        target_textbox.see("end")
        target_textbox.configure(state="disabled")
        self.update_idletasks() # Ensure UI updates immediately

    def on_closing(self) -> None:
        """Handles window close event."""
        self.add_to_output("Closing application...", log_type="debug")
        if self.engine_communicator:
            self.engine_communicator.stop_engine()
        if self.browser_manager:
            self.browser_manager.quit_browser()
        self.destroy()

    def _open_browser_command_handler(self) -> None:
        """Handles the 'Open Browser' button click."""
        if self.browser_manager.open_browser():
            # Enable other buttons if browser opened successfully
            self.btn_login.configure(state="normal")
            self.btn_get_board.configure(state="normal")
            self.btn_get_fen.configure(state="normal")
            self.btn_run_bot.configure(state="normal")
        else:
            messagebox.showerror("Browser Error", "Could not open browser. Check debug logs.")
            
    def _login_command_handler(self) -> None:
        """Handles the 'Login' button click."""
        if not CHESS_USERNAME or not CHESS_PASSWORD:
            self.add_to_output("Username or Password not set in .env file.", log_type="user")
            messagebox.showerror("Config Error", "Chess username/password not configured in .env")
            return
        if not self.browser_manager.login(CHESS_USERNAME, CHESS_PASSWORD):
            messagebox.showwarning("Login Failed", "Login attempt failed. Check credentials or website status. See logs for details.")

    def _update_internal_board_state(self) -> bool:
        """Updates the internal chess board from scraped moves."""
        self.internal_board.reset()
        scraped_moves = self.browser_manager.get_scraped_moves()
        if not scraped_moves:
            self.add_to_output("No moves found to update board.", log_type="user")
            return False
        
        parsed_count = 0
        for move_san_original in scraped_moves:
            try:
                # Clean common prefixes like "1." or "1..." 
                move_san_cleaned = re.sub(r"^\d+\.*\s*", "", move_san_original).strip()
                if not move_san_cleaned: continue # Skip if cleaning resulted in empty string
                
                self.internal_board.push_san(move_san_cleaned)
                parsed_count += 1
            except ValueError as e: # Illegal move or bad SAN
                self.add_to_output(f"Error parsing move '{move_san_original}' (cleaned: '{move_san_cleaned}'): {e}. Board may be out of sync.", log_type="debug")
            except Exception as e: # Other unexpected errors
                self.add_to_output(f"Unexpected error parsing move '{move_san_original}': {e}", log_type="debug")
        
        if parsed_count > 0:
            self.add_to_output(f"Internal board updated with {parsed_count} moves.", log_type="debug")
            return True
        elif not scraped_moves: # No moves were scraped (already logged by get_scraped_moves)
            return False
        else: # Moves were scraped but all failed to parse
            self.add_to_output("All scraped moves failed to parse. Board not updated.", log_type="user")
            return False

    def _get_board_command_handler(self) -> None:
        """Handles the 'Get Virtual Board' button click."""
        if self._update_internal_board_state():
            self.add_to_output("--- Current Virtual Board ---", log_type="user")
            self.add_to_output(f"\n{self.internal_board}\n", log_type="user") # Add newlines for board display
            self.add_to_output("---------------------------", log_type="user")
        else:
            self.add_to_output("Could not display board (update failed or no moves).", log_type="user")

    def _get_fen_command_handler(self) -> None:
        """Handles the 'Get FEN' button click."""
        if self._update_internal_board_state():
            fen = self.internal_board.fen()
            self.add_to_output(f"FEN: {fen}", log_type="user")
        else:
            self.add_to_output("Could not get FEN (board update failed or no moves).", log_type="user")

    def _run_bot_command_handler(self) -> None:
        """Handles the 'Run Bot' button click."""
        self.add_to_output(f"Run Bot ({DEFAULT_ENGINE_NAME}) initiated.", log_type="user")
        if not self.browser_manager.driver:
            self.add_to_output("Browser not open. Please open the browser first.", log_type="user")
            return
        if not self._update_internal_board_state():
            self.add_to_output("Board update failed. Cannot run bot.", log_type="user")
            return
        if self.internal_board.is_game_over():
            self.add_to_output(f"Game is over ({self.internal_board.result()}). Bot not run.", log_type="user")
            return

        current_fen = self.internal_board.fen()
        self.add_to_output(f"Current FEN for engine: {current_fen}", log_type="debug")

        # Determine engine path
        final_engine_path = None
        if os.path.exists(ENGINE_PATH_LOCAL):
            final_engine_path = ENGINE_PATH_LOCAL
        elif os.name == 'nt' and os.path.exists(ENGINE_PATH_LOCAL_EXE):
            final_engine_path = ENGINE_PATH_LOCAL_EXE
        else: # Try finding in PATH
            path_from_shutil = shutil.which(DEFAULT_ENGINE_NAME) or \
                               (os.name == 'nt' and shutil.which(f"{DEFAULT_ENGINE_NAME}.exe"))
            if path_from_shutil:
                final_engine_path = path_from_shutil
        
        if not final_engine_path:
            err_msg = f"Engine '{DEFAULT_ENGINE_NAME}' (or .exe) not found in script directory or PATH."
            self.add_to_output(err_msg, log_type="user")
            messagebox.showerror("Engine Not Found", err_msg)
            return
        
        self.add_to_output(f"Using engine at: {final_engine_path}", log_type="debug")

        # Initialize or re-initialize engine if necessary
        if self.engine_communicator is None or \
           not self.engine_communicator.engine_process or \
           self.engine_communicator.engine_process.poll() is not None or \
           self.engine_communicator.engine_path != final_engine_path: # If path changed or process died
            try:
                if self.engine_communicator: # Stop old/dead instance
                    self.engine_communicator.stop_engine()
                self.add_to_output(f"Initializing {DEFAULT_ENGINE_NAME}...", log_type="debug")
                self.engine_communicator = ChessEngineCommunicator(final_engine_path, self.add_to_output)
            except OSError as e:
                 self.add_to_output(f"Engine OS Error: {e}. Ensure it's for your OS.",log_type="user"); self.engine_communicator = None; return
            except Exception as e:
                self.add_to_output(f"Failed to initialize {DEFAULT_ENGINE_NAME}: {e}", log_type="user")
                messagebox.showerror("Engine Error", f"Failed to initialize {DEFAULT_ENGINE_NAME}: {e}")
                self.engine_communicator = None; return
        
        # Get best move from engine
        if self.engine_communicator and self.engine_communicator.engine_process and \
           self.engine_communicator.engine_process.poll() is None:
            try:
                self.add_to_output(f"Requesting best move from {DEFAULT_ENGINE_NAME}...", log_type="debug")
                # Example dynamic movetime, adjust as needed
                movetime_ms = min(max(self.internal_board.ply() * 70 + 1000, 500), 5000) 
                self.add_to_output(f"Engine thinking for {movetime_ms}ms...", log_type="debug")
                
                best_move_uci = self.engine_communicator.get_best_move(current_fen, movetime_ms=movetime_ms)
                
                if best_move_uci and best_move_uci != "(none)":
                    try:
                        move_obj = self.internal_board.parse_uci(best_move_uci)
                        best_move_san = self.internal_board.san(move_obj)
                        self.add_to_output(f"Suggested Move: {best_move_san} (UCI: {best_move_uci})", log_type="user")
                    except Exception as parse_e: # Handle if UCI move is valid but SAN conversion fails
                        self.add_to_output(f"Suggested Move (UCI): {best_move_uci} (SAN parse error: {parse_e})", log_type="user")
                elif best_move_uci == "(none)":
                    self.add_to_output(f"{DEFAULT_ENGINE_NAME} returned (none) - game might be over or no legal moves for current side.", log_type="user")
                else: # Engine might have timed out or returned an empty string
                    self.add_to_output(f"{DEFAULT_ENGINE_NAME} did not return a valid best move string or timed out.", log_type="user")
            except Exception as e:
                self.add_to_output(f"Error communicating with {DEFAULT_ENGINE_NAME}: {e}", log_type="user")
                messagebox.showerror("Engine Communication Error", f"Error: {e}")
                # Consider stopping engine on communication error
                if self.engine_communicator: self.engine_communicator.stop_engine(); self.engine_communicator = None
        else:
            self.add_to_output(f"{DEFAULT_ENGINE_NAME} is not running or failed to initialize.", log_type="user")