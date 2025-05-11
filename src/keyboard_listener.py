# keyboard_listener.py
# No changes needed for this request.
import threading
from pynput import keyboard
from typing import Callable, Optional

class KeyboardListener:
    def __init__(self, key_to_listen: str, callback: Callable[[], None], logger_func: Callable[[str, str], None]):
        self.key_to_listen_str = key_to_listen.lower()
        self.callback = callback
        self.logger = logger_func
        self.listener_thread: Optional[threading.Thread] = None
        self.keyboard_listener_obj: Optional[keyboard.Listener] = None
        self._stop_event = threading.Event()
        self.target_key = None
        try:
            self.target_key = getattr(keyboard.Key, self.key_to_listen_str)
        except AttributeError:
            if len(self.key_to_listen_str) == 1:
                self.target_key = keyboard.KeyCode.from_char(self.key_to_listen_str)
            else: raise ValueError(f"Invalid failsafe key: {self.key_to_listen_str}")

    def _on_press(self, key):
        try:
            pressed_key = None
            if isinstance(key, keyboard.Key): pressed_key = key
            elif isinstance(key, keyboard.KeyCode) and key.char: pressed_key = keyboard.KeyCode.from_char(key.char.lower())
            if pressed_key == self.target_key:
                self.logger(f"Failsafe '{self.key_to_listen_str.upper()}' pressed.", "user")
                if self.callback: self.callback()
        except Exception as e: self.logger(f"Error in key listener _on_press: {e}", "debug") # pylint: disable=broad-except

    def _listener_loop(self):
        try:
            with keyboard.Listener(on_press=self._on_press) as self.keyboard_listener_obj:
                self._stop_event.wait() 
                if self.keyboard_listener_obj and self.keyboard_listener_obj.running: self.keyboard_listener_obj.stop()
        except Exception as e: self.logger(f"Exception in kbd listener thread: {e}", "debug") # pylint: disable=broad-except
        finally: self.logger("Keyboard listener thread finished.", "debug")

    def start(self):
        if not self.listener_thread or not self.listener_thread.is_alive():
            if not self.target_key: self.logger("Cannot start kbd listener: invalid key.", "user"); return
            self._stop_event.clear()
            self.listener_thread = threading.Thread(target=self._listener_loop, daemon=True)
            self.listener_thread.start()
            self.logger(f"Keyboard listener started for '{self.key_to_listen_str}'.", "debug")

    def stop(self):
        self.logger("Stopping keyboard listener...", "debug")
        self._stop_event.set() 
        if self.listener_thread and self.listener_thread.is_alive():
            self.listener_thread.join(timeout=1.0)
        self.listener_thread = None; self.keyboard_listener_obj = None
        self.logger("Keyboard listener stopped.", "debug")