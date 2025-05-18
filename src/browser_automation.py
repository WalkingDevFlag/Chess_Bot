from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementNotInteractableException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup # NavigableString is no longer directly used here
import time
# import re # No longer directly used here
from typing import Optional, List, Callable
import chess

from chess_utils import extract_san_from_ply_div # Import the utility function

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
            # Ensure ChromeDriver is managed or specify executable_path if needed
            try:
                service = ChromeService(ChromeDriverManager().install())
            except Exception as e_cdm:
                self.logger(f"ChromeDriver manager error: {e_cdm}. Ensure Chrome is installed and accessible.", "user")
                # Fallback or re-raise, depending on desired robustness
                # For now, let it raise if CDM fails.
                # Consider adding a manual path option from config if CDM is unreliable.
                raise
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
            wait = WebDriverWait(self.driver, 20) # Increased timeout slightly
            username_field = wait.until(EC.visibility_of_element_located((By.ID, "login-username")))
            username_field.clear(); username_field.send_keys(username)
            password_field = wait.until(EC.visibility_of_element_located((By.ID, "login-password")))
            password_field.clear(); password_field.send_keys(password)
            login_button = wait.until(EC.element_to_be_clickable((By.ID, "login"))) # Changed to ID "login" which is common
            try: login_button.click()
            except ElementNotInteractableException:
                self.logger("JS click for login.", "debug"); self.driver.execute_script("arguments[0].click();", login_button)

            current_url_before_click = self.driver.current_url; time.sleep(0.5) # Wait for potential immediate redirect
            # Wait for URL to change OR contain a success keyword (robust for different login flows)
            wait.until(EC.any_of(EC.url_changes(current_url_before_click), *[EC.url_contains(k) for k in success_url_keywords]))
            time.sleep(1.5) # Allow page to fully load after redirect

            current_url_lower = self.driver.current_url.lower()
            if any(k in current_url_lower for k in success_url_keywords) and "login" not in current_url_lower and "credentials" not in current_url_lower:
                self.logger("Login successful.", "user"); return True
            else:
                self.logger(f"Login failed. URL: {self.driver.current_url}", "user")
                try: # Try to find a generic error message element
                    err_el = self.driver.find_element(By.CSS_SELECTOR, "div.notice-message-component.error") # chess.com specific example
                    if err_el and err_el.is_displayed(): self.logger(f"Login page error: {err_el.text}", "user")
                except NoSuchElementException: pass
                return False
        except TimeoutException: self.logger(f"Login timeout. URL: '{self.driver.current_url if self.driver else 'N/A'}'", "user"); return False
        except Exception as e: self.logger(f"Login error: {e}", "user"); return False #pylint: disable=broad-except

    # _extract_san_from_ply_div has been moved to chess_utils.py

    def get_scraped_moves(self) -> List[str]:
        if not self.driver: return []
        try:
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            moves_san: List[str] = []
            # Try the wc-vertical-move-list structure first (common on newer chess.com UI)
            move_list_wc = soup.find('wc-vertical-move-list')
            if move_list_wc:
                # Find all divs that are direct children representing plies (white or black class)
                # and are not part of a variation.
                for ply_cand in move_list_wc.find_all('div', class_=['white', 'black'], recursive=True): # recursive to catch nested structure
                    parent = ply_cand.parent
                    is_variation = False
                    # Traverse up to see if any parent is a variation container until move_list_wc
                    while parent and parent != move_list_wc:
                        if any(cls in parent.get('class', []) for cls in ['variation', 'subline']): # common classes for variations
                            is_variation = True; break
                        parent = parent.parent
                    if not is_variation:
                        san = extract_san_from_ply_div(ply_cand) # Use the utility function
                        if san: moves_san.append(san)
            else: # Fallback to a more general structure if wc-vertical-move-list is not found
                # This fallback might need adjustment based on the actual HTML structure encountered.
                # Looking for rows and then nodes within them.
                for turn_row in soup.find_all('div', class_=lambda v: v and 'main-line-row' in v): # Example class
                    for ply_div in turn_row.find_all('div', class_=lambda c: c and 'node' in c and any(mc in c for mc in ['white','black','white-move','black-move']) and 'main-line-ply' in c): # More specific ply class
                        # Ensure it's not a subline/variation by checking parents
                        if not ply_div.find_parent(class_=lambda c: c and 'subline' in c): # Example variation class
                            san = extract_san_from_ply_div(ply_div) # Use the utility function
                            if san: moves_san.append(san)
            # self.logger(f"Scraped moves ({len(moves_san)}): {moves_san}", "debug")
            return moves_san
        except Exception as e: self.logger(f"Error scraping moves: {e}", "debug"); return [] #pylint: disable=broad-except

    def get_player_clock_time(self, player_color: chess.Color) -> Optional[float]:
        if not self.driver: return None
        try:
            orientation = self.get_board_orientation()
            # CSS selectors for clock elements on chess.com (may need updates if site changes)
            clock_sel_bottom = "div.clock-bottom div.clock-time-text" # Player at bottom of screen
            clock_sel_top = "div.clock-top div.clock-time-text"     # Player at top of screen
            target_sel = ""

            if player_color == chess.WHITE:
                target_sel = clock_sel_bottom if orientation == "white_bottom" else clock_sel_top
            else: # player_color == chess.BLACK
                target_sel = clock_sel_bottom if orientation == "black_bottom" else clock_sel_top
            
            if not target_sel: return None # Should not happen if orientation is valid

            time_str = self.driver.find_element(By.CSS_SELECTOR, target_sel).text.strip()
            parts = [float(p) for p in time_str.split(':')]
            if len(parts) == 2: return parts[0] * 60 + parts[1] # M:S format
            if len(parts) == 1: return parts[0] # S format (e.g., during increment)
            # Potentially handle H:M:S if necessary, though less common in online blitz/bullet
            return None 
        except Exception: return None #pylint: disable=broad-except


    def get_board_orientation(self) -> str: # "white_bottom" or "black_bottom"
        if not self.driver: return "white_bottom" # Default assumption
        try:
            # Check for 'flipped' class on newer wc-chess-board component
            try:
                board_element = self.driver.find_element(By.TAG_NAME, "wc-chess-board")
                if "flipped" in board_element.get_attribute("class"):
                    return "black_bottom"
                return "white_bottom"
            except NoSuchElementException:
                pass # Fallback to older method if wc-chess-board not found

            # Fallback: Check for a general board element with a 'flipped' class
            # This XPath looks for any element with 'board' in its id or class, and also class 'flipped'
            if self.driver.find_element(By.XPATH, "//*[(contains(@id, 'board-') or contains(@class, 'board')) and contains(@class, 'flipped')]"):
                return "black_bottom"
        except Exception: #pylint: disable=broad-except
            # If any error occurs, default to white at the bottom
            pass
        return "white_bottom" # Default if no specific 'flipped' state is found

    def quit_browser(self) -> None:
        if self.driver:
            try: self.driver.quit()
            except Exception as e: self.logger(f"Error quitting: {e}", "debug") #pylint: disable=broad-except
            finally: self.driver = None