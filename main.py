import customtkinter
from trial import Chessbot

class GUI:
  def __init__(self, app):
    self.app = app
    self.chess_bot = Chessbot()

    app.geometry("480x480")
    app.title("Cheat Code")
    
    self.button_font = ("Roboto", 16, "bold")

    self.open_browser_btn = customtkinter.CTkButton(app, text = "Open Browser", width=470, height=50, command=self.chess_bot.open_browser, font=self.button_font)
    self.open_browser_btn.pack(anchor = 'w', padx=10, pady=(10, 0)) #fill=customtkinter.X

    self.get_fen_btn = customtkinter.CTkButton(app, text = "Get FEN String", width=470, height=50, command=self.chess_bot.extract_fen, font=self.button_font)
    self.get_fen_btn.pack(anchor = 'w', padx = 10, pady = (10, 0))
      
    # self.show_fen_btn = customtkinter.CTkButton(app, text = "Board", width=470, height=50, command=self.chess_bot.display_fen, font=self.button_font)
    # self.show_fen_btn.pack(anchor = 'w', padx = 10, pady = (10, 0))

    self.get_best_move_btn = customtkinter.CTkButton(app, text="Get Best Move", width=470,height=50,command=self.chess_bot.get_best_move,font=self.button_font)
    self.get_best_move_btn.pack(anchor='w', padx=10, pady=(10, 0))

    self.close_browser_btn = customtkinter.CTkButton(app, text = "Close Browser", width=470, height=50, command=self.chess_bot.close_browser, font=self.button_font)
    self.close_browser_btn.pack(anchor = 'w', padx = 10, pady = (10, 0))


if __name__ == '__main__':
    customtkinter.set_appearance_mode("System")
    customtkinter.set_default_color_theme("blue")
    app = customtkinter.CTk()
    gui = GUI(app)
    app.mainloop()