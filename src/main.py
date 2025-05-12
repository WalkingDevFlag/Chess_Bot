import customtkinter as ctk
from tkinter import messagebox
import os

from ui import ChessApp 
from config import CHESS_USERNAME, CHESS_PASSWORD, BASE_DIR

if __name__ == "__main__":
    dotenv_full_path = os.path.join(BASE_DIR, ".env")
    if not CHESS_USERNAME or not CHESS_PASSWORD:
        print(f"CRITICAL: Credentials not in .env (expected at {dotenv_full_path}).")
        try:
            temp_root = ctk.CTk(); temp_root.withdraw()
            messagebox.showerror("Config Error", f"Credentials not in .env (expected at {dotenv_full_path}). Create and restart.")
            temp_root.destroy()
        except Exception: pass # pylint: disable=broad-except
    app = ChessApp()
    app.mainloop()