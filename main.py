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

# Configuration for the chess engine
# If your engine is named 'Ethereal' (Linux build) or 'Ethereal.exe' (Windows build)
# place it in the same directory as this script.
DEFAULT_ENGINE_NAME = "Ethereal-9.00"
# For Windows, if your engine is Ethereal.exe, it will try that too.

class ChessEngineCommunicator:
    def __init__(self, engine_path, logger_func=print):
        self.engine_path = engine_path
        self.logger = logger_func
        self.engine_process = None
        self._start_engine()

    def _start_engine(self):
        try:
            self.logger(f"Starting chess engine: {self.engine_path}")
            # On Windows, explicitly use shell=False (default) and ensure the path is correct.
            # bufsize=1 and universal_newlines=True are good for text-based communication.
            self.engine_process = subprocess.Popen(
                [self.engine_path],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0 # Hide console window on Windows
            )
            self._initialize_uci()
            self.logger("Chess engine started and UCI initialized.")
        except FileNotFoundError:
            self.logger(f"ERROR: Engine executable not found at {self.engine_path}")
            self.engine_process = None
            raise
        except OSError as e: # Catch errors like WinError 193
            self.logger(f"ERROR: OSError while trying to start engine (e.g., not a valid executable for this OS): {e}")
            self.logger("This can happen if you're trying to run a Linux-compiled engine on Windows or vice-versa.")
            self.engine_process = None
            raise
        except Exception as e:
            self.logger(f"ERROR: Failed to start engine process: {e}")
            if self.engine_process:
                try:
                    self.engine_process.kill()
                except: pass
            self.engine_process = None
            raise

    def _initialize_uci(self):
        if not self.engine_process:
            self.logger("Engine process not running, cannot send UCI.")
            return

        self.send_command("uci")
        uci_handshake_timeout = time.time() + 10 # 10 seconds timeout for uciok
        while time.time() < uci_handshake_timeout:
            output = self.read_output_line()
            if output is None:
                self.logger("ERROR: No output from engine during UCI handshake or engine terminated.")
                raise Exception("Engine terminated or did not respond to UCI.")
            self.logger(f"Engine UCI Init: {output}")
            if "uciok" in output:
                self.send_command("isready")
                isready_timeout = time.time() + 10
                while time.time() < isready_timeout:
                    ready_output = self.read_output_line()
                    if ready_output is None:
                        self.logger("ERROR: No output from engine during isready or engine terminated.")
                        raise Exception("Engine terminated or did not respond to isready.")
                    self.logger(f"Engine Ready Check: {ready_output}")
                    if "readyok" in ready_output:
                        return # Successfully initialized
                self.logger("ERROR: Timeout waiting for 'readyok' from engine.")
                raise Exception("Engine did not respond with 'readyok'.")
        self.logger("ERROR: Timeout waiting for 'uciok' from engine.")
        raise Exception("Engine did not respond with 'uciok'.")


    def send_command(self, command):
        if self.engine_process and self.engine_process.stdin and not self.engine_process.stdin.closed:
            try:
                self.logger(f"To Engine: {command}")
                self.engine_process.stdin.write(command + "\n")
                self.engine_process.stdin.flush()
            except BrokenPipeError:
                self.logger("ERROR: Broken pipe. Engine may have crashed or stdin closed.")
                self.engine_process = None
            except Exception as e:
                self.logger(f"ERROR sending command '{command}': {e}")
                self.engine_process = None
        elif self.engine_process and self.engine_process.stdin.closed:
             self.logger(f"ERROR: Cannot send command '{command}', engine stdin is closed.")
             self.engine_process = None


    def read_output_line(self):
        if self.engine_process and self.engine_process.stdout and not self.engine_process.stdout.closed:
            try:
                output = self.engine_process.stdout.readline()
                if not output and self.engine_process.poll() is not None: # No output and process terminated
                    self.logger("Engine process terminated while expecting output.")
                    return None
                output = output.strip()
                if output:
                    self.logger(f"From Engine: {output}")
                return output
            except Exception as e:
                self.logger(f"ERROR reading engine output: {e}")
                return None
        return None

    def get_best_move(self, fen, movetime_ms=2000):
        if not self.engine_process or (self.engine_process.poll() is not None):
            self.logger("Engine not running or has terminated. Cannot get best move.")
            return None

        self.send_command("ucinewgame")
        self.send_command("isready")
        ready_timeout = time.time() + 5
        while time.time() < ready_timeout:
            output = self.read_output_line()
            if output is None: return None
            if "readyok" in output: break
        else:
            self.logger("Engine not ready after ucinewgame. Aborting get_best_move.")
            return None
        
        self.send_command(f"position fen {fen}")
        self.send_command(f"go movetime {movetime_ms}")

        best_move = None
        start_time = time.time()
        wait_timeout_duration = (movetime_ms / 1000.0) + 10 # Engine time + generous buffer

        while True:
            if time.time() - start_time > wait_timeout_duration:
                self.logger(f"ERROR: Timeout ({wait_timeout_duration}s) waiting for 'bestmove' from engine.")
                self.send_command("stop")
                return None

            output = self.read_output_line()
            if output is None:
                self.logger("ERROR: Engine stream ended unexpectedly while waiting for bestmove.")
                return None
            
            if output.startswith("bestmove"):
                parts = output.split()
                if len(parts) > 1:
                    best_move = parts[1]
                break
        return best_move

    def stop_engine(self):
        if self.engine_process:
            self.logger("Stopping chess engine...")
            if self.engine_process.poll() is None: # If still running
                try:
                    self.send_command("quit")
                    self.engine_process.communicate(timeout=3)
                except subprocess.TimeoutExpired:
                    self.logger("Engine did not quit gracefully, killing process.")
                    self.engine_process.kill()
                    self.engine_process.communicate()
                except Exception as e:
                    self.logger(f"Exception during engine stop: {e}. Attempting to kill.")
                    try:
                        self.engine_process.kill()
                        self.engine_process.communicate()
                    except Exception as kill_e:
                        self.logger(f"Exception during fallback kill: {kill_e}")
            else: # Already terminated
                self.logger("Engine process was already terminated.")
            self.engine_process = None
            self.logger("Chess engine stopped.")


class ChessApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Chess.com AI Helper")
        self.geometry("700x600")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        self.driver = None
        self.internal_board = chess.Board()
        self.chess_engine_instance = None
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(pady=20, padx=20, fill="both", expand=True)
        button_frame = ctk.CTkFrame(main_frame)
        button_frame.pack(pady=10, padx=10, fill="x")
        self.btn_open_browser = ctk.CTkButton(button_frame, text="Open Browser", command=self.open_browser_command)
        self.btn_open_browser.pack(pady=5, padx=5, fill="x")
        self.btn_login = ctk.CTkButton(button_frame, text="Login", command=self.login_command, state="disabled")
        self.btn_login.pack(pady=5, padx=5, fill="x")
        self.btn_get_board = ctk.CTkButton(button_frame, text="Get Virtual Board", command=self.get_board_command, state="disabled")
        self.btn_get_board.pack(pady=5, padx=5, fill="x")
        self.btn_get_fen = ctk.CTkButton(button_frame, text="Get FEN", command=self.get_fen_command, state="disabled")
        self.btn_get_fen.pack(pady=5, padx=5, fill="x")
        self.btn_run_bot = ctk.CTkButton(button_frame, text="Run Bot with Engine", command=self.run_bot_command, state="disabled")
        self.btn_run_bot.pack(pady=5, padx=5, fill="x")
        output_frame = ctk.CTkFrame(main_frame)
        output_frame.pack(pady=10, padx=10, fill="both", expand=True)
        self.output_textbox = ctk.CTkTextbox(output_frame, wrap="word", state="disabled", height=300)
        self.output_textbox.pack(fill="both", expand=True, padx=5, pady=5)
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def add_to_output(self, message):
        self.output_textbox.configure(state="normal")
        self.output_textbox.insert("end", f"{time.strftime('%H:%M:%S')} - {message}\n")
        self.output_textbox.see("end")
        self.output_textbox.configure(state="disabled")
        self.update_idletasks()

    def on_closing(self):
        if self.chess_engine_instance:
            self.chess_engine_instance.stop_engine()
        if self.driver:
            try:
                self.driver.quit()
            except Exception as e:
                self.add_to_output(f"Error quitting driver: {e}")
        self.destroy()

    def open_browser_command(self):
        if self.driver:
            self.add_to_output("Browser already open. Focusing existing window.")
            try:
                self.driver.switch_to.window(self.driver.current_window_handle)
            except Exception:
                self.add_to_output("Could not focus existing window.")
            return
        try:
            self.add_to_output("Opening chess.com...")
            options = webdriver.ChromeOptions()
            options.add_experimental_option('excludeSwitches', ['enable-logging'])
            service = ChromeService(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            self.driver.get("https://www.chess.com")
            self.add_to_output("Chess.com opened successfully.")
            self.btn_login.configure(state="normal")
            self.btn_get_board.configure(state="normal")
            self.btn_get_fen.configure(state="normal")
            self.btn_run_bot.configure(state="normal")
        except Exception as e:
            self.add_to_output(f"Error opening browser: {e}")
            messagebox.showerror("Browser Error", f"Could not open browser: {e}")
            self.driver = None

    def login_command(self):
        if not self.driver:
            self.add_to_output("Browser not open. Please open browser first.")
            messagebox.showwarning("Login Error", "Browser is not open.")
            return
        if not CHESS_USERNAME or not CHESS_PASSWORD:
            self.add_to_output("Username or Password not found in .env file.")
            messagebox.showerror("Login Error", "Credentials not found in .env file.")
            return
        try:
            self.add_to_output("Navigating to login page...")
            self.driver.get("https://www.chess.com/login") 
            wait = WebDriverWait(self.driver, 20)
            self.add_to_output("Waiting for username field...")
            username_field = wait.until(EC.visibility_of_element_located((By.ID, "login-username")))
            username_field.clear()
            username_field.send_keys(CHESS_USERNAME)
            self.add_to_output("Username entered.")
            self.add_to_output("Waiting for password field...")
            password_field = wait.until(EC.visibility_of_element_located((By.ID, "login-password")))
            password_field.clear()
            password_field.send_keys(CHESS_PASSWORD)
            self.add_to_output("Password entered.")
            self.add_to_output("Waiting for login button to be clickable...")
            login_button = wait.until(EC.element_to_be_clickable((By.ID, "login")))
            self.add_to_output("Attempting to click login button...")
            try:
                login_button.click()
            except ElementNotInteractableException:
                self.add_to_output("Standard click failed. Trying JavaScript click for login button...")
                self.driver.execute_script("arguments[0].click();", login_button)
            self.add_to_output("Waiting for login to complete and redirect...")
            WebDriverWait(self.driver, 30).until(
                EC.any_of(
                    EC.url_contains("/home"), EC.url_contains("/play/online"),
                    EC.url_contains(f"/member/{CHESS_USERNAME.lower()}"), EC.url_contains("/today")
                ))
            if "login" in self.driver.current_url.lower() or "credentials" in self.driver.current_url.lower():
                 self.add_to_output(f"Login may have failed. Redirected back to a login page: {self.driver.current_url}")
                 messagebox.showerror("Login Failed", "Login failed. Please check credentials or if the page redirected to an error.")
                 return
            self.add_to_output(f"Login successful. Current URL: {self.driver.current_url}")
        except TimeoutException:
            page_title = self.driver.title
            current_url = self.driver.current_url
            self.add_to_output(f"Login error: Timeout. Page title: '{page_title}', URL: '{current_url}'")
            messagebox.showerror("Login Error", "Timeout during login. Elements not found or page did not redirect as expected.")
        except Exception as e:
            self.add_to_output(f"An unexpected error occurred during login: {e}")
            messagebox.showerror("Login Error", f"An unexpected error occurred: {e}")

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
                if tag_text: move_detail_parts.append(tag_text)
        move_detail_from_text = "".join(filter(None, move_detail_parts)).strip()
        if move_detail_from_text and move_detail_from_text[0].isupper() and move_detail_from_text[0] in "KQRBN":
            san = move_detail_from_text
        elif piece_char_from_data: san = piece_char_from_data + move_detail_from_text
        else: san = move_detail_from_text
        if san: san = san.replace('+', '').replace('#', '').replace('!', '').replace('?', '')
        return san if san else None

    def _get_moves_from_page(self):
        if not self.driver:
            self.add_to_output("Browser not open.")
            return []
        try:
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            moves_san = []
            ply_divs = soup.find_all('div', class_=lambda c: c and 'node' in c.split() and ('white-move' in c.split() or 'black-move' in c.split()) and 'main-line-ply' in c.split())
            if ply_divs:
                self.add_to_output(f"Found {len(ply_divs)} direct ply elements ('node main-line-ply').")
                for ply_div in ply_divs:
                    if ply_div.find_parent(class_=lambda c: c and 'subline' in c.split()): continue
                    san = self._extract_san_from_ply_div(ply_div)
                    if san: moves_san.append(san)
            else:
                self.add_to_output("No 'node main-line-ply' elements found. Trying container search...")
                move_list_container = soup.find('div', class_='vertical-move-list') or soup.find('wc-vertical-move-list')
                if move_list_container:
                    self.add_to_output(f"Found container: '{move_list_container.name}' with classes '{move_list_container.get('class', [])}'. Processing its children.")
                    potential_plies = move_list_container.find_all('div', class_=['white', 'black'], recursive=True) 
                    for ply_candidate in potential_plies:
                        is_subline = False; parent = ply_candidate.parent
                        while parent and parent != move_list_container:
                            if 'subline' in parent.get('class', []): is_subline = True; break
                            parent = parent.parent
                        if is_subline: continue
                        san = self._extract_san_from_ply_div(ply_candidate) 
                        if san: moves_san.append(san)
                else: self.add_to_output("No known move list container or direct ply elements found.")
            if not moves_san: self.add_to_output("No moves extracted. Page structure might have changed or no game is active.")
            else: self.add_to_output(f"Scraped moves: {moves_san}")
            return moves_san
        except Exception as e:
            self.add_to_output(f"Error scraping moves: {e}")
            return []

    def _update_internal_board(self):
        self.internal_board.reset()
        moves = self._get_moves_from_page()
        if not moves: self.add_to_output("No moves found to update board."); return False
        parsed_count = 0
        for move_san_original in moves:
            try:
                move_san_cleaned = re.sub(r"^\d+\.*\s*", "", move_san_original).strip()
                if not move_san_cleaned: continue
                self.internal_board.push_san(move_san_cleaned)
                parsed_count += 1
            except ValueError as e: self.add_to_output(f"Error parsing move '{move_san_original}' (cleaned to '{move_san_cleaned}'): {e}. Board may be out of sync.")
            except Exception as e: self.add_to_output(f"Unexpected error parsing move '{move_san_original}': {e}")
        if parsed_count > 0: self.add_to_output(f"Internal board updated with {parsed_count} moves.")
        elif not moves: pass
        else: self.add_to_output("All scraped moves failed to parse. Board not updated."); return False
        return True

    def get_board_command(self):
        if self._update_internal_board():
            self.add_to_output("--- Current Virtual Board ---"); self.add_to_output(str(self.internal_board)); self.add_to_output("---------------------------")
        else: self.add_to_output("Could not display board due to update error or no moves.")

    def get_fen_command(self):
        if self._update_internal_board():
            fen = self.internal_board.fen()
            self.add_to_output(f"Current FEN: {fen}")
        else: self.add_to_output("Could not get FEN due to board update error or no moves.")

    def run_bot_command(self):
        self.add_to_output(f"Run Bot ({DEFAULT_ENGINE_NAME}) clicked.")
        if not self.driver: self.add_to_output("Browser not open. Cannot run bot."); return
        if not self._update_internal_board(): self.add_to_output("Board update failed. Cannot run bot."); return
        if self.internal_board.is_game_over():
            self.add_to_output(f"Game is over: {self.internal_board.result()}. Bot not run."); return

        fen = self.internal_board.fen()
        self.add_to_output(f"Current FEN for bot: {fen}")

        engine_path_local = os.path.join(BASE_DIR, DEFAULT_ENGINE_NAME)
        engine_path_local_exe = os.path.join(BASE_DIR, f"{DEFAULT_ENGINE_NAME}.exe") # For Windows
        
        final_engine_path = None
        if os.path.exists(engine_path_local):
            final_engine_path = engine_path_local
            self.add_to_output(f"Engine found in script directory: {final_engine_path}")
        elif os.name == 'nt' and os.path.exists(engine_path_local_exe):
            final_engine_path = engine_path_local_exe
            self.add_to_output(f"Engine (.exe) found in script directory: {final_engine_path}")
        else:
            path_from_shutil = shutil.which(DEFAULT_ENGINE_NAME) or (os.name == 'nt' and shutil.which(f"{DEFAULT_ENGINE_NAME}.exe"))
            if path_from_shutil:
                final_engine_path = path_from_shutil
                self.add_to_output(f"Engine found in PATH: {final_engine_path}")
            else:
                error_msg = f"Error: Chess engine '{DEFAULT_ENGINE_NAME}' (or .exe) not found in script directory ('{BASE_DIR}') or System PATH."
                self.add_to_output(error_msg)
                messagebox.showerror("Engine Error", error_msg)
                return

        if self.chess_engine_instance is None or not self.chess_engine_instance.engine_process or self.chess_engine_instance.engine_process.poll() is not None:
            try:
                self.add_to_output(f"Initializing chess engine: {final_engine_path}...")
                if self.chess_engine_instance and self.chess_engine_instance.engine_process: # Stale process?
                    self.chess_engine_instance.stop_engine()
                self.chess_engine_instance = ChessEngineCommunicator(final_engine_path, self.add_to_output)
            except Exception as e:
                self.add_to_output(f"Failed to initialize chess engine: {e}")
                messagebox.showerror("Engine Error", f"Failed to initialize chess engine: {e}")
                self.chess_engine_instance = None; return
        
        if self.chess_engine_instance and self.chess_engine_instance.engine_process and self.chess_engine_instance.engine_process.poll() is None:
            try:
                self.add_to_output(f"Requesting best move from {DEFAULT_ENGINE_NAME}...")
                movetime_ms = 2000 
                best_move_uci = self.chess_engine_instance.get_best_move(fen, movetime_ms=movetime_ms)
                if best_move_uci and best_move_uci != "(none)":
                    try:
                        move_obj = self.internal_board.parse_uci(best_move_uci)
                        best_move_san = self.internal_board.san(move_obj)
                        self.add_to_output(f"{DEFAULT_ENGINE_NAME} suggests: {best_move_san} (UCI: {best_move_uci})")
                    except Exception as parse_e:
                        self.add_to_output(f"{DEFAULT_ENGINE_NAME} suggests (UCI): {best_move_uci} (Could not parse to SAN: {parse_e})")
                elif best_move_uci == "(none)": self.add_to_output(f"{DEFAULT_ENGINE_NAME} returned (none) - checkmate/stalemate?")
                else: self.add_to_output(f"{DEFAULT_ENGINE_NAME} did not return a valid best move string.")
            except Exception as e:
                self.add_to_output(f"Error communicating with {DEFAULT_ENGINE_NAME}: {e}")
                messagebox.showerror("Engine Communication Error", f"Error: {e}")
                if self.chess_engine_instance: self.chess_engine_instance.stop_engine(); self.chess_engine_instance = None
        else: self.add_to_output(f"Chess engine ({DEFAULT_ENGINE_NAME}) is not running or failed to initialize.")

if __name__ == "__main__":
    if not CHESS_USERNAME or not CHESS_PASSWORD:
        print("CRITICAL: CHESS_USERNAME or CHESS_PASSWORD not set in .env file!")
        print(f"Attempted to load from: {dotenv_path}")
        print("Please create a .env file in the script directory with your chess.com credentials.")
        try:
            root = ctk.CTk(); root.withdraw(); messagebox.showerror("Configuration Error", "CHESS_USERNAME or CHESS_PASSWORD not set in .env file. Please configure .env and restart."); root.destroy()
        except Exception: pass
    app = ChessApp()
    app.mainloop()