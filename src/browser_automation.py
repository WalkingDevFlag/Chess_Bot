from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementNotInteractableException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup, NavigableString
import time
import re
from typing import Optional, List, Callable
import chess

class BrowserManager:
    def __init__(self, logger_func: Callable[[str, str], None]):
        self.driver: Optional[webdriver.Chrome] = None
        self.logger: Callable[[str, str], None] = logger_func

    def open_browser(self, url: str = "https://www.chess.com", incognito: bool = True) -> bool:
        if self.driver:
            try: self.driver.switch_to.window(self.driver.current_window_handle)
            except Exception: self.logger("Could not focus browser.", "debug") #pylint: disable=broad-except
            return True
        try:
            self.logger(f"Opening browser (Incognito: {incognito})...", "user")
            options = webdriver.ChromeOptions()
            options.add_experimental_option('excludeSwitches', ['enable-logging'])
            if incognito: options.add_argument("--incognito")
            service = ChromeService(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            self.driver.get(url)
            self.logger(f"{url} opened.", "user"); return True
        except Exception as e: #pylint: disable=broad-except
            self.logger(f"Error opening browser: {e}", "user"); self.driver = None; return False

    def login(self, username: Optional[str], password: Optional[str], 
              login_url: str = "https://www.chess.com/login",
              success_url_keywords: List[str] = ["/home", "/play", "/member/", "/today"]) -> bool:
        if not self.driver: self.logger("Browser not open.", "user"); return False
        if not username or not password: self.logger("Username/Password not provided.", "user"); return False
        try:
            self.logger("Attempting login...", "user")
            self.driver.get(login_url)
            wait = WebDriverWait(self.driver, 20)
            username_field = wait.until(EC.visibility_of_element_located((By.ID, "login-username")))
            username_field.clear(); username_field.send_keys(username)
            password_field = wait.until(EC.visibility_of_element_located((By.ID, "login-password")))
            password_field.clear(); password_field.send_keys(password)
            login_button = wait.until(EC.element_to_be_clickable((By.ID, "login")))
            try: login_button.click()
            except ElementNotInteractableException:
                self.logger("JS click for login.", "debug"); self.driver.execute_script("arguments[0].click();", login_button)
            
            current_url_before_click = self.driver.current_url; time.sleep(0.5)
            wait.until(EC.any_of(EC.url_changes(current_url_before_click), *[EC.url_contains(k) for k in success_url_keywords]))
            time.sleep(1.5) 

            current_url_lower = self.driver.current_url.lower()
            if any(k in current_url_lower for k in success_url_keywords) and "login" not in current_url_lower and "credentials" not in current_url_lower:
                self.logger("Login successful.", "user"); return True
            else:
                self.logger(f"Login failed. URL: {self.driver.current_url}", "user")
                try:
                    err_el = self.driver.find_element(By.CSS_SELECTOR, "div.notice-message-component.error")
                    if err_el and err_el.is_displayed(): self.logger(f"Login page error: {err_el.text}", "user")
                except NoSuchElementException: pass
                return False
        except TimeoutException: self.logger(f"Login timeout. URL: '{self.driver.current_url if self.driver else 'N/A'}'", "user"); return False
        except Exception as e: self.logger(f"Login error: {e}", "user"); return False #pylint: disable=broad-except

    def _extract_san_from_ply_div(self, ply_div: BeautifulSoup) -> Optional[str]:
        content_span = ply_div.find('span', class_=lambda c: c and ('node-highlight-content' in c or 'move-text-move' in c))
        text_to_parse = ""
        if content_span:
            figurine_element = content_span.find(attrs={"data-figurine": True})
            piece_char = figurine_element['data-figurine'] if figurine_element else ""
            if piece_char == 'P': piece_char = "" 
            parts = [elem.strip() for elem in content_span.descendants if isinstance(elem, NavigableString) and elem.strip()]
            text_content_parts = "".join(parts)
            if text_content_parts and text_content_parts[0].upper() in "KQRBN" and not piece_char: text_to_parse = text_content_parts 
            else: text_to_parse = piece_char + text_content_parts
        else: text_to_parse = ply_div.get_text(separator=' ', strip=True)
        if not text_to_parse: return None
        cleaned = re.sub(r"^\d+\.*\s*|[+#!?]", "", text_to_parse).strip() # Combined cleaning
        m = re.match(r"(Pawn|Knight|Bishop|Rook|Queen|King)\s*([a-h]?[1-8]?x?[a-h][1-8])", cleaned, re.I)
        if m: cleaned = {"Pawn": "", "Knight": "N", "Bishop": "B", "Rook": "R", "Queen": "Q", "King": "K"}[m.group(1).capitalize()] + m.group(2)
        return cleaned if cleaned else None

    def get_scraped_moves(self) -> List[str]:
        if not self.driver: return []
        try:
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            moves_san: List[str] = []
            move_list_wc = soup.find('wc-vertical-move-list')
            if move_list_wc:
                for ply_cand in move_list_wc.find_all('div', class_=['white', 'black'], recursive=True):
                    parent = ply_cand.parent
                    is_variation = False
                    while parent and parent != move_list_wc:
                        if any(cls in parent.get('class', []) for cls in ['variation', 'subline']): is_variation = True; break
                        parent = parent.parent
                    if not is_variation:
                        san = self._extract_san_from_ply_div(ply_cand)
                        if san: moves_san.append(san)
            else: # Fallback
                for turn_row in soup.find_all('div', class_=lambda v: v and 'main-line-row' in v):
                    for ply_div in turn_row.find_all('div', class_=lambda c: c and 'node' in c and any(mc in c for mc in ['white','black','white-move','black-move']) and 'main-line-ply' in c):
                        if not ply_div.find_parent(class_=lambda c: c and 'subline' in c):
                            san = self._extract_san_from_ply_div(ply_div)
                            if san: moves_san.append(san)
            # self.logger(f"Scraped moves ({len(moves_san)}): {moves_san}", "debug")
            return moves_san
        except Exception as e: self.logger(f"Error scraping moves: {e}", "debug"); return [] #pylint: disable=broad-except

    def get_player_clock_time(self, player_color: chess.Color) -> Optional[float]:
        if not self.driver: return None
        try:
            orientation = self.get_board_orientation()
            clock_sel_bottom = "div.clock-bottom div.clock-time-text"
            clock_sel_top = "div.clock-top div.clock-time-text"
            target_sel = ""
            if player_color == chess.WHITE: target_sel = clock_sel_bottom if orientation == "white_bottom" else clock_sel_top
            else: target_sel = clock_sel_bottom if orientation == "black_bottom" else clock_sel_top
            if not target_sel: return None
            time_str = self.driver.find_element(By.CSS_SELECTOR, target_sel).text.strip()
            parts = [float(p) for p in time_str.split(':')]
            return parts[0] * 60 + parts[1] if len(parts) == 2 else parts[0]
        except Exception: return None #pylint: disable=broad-except

    def get_board_orientation(self) -> str: # "white_bottom" or "black_bottom"
        if not self.driver: return "white_bottom" 
        try:
            try: # Check wc-chess-board first
                if "flipped" in self.driver.find_element(By.TAG_NAME, "wc-chess-board").get_attribute("class"): return "black_bottom"
                return "white_bottom"
            except NoSuchElementException: pass # Fallback
            if self.driver.find_element(By.XPATH, "//*[(contains(@id, 'board-') or contains(@class, 'board')) and contains(@class, 'flipped')]"):
                return "black_bottom"
        except Exception: pass #pylint: disable=broad-except
        return "white_bottom" 

    def quit_browser(self) -> None:
        if self.driver:
            try: self.driver.quit()
            except Exception as e: self.logger(f"Error quitting: {e}", "debug") #pylint: disable=broad-except
            finally: self.driver = None