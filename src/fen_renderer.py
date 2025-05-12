from PIL import Image

import os

def render_fen(fen, assets_dir='chess_pieces', output_dir='fen_rendered', board_image='board.png'):
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Load the board image
    board_path = os.path.join(assets_dir, board_image)
    board = Image.open(board_path).convert('RGBA')
    width, height = board.size
    square_size = width // 8
    
    # Prepare a blank overlay
    overlay = Image.new('RGBA', board.size, (255, 255, 255, 0))
    
    # Map FEN characters to filenames
    piece_map = {
        'K': 'wk.png', 'Q': 'wq.png', 'R': 'wr.png',
        'B': 'wb.png', 'N': 'wn.png', 'P': 'wp.png',
        'k': 'bk.png', 'q': 'bq.png', 'r': 'br.png',
        'b': 'bb.png', 'n': 'bn.png', 'p': 'bp.png',
    }
    
    # Iterate over ranks and files
    for rank_idx, rank in enumerate(fen.split()[0].split('/')):
        file_idx = 0
        for c in rank:
            if c.isdigit():
                file_idx += int(c)
            else:
                fn = piece_map[c]
                piece = Image.open(os.path.join(assets_dir, fn)).convert('RGBA')
                piece = piece.resize((square_size, square_size), Image.LANCZOS)
                overlay.paste(piece, (file_idx * square_size, rank_idx * square_size), piece)
                file_idx += 1

    result = Image.alpha_composite(board, overlay)
    out_path = os.path.join(output_dir, f"{fen.replace('/', '_')}.png")
    result.save(out_path)
    print(f"Rendered → {out_path}")

# Example usage
if __name__ == "__main__":
    test_fen = "r3kb1r/pp4pp/2ppp3/3B4/6n1/5N2/PP3PPP/R1B1K2R w KQkq - 0 16"
    render_fen(test_fen)