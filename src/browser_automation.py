from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementNotInteractableException
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup, NavigableString
import time
import re
from typing import Optional, List, Callable

class BrowserManager:
    """
    Manages Selenium WebDriver interactions with chess.com.
    """
    def __init__(self, logger_func: Callable[[str, str], None]):
        """
        Initializes the BrowserManager.

        Args:
            logger_func: A callable for logging messages, accepting (message, log_type).
        """
        self.driver: Optional[webdriver.Chrome] = None
        self.logger: Callable[[str, str], None] = logger_func

    def open_browser(self, url: str = "https://www.chess.com", incognito: bool = True) -> bool: # Added incognito flag
        """
        Opens the browser and navigates to the given URL.

        Args:
            url: The URL to navigate to.
            incognito: If True, opens the browser in Incognito mode.
        
        Returns:
            True if the browser was opened/managed successfully, False otherwise.
        """
        if self.driver:
            self.logger("Browser already open. Focusing existing window.", log_type="user")
            try: 
                self.driver.switch_to.window(self.driver.current_window_handle)
            except Exception:
                self.logger("Could not focus existing browser window.", log_type="debug")
            return True

        try:
            self.logger(f"Opening browser (Incognito: {incognito})...", log_type="user") # Updated log
            options = webdriver.ChromeOptions()
            options.add_experimental_option('excludeSwitches', ['enable-logging'])
            
            if incognito:
                options.add_argument("--incognito") # <<<<<<<<<<<< ADDED THIS LINE FOR INCOGNITO
            
            # Add other options if needed (headless, window-size, etc.)
            # options.add_argument("--headless") 
            
            service = ChromeService(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            self.driver.get(url)
            self.logger(f"{url} opened successfully.", log_type="user")
            return True
        except Exception as e:
            self.logger(f"Error opening browser: {e}", log_type="user")
            self.driver = None 
            return False

    def login(self, username: Optional[str], password: Optional[str], 
              login_url: str = "https://www.chess.com/login",
              success_url_keywords: List[str] = ["/home", "/play/online", "/member/", "/today"]) -> bool:
        """Logs into chess.com."""
        if not self.driver:
            self.logger("Browser not open. Cannot login.", log_type="user")
            return False
        if not username or not password:
            self.logger("Username or Password not provided for login.", log_type="user")
            return False

        try:
            self.logger("Attempting to login to chess.com...", log_type="user")
            self.logger(f"Navigating to login page: {login_url}", log_type="debug")
            self.driver.get(login_url)
            
            wait = WebDriverWait(self.driver, 20)

            self.logger("Waiting for username field...", log_type="debug")
            username_field = wait.until(EC.visibility_of_element_located((By.ID, "login-username")))
            username_field.clear()
            username_field.send_keys(username)
            self.logger("Username entered.", log_type="debug")

            self.logger("Waiting for password field...", log_type="debug")
            password_field = wait.until(EC.visibility_of_element_located((By.ID, "login-password")))
            password_field.clear()
            password_field.send_keys(password)
            self.logger("Password entered.", log_type="debug")

            self.logger("Waiting for login button to be clickable...", log_type="debug")
            login_button = wait.until(EC.element_to_be_clickable((By.ID, "login")))
            
            self.logger("Attempting to click login button...", log_type="debug")
            try:
                login_button.click()
            except ElementNotInteractableException:
                self.logger("Standard click failed (ElementNotInteractable). Trying JavaScript click.", log_type="debug")
                self.driver.execute_script("arguments[0].click();", login_button)

            self.logger("Waiting for login to complete and redirect...", log_type="debug")
            expected_conditions = [EC.url_contains(keyword) for keyword in success_url_keywords]
            wait.until(EC.any_of(*expected_conditions))
            
            time.sleep(1) 

            current_url_lower = self.driver.current_url.lower()
            if any(keyword in current_url_lower for keyword in success_url_keywords) and \
               "login" not in current_url_lower and "credentials" not in current_url_lower :
                self.logger("Login successful.", log_type="user")
                return True
            else:
                self.logger(f"Login may have failed. Current URL: {self.driver.current_url}", log_type="user")
                return False

        except TimeoutException:
            self.logger(f"Login error: Timeout. Current URL: '{self.driver.current_url if self.driver else 'N/A'}'", log_type="user")
            return False
        except Exception as e:
            self.logger(f"An unexpected error occurred during login: {e}", log_type="user")
            return False

    def _extract_san_from_ply_div(self, ply_div: BeautifulSoup) -> Optional[str]:
        """Extracts SAN from a single ply div element."""
        highlight_span = ply_div.find('span', class_='node-highlight-content')
        if not highlight_span:
            raw_text = ply_div.get_text(strip=True)
            cleaned_text = re.sub(r"^\d+\.*\s*", "", raw_text).strip()
            return cleaned_text if cleaned_text else None
        
        figurine_span = highlight_span.find('span', class_='icon-font-chess')
        piece_char_from_data = ''
        if figurine_span and 'data-figurine' in figurine_span.attrs:
            piece_char_from_data = figurine_span['data-figurine']
        if piece_char_from_data == 'P': 
            piece_char_from_data = ''
            
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
        elif piece_char_from_data: 
            san = piece_char_from_data + move_detail_from_text
        else: 
            san = move_detail_from_text
            
        if san: 
            san = san.replace('+', '').replace('#', '').replace('!', '').replace('?', '')
        return san if san else None

    def get_scraped_moves(self) -> List[str]:
        """Scrapes moves from the current chess.com game page."""
        if not self.driver:
            self.logger("Browser not open, cannot scrape moves.", log_type="debug")
            return []
        try:
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            moves_san: List[str] = []

            turn_rows = soup.find_all('div', class_=lambda value: value and 'main-line-row' in value and 'move-list-row' in value)
            
            if turn_rows:
                self.logger(f"Found {len(turn_rows)} 'main-line-row move-list-row' (turn rows).", log_type="debug")
                for turn_row_div in turn_rows:
                    ply_divs_in_row = turn_row_div.find_all('div', class_=lambda c: c and 'node' in c.split() and ('white-move' in c.split() or 'black-move' in c.split()) and 'main-line-ply' in c.split())
                    for ply_div in ply_divs_in_row:
                        if ply_div.find_parent(class_=lambda c: c and 'subline' in c.split()):
                            continue 
                        san = self._extract_san_from_ply_div(ply_div)
                        if san:
                            moves_san.append(san)
            else:
                self.logger("No 'main-line-row' (turn rows) found. Trying global ply search.", log_type="debug")
                ply_divs_global = soup.find_all('div', class_=lambda c: c and 'node' in c.split() and ('white-move' in c.split() or 'black-move' in c.split()) and 'main-line-ply' in c.split())
                if ply_divs_global:
                    self.logger(f"Global Fallback: Found {len(ply_divs_global)} 'node main-line-ply' elements.", log_type="debug")
                    for ply_div in ply_divs_global:
                        if not ply_div.find_parent(class_=lambda c: c and 'subline' in c.split()):
                            san = self._extract_san_from_ply_div(ply_div)
                            if san:
                                moves_san.append(san)
                else:
                    self.logger("Global ply search failed. Trying 'wc-vertical-move-list'.", log_type="debug")
                    move_list_wc = soup.find('wc-vertical-move-list')
                    if move_list_wc:
                        self.logger("Found 'wc-vertical-move-list'. Processing its children.", log_type="debug")
                        potential_plies = move_list_wc.find_all('div', class_=['white', 'black'], recursive=True)
                        for ply_candidate in potential_plies:
                            is_subline = False; parent = ply_candidate.parent
                            while parent and parent != move_list_wc:
                                if 'subline' in parent.get('class', []): is_subline = True; break
                                parent = parent.parent
                            if is_subline: continue
                            san = self._extract_san_from_ply_div(ply_candidate) 
                            if san: moves_san.append(san)
                    else:
                        self.logger("No moves found with any known selector.", log_type="debug")
            
            if not moves_san:
                 self.logger("No moves extracted from page.", log_type="debug")
            else:
                self.logger(f"Final Scraped moves: {moves_san}", log_type="debug")
            return moves_san
        except Exception as e:
            self.logger(f"Error scraping moves: {e}", log_type="debug")
            return []

    def quit_browser(self) -> None:
        """Quits the WebDriver if it's running."""
        if self.driver:
            self.logger("Quitting browser.", log_type="debug")
            try:
                self.driver.quit()
            except Exception as e:
                self.logger(f"Error quitting browser: {e}", log_type="debug")
            finally:
                self.driver = None