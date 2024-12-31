import tkinter as tk
from tkinter import messagebox

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

from bs4 import BeautifulSoup
import chess


class Chessbot:
    def __init__(self):
        self.driver = None
        self.board = chess.Board()

    def open_browser(self):
        """
        Opens a browser and navigates to chess.com.
        """
        self.driver = webdriver.Chrome()
        page_source = "https://chess.com"
        self.driver.get(page_source)
        self.driver.implicitly_wait(0.5)

    def close_browser(self):
        """
        Closes a browser.
        """
        root = tk.Tk()
        root.withdraw()
        if messagebox.askyesno("Confirm Exit", "Do you really want to quit the browser?"):
            print("Quitting the browser...")
            self.driver.quit()
        else:
            print("Browser will remain open.")

    def color(self):
        """
        Determines whether the current chess piece color is white or black based on the board.
        Returns the color as a string ('white' or 'black') or None if no board is found.
        """
        all_squares = None

        try:
            # Try to find the board element for playing against the computer
            coordinates = self.driver.find_element(By.XPATH, "//*[@id='board-play-computer']//*[name()='svg']")
            all_squares = coordinates.find_elements(By.XPATH, ".//*")
        except NoSuchElementException:
            try:
                # Try to find the board element for single-player mode
                coordinates = self.driver.find_elements(By.XPATH, "//*[@id='board-single']//*[name()='svg']")
                coordinates = [x for x in coordinates if x.get_attribute("class") == "coordinates"][0]
                all_squares = coordinates.find_elements(By.XPATH, ".//*")
            except NoSuchElementException:
                return None

        elem = None
        x_pos = None
        y_pos = None

        for i in range(len(all_squares)):
            name_element = all_squares[i]
            x = float(name_element.get_attribute("x"))
            y = float(name_element.get_attribute("y"))

            if i == 0 or (x <= x_pos and y >= y_pos):
                x_pos = x
                y_pos = y
                elem = name_element

        if elem is not None and elem.text == "1":
            print("white")
            return "white"
        elif elem is not None:
            print("black")
            return "black"

        return None



    def extract_fen(self):
        """
        Extracts the FEN string representing the current board state, considering the player's color.
        Returns the FEN string if successful, otherwise None.
        """
        try:
            # Fetch board HTML content
            board_html = self.driver.find_element(By.XPATH, '//*[@id="board-play-computer"] | //*[@id="board-single"]').get_attribute("outerHTML")
            soup = BeautifulSoup(board_html, "html.parser")
            pieces = soup.find_all("div", class_="piece")

            piece_map = {
                "br": "r", "bn": "n", "bb": "b", "bq": "q", "bk": "k", "bp": "p",
                "wr": "R", "wn": "N", "wb": "B", "wq": "Q", "wk": "K", "wp": "P"
            }

            # Initialize an empty 8x8 board
            board = [["" for _ in range(8)] for _ in range(8)]

            for piece in pieces:
                piece_class = piece.get("class", [])
                square_class = [cls for cls in piece_class if cls.startswith("square-")]

                if len(piece_class) > 1 and square_class:
                    piece_type = piece_map.get(piece_class[1], "")
                    square = square_class[0].split("-")[1]
                    col = int(square[1]) - 1 
                    row = 8 - int(square[0]) 

                    if piece_type:
                        board[row][col] = piece_type

            # Rotate the board 90 degrees to the right
            rotated_board = [["" for _ in range(8)] for _ in range(8)]
            for r in range(8):
                for c in range(8):
                    rotated_board[c][7 - r] = board[r][c]

            # Generate the FEN rows from the rotated board
            fen_rows = []
            for row in rotated_board:
                empty_count = 0
                fen_row = ""
                for square in row:
                    if square == "":
                        empty_count += 1
                    else:
                        if empty_count > 0:
                            fen_row += str(empty_count)
                            empty_count = 0
                        fen_row += square
                if empty_count > 0:
                    fen_row += str(empty_count)
                fen_rows.append(fen_row)

            # Determine the turn from the player's color
            player_color = self.color()
            if player_color == "white":
                turn = "w"
            elif player_color == "black":
                turn = "b"
            else:
                print("Failed to determine player color.")
                return None

            # Construct the complete FEN string
            fen = "/".join(fen_rows) + f" {turn} - - 0 1"
            print(f"Extracted FEN: {fen}")
            return fen

        except NoSuchElementException:
            print("Failed to extract FEN: No board element found.")
            return None


    def display_fen(self, fen):
        """
        Displays the chess board in the terminal using the given FEN string.
        """
        try:
            board = chess.Board(fen)
            print("\nCurrent Board Representation:")
            print(board)
        except ValueError as e:
            print(f"Invalid FEN string provided: {e}")


        # def get_board(self):
    #     """
    #     Retrieves the chess board element from the webpage.
    #     Returns the board element if found, otherwise returns None.
    #     """
    #     try:
    #         board = self.driver.find_element(By.XPATH, "//*[@id='board-play-computer']")
    #         print("Found board for playing against computer.")
    #         return board
    #     except NoSuchElementException:
    #         try:
    #             board = self.driver.find_element(By.XPATH, '//*[@id="board-single"]')
    #             print("Found single-player mode board.")
    #             return board
    #         except NoSuchElementException:
    #             print("No chess board found.")
    #             return None