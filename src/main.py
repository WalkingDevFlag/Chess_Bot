import customtkinter as ctk
from tkinter import messagebox
from ui import ChessApp # Import the ChessApp class from ui.py
from config import CHESS_USERNAME, CHESS_PASSWORD, dotenv_path

if __name__ == "__main__":
    # Initial check for .env configuration
    if not CHESS_USERNAME or not CHESS_PASSWORD:
        # This message will print to console if GUI hasn't started
        print(f"CRITICAL: CHESS_USERNAME or CHESS_PASSWORD not found in .env file (expected at {dotenv_path}).")
        print("Please create a .env file in the application directory with your chess.com credentials.")
        
        # Attempt to show a GUI error if possible, for better user feedback
        try:
            # Need a temporary root to show messagebox if main app isn't up
            temp_root = ctk.CTk()
            temp_root.withdraw() # Hide the temp root window
            messagebox.showerror(
                "Configuration Error",
                "CHESS_USERNAME or CHESS_PASSWORD not set in .env file.\n"
                "Please create a .env file in the application directory and restart."
            )
            temp_root.destroy()
        except Exception as e:
            print(f"Could not display GUI error message: {e}")
        # exit(1) # Optionally exit if config is critical for startup

    # Create and run the application
    app = ChessApp()
    app.mainloop()