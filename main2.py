import customtkinter as ctk
from tkinter import messagebox
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import ElementNotInteractableException, TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
import chess
import time
from bs4 import BeautifulSoup, NavigableString
from dotenv import dotenv_values
import os
import re
import subprocess
import shutil # For shutil.which

# Load environment variables
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
dotenv_path = os.path.join(BASE_DIR, ".env")
config = dotenv_values(dotenv_path)

CHESS_USERNAME = config.get("CHESS_USERNAME")
CHESS_PASSWORD = config.get("CHESS_PASSWORD")

DEFAULT_ENGINE_NAME = "Ethereal-9.00"

class ChessEngineCommunicator:
    def __init__(self, engine_path, logger_func=print):
        self.engine_path = engine_path
        self.logger = logger_func 
        self.engine_process = None
        self._start_engine()

    def _start_engine(self):
        try:
            self.logger(f"Starting chess engine: {self.engine_path}", log_type="debug")
            creationflags = 0
            if os.name == 'nt':
                creationflags = subprocess.CREATE_NO_WINDOW
            self.engine_process = subprocess.Popen(
                [self.engine_path],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True, bufsize=1, universal_newlines=True,
                creationflags=creationflags
            )
            self._initialize_uci()
            self.logger("Chess engine started and UCI initialized.", log_type="debug")
        except FileNotFoundError:
            self.logger(f"ERROR: Engine executable not found at {self.engine_path}", log_type="debug")
            self.engine_process = None; raise
        except OSError as e:
            self.logger(f"ERROR: OSError while trying to start engine: {e}", log_type="debug")
            if hasattr(e, 'winerror') and e.winerror == 193:
                self.logger("This error (WinError 193) means the engine executable is not compatible with your Windows OS. It might be compiled for a different system (e.g., Linux).", log_type="debug")
            self.engine_process = None; raise
        except Exception as e:
            self.logger(f"ERROR: Failed to start engine process: {e}", log_type="debug")
            if self.engine_process:
                try: self.engine_process.kill()
                except: pass
            self.engine_process = None; raise

    def _initialize_uci(self):
        if not self.engine_process: self.logger("Engine process not running, cannot send UCI.", log_type="debug"); return
        self.send_command("uci")
        uci_handshake_timeout = time.time() + 10; uciok_received = False
        while time.time() < uci_handshake_timeout:
            output = self.read_output_line()
            if output is None: self.logger("ERROR: No output from engine during UCI handshake or engine terminated.", log_type="debug"); raise Exception("Engine terminated or did not respond to UCI.")
            if "uciok" in output: uciok_received = True; break
        if not uciok_received: self.logger("ERROR: Timeout waiting for 'uciok' from engine.", log_type="debug"); raise Exception("Engine did not respond with 'uciok'.")
        self.send_command("isready")
        isready_timeout = time.time() + 10; readyok_received = False
        while time.time() < isready_timeout:
            ready_output = self.read_output_line()
            if ready_output is None: self.logger("ERROR: No output from engine during isready or engine terminated.", log_type="debug"); raise Exception("Engine terminated or did not respond to isready.")
            if "readyok" in ready_output: readyok_received = True; break
        if not readyok_received: self.logger("ERROR: Timeout waiting for 'readyok' from engine.", log_type="debug"); raise Exception("Engine did not respond with 'readyok'.")
        self.send_command("setoption name Hash value 32")

    def send_command(self, command):
        if self.engine_process and self.engine_process.stdin and not self.engine_process.stdin.closed:
            try:
                self.logger(f"To Engine: {command}", log_type="debug")
                self.engine_process.stdin.write(command + "\n"); self.engine_process.stdin.flush()
            except BrokenPipeError: self.logger("ERROR: Broken pipe. Engine may have crashed or stdin closed.", log_type="debug"); self.engine_process = None
            except Exception as e: self.logger(f"ERROR sending command '{command}': {e}", log_type="debug"); self.engine_process = None
        elif self.engine_process and hasattr(self.engine_process.stdin, 'closed') and self.engine_process.stdin.closed:
             self.logger(f"ERROR: Cannot send command '{command}', engine stdin is closed.", log_type="debug"); self.engine_process = None

    def read_output_line(self):
        if self.engine_process and self.engine_process.stdout and not self.engine_process.stdout.closed:
            try:
                output_line = self.engine_process.stdout.readline()
                if not output_line and self.engine_process.poll() is not None: self.logger("Engine process terminated while expecting output.", log_type="debug"); return None
                output = output_line.strip()
                if output: self.logger(f"From Engine: {output}", log_type="debug")
                return output
            except Exception as e: self.logger(f"ERROR reading engine output: {e}", log_type="debug"); return None
        return None

    def get_best_move(self, fen, movetime_ms=2000):
        if not self.engine_process or (self.engine_process.poll() is not None):
            self.logger("Engine not running or has terminated. Cannot get best move.", log_type="debug")
            if self.engine_path and self.engine_process and self.engine_process.poll() is not None:
                self.logger("Attempting to restart the engine...", log_type="debug")
                try:
                    self._start_engine()
                    if not self.engine_process or self.engine_process.poll() is not None: self.logger("Engine restart failed.", log_type="debug"); return None
                except Exception as e: self.logger(f"Engine restart failed: {e}", log_type="debug"); return None
            else: return None
        self.send_command("ucinewgame"); self.send_command("isready")
        ready_timeout = time.time() + 5; is_ready = False
        while time.time() < ready_timeout:
            output = self.read_output_line()
            if output is None: return None
            if "readyok" in output: is_ready = True; break
        if not is_ready: self.logger("Engine not ready after ucinewgame. Aborting get_best_move.", log_type="debug"); return None
        self.send_command(f"position fen {fen}"); self.send_command(f"go movetime {movetime_ms}")
        best_move = None; start_time = time.time(); wait_timeout_duration = (movetime_ms / 1000.0) + 10
        while True:
            if time.time() - start_time > wait_timeout_duration: self.logger(f"ERROR: Timeout ({wait_timeout_duration:.1f}s) waiting for 'bestmove' from engine.", log_type="debug"); self.send_command("stop"); return None
            output = self.read_output_line()
            if output is None: self.logger("ERROR: Engine stream ended unexpectedly while waiting for bestmove.", log_type="debug"); return None
            if output.startswith("bestmove"): parts = output.split(); best_move = parts[1] if len(parts) > 1 else None; break
        return best_move

    def stop_engine(self):
        if self.engine_process:
            self.logger("Stopping chess engine...", log_type="debug")
            if self.engine_process.poll() is None:
                try: self.send_command("quit"); self.engine_process.communicate(timeout=3)
                except subprocess.TimeoutExpired: self.logger("Engine did not quit gracefully, killing process.", log_type="debug"); self.engine_process.kill(); self.engine_process.communicate()
                except Exception as e: self.logger(f"Exception during engine stop: {e}. Attempting to kill.", log_type="debug"); 
                try: self.engine_process.kill(); self.engine_process.communicate()
                except Exception as kill_e: self.logger(f"Exception during fallback kill: {kill_e}", log_type="debug")
            else: self.logger("Engine process was already terminated.", log_type="debug")
            self.engine_process = None; self.logger("Chess engine stopped.", log_type="debug")

class ChessApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Chess.com AI Helper")
        self.geometry("700x600")
        ctk.set_appearance_mode("dark"); ctk.set_default_color_theme("blue")
        self.driver = None; self.internal_board = chess.Board(); self.chess_engine_instance = None
        
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(pady=10, padx=10, fill="both", expand=True)

        self.button_frame = ctk.CTkFrame(self.main_frame)
        self.button_frame.pack(pady=5, padx=5, fill="x")

        self.btn_open_browser = ctk.CTkButton(self.button_frame, text="Open Browser", command=self.open_browser_command)
        self.btn_open_browser.pack(pady=5, padx=5, fill="x")
        self.btn_login = ctk.CTkButton(self.button_frame, text="Login", command=self.login_command, state="disabled")
        self.btn_login.pack(pady=5, padx=5, fill="x")
        self.btn_get_board = ctk.CTkButton(self.button_frame, text="Get Virtual Board", command=self.get_board_command, state="disabled")
        self.btn_get_board.pack(pady=5, padx=5, fill="x")
        self.btn_get_fen = ctk.CTkButton(self.button_frame, text="Get FEN", command=self.get_fen_command, state="disabled")
        self.btn_get_fen.pack(pady=5, padx=5, fill="x")
        self.btn_run_bot = ctk.CTkButton(self.button_frame, text=f"Run Bot ({DEFAULT_ENGINE_NAME})", command=self.run_bot_command, state="disabled")
        self.btn_run_bot.pack(pady=5, padx=5, fill="x")
        
        self.output_frame = ctk.CTkFrame(self.main_frame)
        self.output_frame.pack(pady=5, padx=5, fill="both", expand=True)
        self.output_textbox = ctk.CTkTextbox(self.output_frame, wrap="word", state="disabled", height=150)
        self.output_textbox.pack(fill="both", expand=True, padx=5, pady=5)

        self.btn_toggle_debug_logs = ctk.CTkButton(self.main_frame, text="Show Debug Logs", command=self.toggle_debug_logs_command, height=28)
        self.btn_toggle_debug_logs.pack(pady=(5,0), padx=5, fill="x")

        self.debug_logs_visible = False
        self.debug_log_textbox_frame = ctk.CTkFrame(self.main_frame)
        self.debug_log_textbox = ctk.CTkTextbox(self.debug_log_textbox_frame, wrap="word", state="disabled", height=150)
        self.debug_log_textbox.pack(fill="both", expand=True, padx=5, pady=5)

        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def toggle_debug_logs_command(self):
        if self.debug_logs_visible:
            self.debug_log_textbox_frame.pack_forget()
            self.btn_toggle_debug_logs.configure(text="Show Debug Logs")
            self.geometry("700x600")
        else:
            self.debug_log_textbox_frame.pack(pady=5, padx=5, fill="both", expand=True, before=self.btn_toggle_debug_logs)
            self.btn_toggle_debug_logs.configure(text="Hide Debug Logs")
            self.geometry("700x800")
        self.debug_logs_visible = not self.debug_logs_visible

    def add_to_output(self, message, log_type="user"):
        current_time = time.strftime('%H:%M:%S')
        formatted_message = f"{current_time} - {message}\n"
        target_textbox = self.output_textbox if log_type == "user" else self.debug_log_textbox
        target_textbox.configure(state="normal")
        target_textbox.insert("end", formatted_message)
        target_textbox.see("end")
        target_textbox.configure(state="disabled")
        self.update_idletasks()

    def on_closing(self):
        if self.chess_engine_instance: self.chess_engine_instance.stop_engine()
        if self.driver:
            try: self.driver.quit()
            except Exception as e: self.add_to_output(f"Error quitting driver: {e}", log_type="debug")
        self.destroy()

    def open_browser_command(self):
        if self.driver: self.add_to_output("Browser already open.", log_type="user"); return
        try:
            self.add_to_output("Opening chess.com...", log_type="user")
            options=webdriver.ChromeOptions(); options.add_experimental_option('excludeSwitches',['enable-logging'])
            service=ChromeService(ChromeDriverManager().install()); self.driver=webdriver.Chrome(service=service,options=options)
            self.driver.get("https://www.chess.com"); self.add_to_output("Chess.com opened.", log_type="user")
            self.btn_login.configure(state="normal"); self.btn_get_board.configure(state="normal")
            self.btn_get_fen.configure(state="normal"); self.btn_run_bot.configure(state="normal")
        except Exception as e: self.add_to_output(f"Error opening browser: {e}", log_type="user"); messagebox.showerror("Browser Error",f"Could not open browser: {e}"); self.driver=None

    def login_command(self):
        if not self.driver: self.add_to_output("Browser not open.", log_type="user"); return
        if not CHESS_USERNAME or not CHESS_PASSWORD: self.add_to_output("Credentials not found.", log_type="user"); return
        try:
            self.add_to_output("Logging in...", log_type="user")
            self.add_to_output("Navigating to login page...", log_type="debug")
            self.driver.get("https://www.chess.com/login"); wait=WebDriverWait(self.driver,20)
            self.add_to_output("Waiting for username field...", log_type="debug")
            username_field=wait.until(EC.visibility_of_element_located((By.ID,"login-username"))); username_field.clear(); username_field.send_keys(CHESS_USERNAME)
            self.add_to_output("Username entered.", log_type="debug")
            self.add_to_output("Waiting for password field...", log_type="debug")
            password_field=wait.until(EC.visibility_of_element_located((By.ID,"login-password"))); password_field.clear(); password_field.send_keys(CHESS_PASSWORD)
            self.add_to_output("Password entered.", log_type="debug")
            login_button=wait.until(EC.element_to_be_clickable((By.ID,"login")))
            self.add_to_output("Attempting to click login button...", log_type="debug")
            try: login_button.click()
            except ElementNotInteractableException: self.driver.execute_script("arguments[0].click();",login_button)
            self.add_to_output("Waiting for login to complete...", log_type="debug")
            WebDriverWait(self.driver,30).until(EC.any_of(EC.url_contains("/home"),EC.url_contains("/play/online"),EC.url_contains(f"/member/{CHESS_USERNAME.lower()}"),EC.url_contains("/today")))
            if "login" in self.driver.current_url.lower() or "credentials" in self.driver.current_url.lower(): self.add_to_output("Login failed. Check credentials.", log_type="user"); return
            self.add_to_output("Login successful.", log_type="user")
        except TimeoutException: self.add_to_output(f"Login timeout. URL: '{self.driver.current_url}'", log_type="user");
        except Exception as e: self.add_to_output(f"Login error: {e}", log_type="user")

    def _extract_san_from_ply_div(self, ply_div):
        highlight_span = ply_div.find('span', class_='node-highlight-content')
        if not highlight_span:
            raw_text = ply_div.get_text(strip=True)
            cleaned_text = re.sub(r"^\d+\.*\s*", "", raw_text).strip()
            return cleaned_text if cleaned_text else None
        figurine_span = highlight_span.find('span', class_='icon-font-chess')
        piece_char_from_data = ''
        if figurine_span and 'data-figurine' in figurine_span.attrs:
            piece_char_from_data = figurine_span['data-figurine']
        if piece_char_from_data == 'P': piece_char_from_data = ''
        move_detail_parts = []
        for content in highlight_span.contents:
            if isinstance(content, NavigableString):
                move_detail_parts.append(str(content).strip())
            elif hasattr(content, 'name') and content.name == 'span' and 'icon-font-chess' in content.get('class', []):
                continue
            elif hasattr(content, 'get_text'):
                tag_text = content.get_text(strip=True) 
                if tag_text: 
                    move_detail_parts.append(tag_text)
        move_detail_from_text = "".join(filter(None, move_detail_parts)).strip()
        if move_detail_from_text and move_detail_from_text[0].isupper() and move_detail_from_text[0] in "KQRBN":
            san = move_detail_from_text
        elif piece_char_from_data: san = piece_char_from_data + move_detail_from_text
        else: san = move_detail_from_text
        if san: san = san.replace('+', '').replace('#', '').replace('!', '').replace('?', '')
        return san if san else None

    def _get_moves_from_page(self):
        if not self.driver:
            self.add_to_output("Browser not open.", log_type="debug")
            return []
        try:
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            moves_san = []

            # Find all divs that represent a "turn row" which contains one or two plies
            turn_rows = soup.find_all('div', class_=lambda value: value and 'main-line-row' in value and 'move-list-row' in value)
            
            if turn_rows:
                self.add_to_output(f"Found {len(turn_rows)} 'main-line-row move-list-row' elements (turn rows).", log_type="debug")
                for turn_row_div in turn_rows:
                    # Within each turn row, find the individual ply divs
                    ply_divs_in_row = turn_row_div.find_all('div', class_=lambda c: c and 'node' in c.split() and ('white-move' in c.split() or 'black-move' in c.split()) and 'main-line-ply' in c.split())
                    for ply_div in ply_divs_in_row:
                        # Check if this ply_div is part of a subline (variation)
                        if ply_div.find_parent(class_=lambda c: c and 'subline' in c.split()): # Removed limit argument
                            continue # Skip this ply as it's a variation
                        san = self._extract_san_from_ply_div(ply_div)
                        if san:
                            moves_san.append(san)
            else:
                # Fallback: If no "turn rows" are found, try a more global search for ply divs
                # This might happen if the overall structure is flatter than expected.
                self.add_to_output("No 'main-line-row move-list-row' (turn rows) found. Trying global ply search as fallback.", log_type="debug")
                ply_divs_global = soup.find_all('div', class_=lambda c: c and 'node' in c.split() and ('white-move' in c.split() or 'black-move' in c.split()) and 'main-line-ply' in c.split())
                if ply_divs_global:
                    self.add_to_output(f"Global Fallback: Found {len(ply_divs_global)} 'node main-line-ply' elements.", log_type="debug")
                    for ply_div in ply_divs_global:
                         # Check again for subline parentage, even in global search
                        if not ply_div.find_parent(class_=lambda c: c and 'subline' in c.split()): # Removed limit argument
                            san = self._extract_san_from_ply_div(ply_div)
                            if san:
                                moves_san.append(san)
                else:
                    self.add_to_output("Global ply search also found no elements. Trying one more fallback for 'wc-vertical-move-list'.", log_type="debug")
                    # Final fallback for the wc-vertical-move-list component if others fail
                    move_list_wc = soup.find('wc-vertical-move-list')
                    if move_list_wc:
                        self.add_to_output(f"Found 'wc-vertical-move-list'. Processing its children.", log_type="debug")
                        potential_plies = move_list_wc.find_all('div', class_=['white', 'black'], recursive=True)
                        for ply_candidate in potential_plies:
                            is_subline = False; parent = ply_candidate.parent
                            while parent and parent != move_list_wc: # Check parentage up to the wc component
                                if 'subline' in parent.get('class', []): is_subline = True; break
                                parent = parent.parent
                            if is_subline: continue
                            san = self._extract_san_from_ply_div(ply_candidate)
                            if san: moves_san.append(san)
                    else:
                        self.add_to_output("No moves found with any known selector.", log_type="debug")


            if not moves_san:
                 self.add_to_output("No moves extracted from page. Structure might have changed or no game active.", log_type="debug")
            else:
                self.add_to_output(f"Final Scraped moves: {moves_san}", log_type="debug")
            return moves_san
        except Exception as e:
            self.add_to_output(f"Error scraping moves: {e}", log_type="debug")
            return []

    def _update_internal_board(self):
        self.internal_board.reset();moves=self._get_moves_from_page()
        if not moves:self.add_to_output("No moves found to update board.",log_type="user");return False
        parsed_count=0
        for move_san_original in moves:
            try:
                move_san_cleaned=re.sub(r"^\d+\.*\s*","",move_san_original).strip()
                if not move_san_cleaned:continue
                self.internal_board.push_san(move_san_cleaned);parsed_count+=1
            except ValueError as e:self.add_to_output(f"Error parsing move '{move_san_original}': {e}",log_type="debug")
            except Exception as e:self.add_to_output(f"Unexpected error parsing '{move_san_original}': {e}",log_type="debug")
        if parsed_count > 0:self.add_to_output(f"Board updated with {parsed_count} moves.",log_type="debug")
        elif not moves:pass
        else:self.add_to_output("All scraped moves failed to parse.",log_type="user");return False
        return True

    def get_board_command(self):
        if self._update_internal_board():
            self.add_to_output("--- Current Virtual Board ---", log_type="user")
            self.add_to_output(f"\n{self.internal_board}\n", log_type="user")
            self.add_to_output("---------------------------", log_type="user")
        else:self.add_to_output("Could not display board.", log_type="user")

    def get_fen_command(self):
        if self._update_internal_board():
            fen=self.internal_board.fen()
            self.add_to_output(f"FEN: {fen}", log_type="user")
        else:self.add_to_output("Could not get FEN.", log_type="user")

    def run_bot_command(self):
        self.add_to_output(f"Run Bot ({DEFAULT_ENGINE_NAME}) clicked.", log_type="user")
        if not self.driver:self.add_to_output("Browser not open.", log_type="user");return
        if not self._update_internal_board():self.add_to_output("Board update failed.", log_type="user");return
        if self.internal_board.is_game_over():self.add_to_output(f"Game over: {self.internal_board.result()}", log_type="user");return
        fen=self.internal_board.fen()
        self.add_to_output(f"Current FEN: {fen}", log_type="debug")
        engine_name_no_ext=DEFAULT_ENGINE_NAME
        engine_path_local=os.path.join(BASE_DIR,engine_name_no_ext)
        engine_path_local_exe=os.path.join(BASE_DIR,f"{engine_name_no_ext}.exe")
        final_engine_path=None
        if os.path.exists(engine_path_local):final_engine_path=engine_path_local
        elif os.name=='nt'and os.path.exists(engine_path_local_exe):final_engine_path=engine_path_local_exe
        else:
            path_from_shutil=shutil.which(engine_name_no_ext)or(os.name=='nt'and shutil.which(f"{engine_name_no_ext}.exe"))
            if path_from_shutil:final_engine_path=path_from_shutil
            else:self.add_to_output(f"Engine '{engine_name_no_ext}' not found.",log_type="user");return
        
        self.add_to_output(f"Using engine: {final_engine_path}", log_type="debug")

        if self.chess_engine_instance is None or \
           not self.chess_engine_instance.engine_process or \
           self.chess_engine_instance.engine_process.poll() is not None or \
           self.chess_engine_instance.engine_path != final_engine_path:
            try:
                if self.chess_engine_instance:self.chess_engine_instance.stop_engine()
                self.add_to_output(f"Initializing {DEFAULT_ENGINE_NAME}...", log_type="debug")
                self.chess_engine_instance=ChessEngineCommunicator(final_engine_path,self.add_to_output)
            except OSError as e:self.add_to_output(f"Engine OS Error: {e}. Ensure it's for your OS.",log_type="user");self.chess_engine_instance=None;return
            except Exception as e:self.add_to_output(f"Engine Init Error: {e}",log_type="user");self.chess_engine_instance=None;return
        
        if self.chess_engine_instance and self.chess_engine_instance.engine_process and self.chess_engine_instance.engine_process.poll()is None:
            try:
                self.add_to_output(f"Requesting move from {DEFAULT_ENGINE_NAME}...", log_type="debug")
                movetime_ms=min(max(self.internal_board.ply()*50+1000,500),5000)
                self.add_to_output(f"Thinking for {movetime_ms}ms...", log_type="debug")
                best_move_uci=self.chess_engine_instance.get_best_move(fen,movetime_ms=movetime_ms)
                if best_move_uci and best_move_uci!="(none)":
                    try:
                        move_obj=self.internal_board.parse_uci(best_move_uci)
                        best_move_san=self.internal_board.san(move_obj)
                        self.add_to_output(f"Move: {best_move_san} (UCI: {best_move_uci})", log_type="user")
                    except Exception as parse_e:self.add_to_output(f"Move (UCI): {best_move_uci} (SAN parse error: {parse_e})",log_type="user")
                elif best_move_uci=="(none)":self.add_to_output(f"{DEFAULT_ENGINE_NAME} returned (none).",log_type="user")
                else:self.add_to_output(f"{DEFAULT_ENGINE_NAME} returned no valid move.",log_type="user")
            except Exception as e:self.add_to_output(f"Engine Comm Error: {e}",log_type="user")
        else:self.add_to_output(f"{DEFAULT_ENGINE_NAME} not running.",log_type="user")

if __name__=="__main__":
    if not CHESS_USERNAME or not CHESS_PASSWORD:
        print("CRITICAL: Credentials not in .env file!")
        try:root=ctk.CTk();root.withdraw();messagebox.showerror("Config Error","Credentials not in .env!");root.destroy()
        except:pass
    app=ChessApp()
    app.mainloop()