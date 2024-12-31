import customtkinter
#from utils import Chessbot
from trials import Chessbot
import keyboard

# Initialize the Chessbot
bot = Chessbot()
bot.open_browser()

def extract_and_display_fen():
    """Extracts FEN and retrieves the best move from the chess engine."""
    fen = bot.extract_fen()

    if fen:
        print("Generated FEN:", fen)
        bot.display_fen(fen) 

        # best_move = bot.get_best_move() 
        # if best_move:
        #     print("Best Move:", best_move)
        # else:
        #     print("Failed to retrieve best move.")


keyboard.add_hotkey('q', extract_and_display_fen)
print("Press 'q' to extract FEN and get the best move. Press 'esc' to exit.")
keyboard.wait('esc')
bot.close_browser()
