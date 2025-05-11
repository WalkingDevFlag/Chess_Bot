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
from browser_automation import BrowserManager
from engine_communication import ChessEngineCommunicator
from auto_player import AutoPlayer
from keyboard_listener import KeyboardListener


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
        self.debug_log_textbox_frame = ctk.CTkFrame(self.main_frame)
        self.debug_log_textbox = ctk.CTkTextbox(self.debug_log_textbox_frame, wrap="word", state="disabled", height=150)
        self.debug_log_textbox.pack(fill="both", expand=True, padx=5, pady=5)

    def _toggle_debug_logs_command_handler(self) -> None:
        if self.debug_logs_visible:
            self.debug_log_textbox_frame.pack_forget()
            self.btn_toggle_debug_logs.configure(text="Show Debug Logs")
            self.geometry(DEFAULT_WINDOW_SIZE)
        else:
            self.debug_log_textbox_frame.pack(pady=5, padx=5, fill="both", expand=True, before=self.btn_toggle_debug_logs)
            self.btn_toggle_debug_logs.configure(text="Hide Debug Logs")
            self.geometry(DEBUG_WINDOW_SIZE)
        self.debug_logs_visible = not self.debug_logs_visible

    def add_to_output(self, message: str, log_type: str = "user") -> None:
        formatted_message = f"{message}\n"
        target_textbox = self.output_textbox if log_type == "user" else self.debug_log_textbox
        def _update_textbox():
            target_textbox.configure(state="normal")
            target_textbox.insert("end", formatted_message)
            target_textbox.see("end")
            target_textbox.configure(state="disabled")
        if threading.current_thread() is threading.main_thread(): _update_textbox()
        else: self.after(0, _update_textbox)
        self.update_idletasks()

    def _clear_output_command_handler(self) -> None:
        for tb in [self.output_textbox, self.debug_log_textbox]:
            tb.configure(state="normal"); tb.delete("1.0", "end"); tb.configure(state="disabled")
        self.add_to_output("Output cleared.", log_type="user")

    def on_closing(self) -> None:
        self.add_to_output("Closing application...", log_type="debug")
        self._stop_auto_play_components(log_message=False)
        if self.engine_communicator: self.engine_communicator.stop_engine()
        if self.browser_manager: self.browser_manager.quit_browser()
        self.destroy()

    def _ensure_engine_ready(self) -> bool:
        # This function relies on ENGINE_PATH_LOCAL and ENGINE_PATH_LOCAL_EXE 
        # being correctly set by config.py (which should be PyInstaller-aware)
        if not self.browser_manager.driver:
            self.add_to_output("Browser not open.", "user"); return False
        
        final_engine_path = None
        # ENGINE_PATH_LOCAL and ENGINE_PATH_LOCAL_EXE are imported from config.
        # If running frozen, config.BASE_DIR (and thus these paths) should point into sys._MEIPASS.
        if os.path.exists(ENGINE_PATH_LOCAL): 
            final_engine_path = ENGINE_PATH_LOCAL
        elif os.name == 'nt' and os.path.exists(ENGINE_PATH_LOCAL_EXE): 
            final_engine_path = ENGINE_PATH_LOCAL_EXE
        else:
            # Fallback to shutil.which if not found in the (potentially bundled) paths
            # This is less ideal for a one-file bundle as it means the engine isn't self-contained.
            self.add_to_output(f"Engine not found at primary paths: '{ENGINE_PATH_LOCAL}' or '{ENGINE_PATH_LOCAL_EXE}'. Checking PATH...", "debug")
            path_from_shutil = shutil.which(DEFAULT_ENGINE_NAME) or \
                               (os.name == 'nt' and shutil.which(f"{DEFAULT_ENGINE_NAME}.exe"))
            if path_from_shutil: 
                final_engine_path = path_from_shutil
                self.add_to_output(f"Warning: Using engine from system PATH: {final_engine_path}", "user")

        if not final_engine_path:
            err_msg = f"Engine '{DEFAULT_ENGINE_NAME}' not found in expected locations or system PATH."
            self.add_to_output(err_msg, "user"); messagebox.showerror("Engine Not Found", err_msg); return False
        
        self.add_to_output(f"Attempting to use engine: {final_engine_path}", "debug")

        if self.engine_communicator is None or \
           not self.engine_communicator.engine_process or \
           self.engine_communicator.engine_process.poll() is not None or \
           self.engine_communicator.engine_path != final_engine_path:
            try:
                if self.engine_communicator: self.engine_communicator.stop_engine()
                self.add_to_output(f"Initializing {DEFAULT_ENGINE_NAME} from {final_engine_path}...", "debug")
                self.engine_communicator = ChessEngineCommunicator(final_engine_path, self.add_to_output)
            except Exception as e: # pylint: disable=broad-except
                self.add_to_output(f"Failed to init {DEFAULT_ENGINE_NAME}: {e}", "user")
                messagebox.showerror("Engine Error", f"Failed to init {DEFAULT_ENGINE_NAME}: {e}")
                self.engine_communicator = None; return False
        return bool(self.engine_communicator and self.engine_communicator.engine_process and \
               self.engine_communicator.engine_process.poll() is None)

    def _open_browser_command_handler(self) -> None:
        if self.browser_manager.open_browser():
            for btn in [self.btn_login, self.btn_get_board, self.btn_get_fen, self.btn_run_bot, self.btn_bullet_bot, self.btn_blitz_bot]:
                btn.configure(state="normal")
        else: messagebox.showerror("Browser Error", "Could not open browser.")
            
    def _login_command_handler(self) -> None:
        if not CHESS_USERNAME or not CHESS_PASSWORD:
            self.add_to_output("Username/Password not set in .env.", "user")
            messagebox.showerror("Config Error", "Chess username/password not set in .env")
            return
        if not self.browser_manager.login(CHESS_USERNAME, CHESS_PASSWORD):
            messagebox.showwarning("Login Failed", "Login failed. Check credentials/website.")

    def _update_internal_board_state(self) -> bool:
        self.internal_board.reset() 
        scraped_moves = self.browser_manager.get_scraped_moves()
        if not scraped_moves:
            self.add_to_output("No moves scraped. Board reset to initial.", "debug"); return True
        parsed_count = 0
        for move_san_original in scraped_moves:
            try:
                move_san_cleaned = re.sub(r"^\d+\.*\s*", "", move_san_original).strip()
                if not move_san_cleaned: continue
                self.internal_board.push_san(move_san_cleaned); parsed_count += 1
            except Exception as e: # pylint: disable=broad-except
                self.add_to_output(f"Error parsing '{move_san_original}': {e}", "debug")
        if parsed_count == len(scraped_moves) and parsed_count > 0 :
            self.add_to_output(f"Board updated: {parsed_count} moves. FEN: {self.internal_board.fen()}", "debug"); return True
        elif parsed_count > 0:
            self.add_to_output(f"Board partially updated: {parsed_count}/{len(scraped_moves)}. FEN: {self.internal_board.fen()}", "debug"); return True
        else:
            self.add_to_output("All scraped moves failed parsing. Board state may be incorrect.", "user"); return False

    def _get_board_command_handler(self) -> None:
        if self._update_internal_board_state():
            if not self.internal_board.move_stack: self.add_to_output("Board is initial.", "user")
            self.add_to_output("--- Virtual Board ---\n" + str(self.internal_board) + "\n-------------------", "user")
        else: self.add_to_output("Could not display board (parse failed).", "user")

    def _get_fen_command_handler(self) -> None:
        if self._update_internal_board_state():
            if not self.internal_board.move_stack: self.add_to_output("Board is initial.", "user")
            self.add_to_output(f"FEN: {self.internal_board.fen()}", "user")
        else: self.add_to_output("Could not get FEN (parse failed).", "user")

    def _run_bot_command_handler(self) -> None:
        self.add_to_output(f"Suggest move ({DEFAULT_ENGINE_NAME})...", "user")
        if not self._ensure_engine_ready(): self.add_to_output("Engine not ready.", "user"); return
        board_updated = self._update_internal_board_state()
        if not board_updated and self.internal_board.move_stack:
            self.add_to_output("Board update failed (parse error).", "user"); return
        if self.internal_board.is_game_over():
            self.add_to_output(f"Game over ({self.internal_board.result()}).", "user"); return
        current_fen = self.internal_board.fen()
        self.add_to_output(f"FEN for engine: {current_fen}", "debug")
        if self.engine_communicator and self.engine_communicator.engine_process and \
           self.engine_communicator.engine_process.poll() is None:
            try:
                movetime_ms = min(max(self.internal_board.ply() * 70 + 1000, 500), 5000) 
                self.add_to_output(f"Engine thinking ({movetime_ms}ms)...", "debug")
                best_move_uci = self.engine_communicator.get_best_move(current_fen, movetime_ms=movetime_ms)
                if best_move_uci and best_move_uci != "(none)":
                    try:
                        move_obj = self.internal_board.parse_uci(best_move_uci)
                        self.add_to_output(f"Suggested: {self.internal_board.san(move_obj)} (UCI: {best_move_uci})", "user")
                    except Exception as e: self.add_to_output(f"Suggested (UCI): {best_move_uci} (SAN parse error: {e})", "user") # pylint: disable=broad-except
                elif best_move_uci == "(none)": self.add_to_output(f"{DEFAULT_ENGINE_NAME} returned (none).", "user")
                else: self.add_to_output(f"{DEFAULT_ENGINE_NAME} no valid move/timed out.", "user")
            except Exception as e: # pylint: disable=broad-except
                self.add_to_output(f"Error with {DEFAULT_ENGINE_NAME}: {e}", "user")
                messagebox.showerror("Engine Error", f"Error: {e}")
        else: self.add_to_output(f"{DEFAULT_ENGINE_NAME} not running/failed init.", "user")

    def _get_player_clock_time_stub(self, color_to_check: chess.Color) -> Optional[float]:
        return self.browser_manager.get_player_clock_time(color_to_check)

    def _handle_auto_play_stop_request(self):
        if self.auto_player_instance and self.auto_player_instance.is_playing:
            self.add_to_output(f"Auto-play stop via key '{FAILSAFE_KEY.upper()}' or button.", "user")
            self._stop_auto_play_components()

    def _stop_auto_play_components(self, log_message=True):
        if self.keyboard_listener_instance:
            if log_message: self.add_to_output("Stopping keyboard listener...", "debug")
            self.keyboard_listener_instance.stop(); self.keyboard_listener_instance = None
        if self.auto_player_instance and self.auto_player_instance.is_playing:
            if log_message: self.add_to_output(f"Stopping auto-play ({self.auto_player_instance.game_mode})...", "user")
            self.auto_player_instance.stop_playing()
            if self.auto_play_thread and self.auto_play_thread.is_alive():
                if log_message: self.add_to_output("Waiting for auto-play thread...", "debug")
                self.auto_play_thread.join(timeout=1.5)
        self.auto_player_instance = None; self.auto_play_thread = None
        self.after(0, self.update_auto_play_ui_on_stop)

    def _toggle_auto_play_mode_handler(self, mode: str) -> None:
        if self.auto_player_instance and self.auto_player_instance.is_playing:
            self._stop_auto_play_components(); return
        self.add_to_output(f"Starting auto-play: {mode}...", "user")
        if not self._ensure_engine_ready(): self.add_to_output("Engine not ready.", "user"); return
        initial_board_updated = self._update_internal_board_state()
        if not initial_board_updated and self.internal_board.move_stack:
            self.add_to_output("Board update failed (parse error).", "user"); return
        if self.internal_board.is_game_over():
            self.add_to_output(f"Game over ({self.internal_board.result()}).", "user"); return
        self.bot_color_for_auto_play = self.internal_board.turn
        self.add_to_output(f"Bot plays as {'White' if self.bot_color_for_auto_play == chess.WHITE else 'Black'}.", "user")
        if not self.engine_communicator: self.add_to_output("Engine not available.", "user"); return

        self.auto_player_instance = AutoPlayer(
            self.engine_communicator, self.internal_board, self._update_internal_board_state,
            self.add_to_output, self._get_player_clock_time_stub, self.browser_manager.get_board_orientation
        )
        self.auto_player_instance.set_ui_update_on_stop_cb(self.update_auto_play_ui_on_stop)
        self.auto_player_instance.start_playing(mode, self.bot_color_for_auto_play)
        self.auto_play_thread = threading.Thread(target=self.auto_player_instance.play_loop, daemon=True)
        self.auto_play_thread.start()

        self.keyboard_listener_instance = KeyboardListener(
            FAILSAFE_KEY, self._handle_auto_play_stop_request, self.add_to_output
        )
        self.keyboard_listener_instance.start()
        self.add_to_output(f"Keyboard failsafe: Press '{FAILSAFE_KEY.upper()}' to stop.", "user")

        btn_clicked = self.btn_bullet_bot if mode == "bullet" else self.btn_blitz_bot
        btn_other = self.btn_blitz_bot if mode == "bullet" else self.btn_bullet_bot
        btn_clicked.configure(text=f"Stop {mode.capitalize()}"); btn_other.configure(state="disabled")
        for btn in [self.btn_run_bot, self.btn_get_board, self.btn_get_fen]: btn.configure(state="disabled")

    def update_auto_play_ui_on_stop(self):
        btn_state = "normal" if self.browser_manager.driver else "disabled"
        self.btn_bullet_bot.configure(text="Play Bullet", state=btn_state)
        self.btn_blitz_bot.configure(text="Play Blitz", state=btn_state)
        for btn in [self.btn_run_bot, self.btn_get_board, self.btn_get_fen]: btn.configure(state=btn_state)
        self.add_to_output("Auto-play UI reset.", "debug")

if __name__ == "__main__":
    # This import is here to ensure sys is available for config.py when it's imported.
    # It's a bit unusual but addresses the case where config.py might be the first
    # to need sys for the getattr(sys, 'frozen', False) check if this script were run directly
    # in a way that config.py gets parsed before other sys imports.
    # However, typically main.py imports ui, ui imports config, and config imports sys.
    # For robustness if config.py is imported very early:
    import sys # pylint: disable=unused-import, wrong-import-position 

    if not CHESS_USERNAME or not CHESS_PASSWORD:
        print(f"CRITICAL: Credentials not in .env (expected at {os.path.join(BASE_DIR, '.env')}).")
        try:
            temp_root = ctk.CTk(); temp_root.withdraw()
            messagebox.showerror("Config Error", "Credentials not in .env. Please create and restart.")
            temp_root.destroy()
        except Exception: pass # pylint: disable=broad-except
    app = ChessApp()
    app.mainloop()