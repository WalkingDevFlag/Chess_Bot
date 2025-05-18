import chess
from typing import Callable, Optional, Tuple
from bs4 import BeautifulSoup, NavigableString # For extract_san_from_ply_div
import re # For extract_san_from_ply_div

# Import specific constants needed by this module directly
from config import BOARD_OFFSET_X, BOARD_OFFSET_Y, SQUARE_PIXEL_SIZE, PLAYER_PERSPECTIVE_DEFAULT_FALLBACK

def uci_to_screen_coords(uci_move: str,
                         get_board_orientation_cb: Callable[[], str],
                         logger: Callable[[str, str], None]) -> Optional[Tuple[Tuple[int, int], Tuple[int, int]]]:
    """
    Converts a UCI move string to screen coordinates for the start and end squares.
    """
    try:
        move = chess.Move.from_uci(uci_move)
        from_square = move.from_square
        to_square = move.to_square
        player_perspective = get_board_orientation_cb()

        if not player_perspective:
            logger("Critical: Could not determine board orientation. Using default.", "debug")
            player_perspective = PLAYER_PERSPECTIVE_DEFAULT_FALLBACK

        coords = []
        for square_index in [from_square, to_square]:
            file_index = chess.square_file(square_index)
            rank_index = chess.square_rank(square_index)
            half_square = SQUARE_PIXEL_SIZE / 2

            if player_perspective == "white_bottom":
                screen_x = BOARD_OFFSET_X + int(file_index * SQUARE_PIXEL_SIZE + half_square)
                screen_y = BOARD_OFFSET_Y + int((7 - rank_index) * SQUARE_PIXEL_SIZE + half_square)
            elif player_perspective == "black_bottom":
                screen_x = BOARD_OFFSET_X + int((7 - file_index) * SQUARE_PIXEL_SIZE + half_square)
                screen_y = BOARD_OFFSET_Y + int(rank_index * SQUARE_PIXEL_SIZE + half_square)
            else:
                logger(f"Error: Unknown player perspective '{player_perspective}'. Cannot calculate coordinates.", "user")
                return None
            coords.append((screen_x, screen_y))

        return tuple(coords) # type: ignore
    except Exception as e: # pylint: disable=broad-except
        logger(f"Error converting UCI '{uci_move}' to screen coordinates: {e}", "debug")
        return None

def extract_san_from_ply_div(ply_div: BeautifulSoup) -> Optional[str]:
    """
    Extracts a SAN move string from a BeautifulSoup div element representing a ply.
    """
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

    # Combined cleaning: remove move numbers, annotations like +, #, !, ?
    cleaned = re.sub(r"^\d+\.*\s*|[+#!?]", "", text_to_parse).strip()

    # Handle piece names like "Pawn e4" or "Knight f3" which might occur if no figurine
    # and direct text includes piece name.
    # This regex aims to convert "Piece square" to "Psquare" (e.g., "Nf3")
    m = re.match(r"(Pawn|Knight|Bishop|Rook|Queen|King)\s*([a-h]?[1-8]?x?[a-h][1-8])", cleaned, re.I)
    if m:
        piece_map = {"Pawn": "", "Knight": "N", "Bishop": "B", "Rook": "R", "Queen": "Q", "King": "K"}
        cleaned = piece_map[m.group(1).capitalize()] + m.group(2)

    return cleaned if cleaned else None