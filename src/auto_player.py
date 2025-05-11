# auto_player.py
import pyautogui
import time
import random
import chess
from typing import Callable, Optional, Tuple

# Import specific constants needed by this module directly
from config import BOARD_OFFSET_X, BOARD_OFFSET_Y, SQUARE_PIXEL_SIZE


class AutoPlayer:
    def __init__(self,
                 engine_communicator, 
                 internal_board_ref: chess.Board,
                 update_internal_board_cb: Callable[[], bool],
                 add_to_output_cb: Callable[[str, str], None],
                 get_player_clock_cb: Callable[[chess.Color], Optional[float]],
                 get_board_orientation_cb: Callable[[], str] # Expected to return "white_bottom" or "black_bottom"
                ):
        self.engine_comm = engine_communicator
        self.internal_board = internal_board_ref
        self.update_internal_board = update_internal_board_cb
        self.logger = add_to_output_cb
        self.get_player_clock = get_player_clock_cb
        self.get_board_orientation = get_board_orientation_cb

        self.is_playing: bool = False
        self.game_mode: Optional[str] = None 
        self.bot_color: Optional[chess.Color] = None
        
        self.ui_update_on_stop_cb: Optional[Callable[[], None]] = None
        
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.05   

    def set_ui_update_on_stop_cb(self, cb: Callable[[], None]):
        self.ui_update_on_stop_cb = cb

    def _uci_to_screen_coords(self, uci_move: str) -> Optional[Tuple[Tuple[int, int], Tuple[int, int]]]:
        try:
            move = chess.Move.from_uci(uci_move)
            from_square = move.from_square
            to_square = move.to_square
            player_perspective = self.get_board_orientation() 
            
            if not player_perspective: 
                self.logger("Critical: Could not determine board orientation. Using default.", "debug")
                from config import PLAYER_PERSPECTIVE_DEFAULT_FALLBACK # pylint: disable=import-outside-toplevel
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
                    self.logger(f"Error: Unknown player perspective '{player_perspective}'. Cannot calculate coordinates.", "user")
                    return None
                coords.append((screen_x, screen_y))
            
            return tuple(coords) # type: ignore
        except Exception as e: # pylint: disable=broad-except
            self.logger(f"Error converting UCI '{uci_move}' to screen coordinates: {e}", "debug")
            return None

    def _make_move_on_screen(self, from_sq_coord: Tuple[int, int], to_sq_coord: Tuple[int, int]):
        try:
            # self.logger(f"Clicking from {from_sq_coord} to {to_sq_coord}", "debug") # Reduced verbosity
            pyautogui.moveTo(from_sq_coord[0], from_sq_coord[1], duration=random.uniform(0.05, 0.15))
            pyautogui.click()
            time.sleep(random.uniform(0.05, 0.1)) 
            pyautogui.moveTo(to_sq_coord[0], to_sq_coord[1], duration=random.uniform(0.05, 0.15))
            pyautogui.click()
            # self.logger("Move executed on screen.", "debug") # Reduced verbosity
        except Exception as e: # pylint: disable=broad-except
            self.logger(f"PyAutoGUI error making move: {e}", "user")

    def _get_move_delay_and_engine_time(self, remaining_time_s: Optional[float]) -> Tuple[float, int]:
        pyautogui_pre_move_delay: float
        engine_movetime_ms: int
        is_low_time = remaining_time_s is not None and remaining_time_s < 20 # Threshold for "low time"

        if self.game_mode == "bullet":
            engine_movetime_ms = random.randint(70, 120) 
            # Bullet: Fast delay, even faster when low on time
            base_delay_min, base_delay_max = (0.05, 0.20) if is_low_time else (0.15, 0.40) # Adjusted bullet slightly
        elif self.game_mode == "blitz":
            engine_movetime_ms = random.randint(150, 400) # Engine thinking time for Blitz (0.15s to 0.4s)
            # Blitz: Significantly longer "human" delay when not low on time, faster when low.
            base_delay_min, base_delay_max = (0.1, 0.5) if is_low_time else (2.0, 7.0) # Changed here: 2.0 to 10.0 seconds
        else: # Default fallback (e.g., if game_mode is not set, though it should be)
            engine_movetime_ms = 500
            base_delay_min, base_delay_max = (0.5, 1.0)

        pyautogui_pre_move_delay = random.uniform(base_delay_min, base_delay_max)
        
        self.logger(f"Mode: {self.game_mode}, Clock: {remaining_time_s if remaining_time_s is not None else 'N/A'}. "
                    f"Human Delay: {pyautogui_pre_move_delay:.2f}s, Engine Time: {engine_movetime_ms}ms", "debug")
        return pyautogui_pre_move_delay, engine_movetime_ms

    def start_playing(self, mode: str, bot_plays_as_color: chess.Color):
        if self.is_playing:
            self.logger("AutoPlayer is already playing.", "user"); return
        if not self.engine_comm:
            self.logger("Engine communicator not available for AutoPlayer.", "user"); return
            
        self.is_playing = True
        self.game_mode = mode
        self.bot_color = bot_plays_as_color
        self.logger(f"AutoPlayer started for {mode}. Bot plays as {'White' if self.bot_color == chess.WHITE else 'Black'}.", "user")

    def stop_playing(self):
        if self.is_playing:
            self.is_playing = False 
            self.logger("AutoPlayer instructed to stop.", "user")

    def play_loop(self):
        self.logger(f"Auto-play loop initiated for {self.game_mode}.", "debug")
        try:
            while self.is_playing:
                time.sleep(0.05)
                if not self.update_internal_board():
                    self.logger("Board update failed (all scraped moves failed). Retrying...", "debug")
                    time.sleep(1); continue
                if self.internal_board.is_game_over():
                    self.logger(f"Game over: {self.internal_board.result()}. Stopping auto-play.", "user")
                    break 
                if self.internal_board.turn != self.bot_color:
                    time.sleep(0.2); continue

                # It's our turn
                self.logger(f"Bot's turn ({'White' if self.bot_color == chess.WHITE else 'Black'}). Analyzing...", "debug")
                remaining_time_s: Optional[float] = self.get_player_clock(self.bot_color) if self.get_player_clock else None
                pyautogui_delay, engine_movetime_ms = self._get_move_delay_and_engine_time(remaining_time_s)
                current_fen = self.internal_board.fen()
                best_move_uci = self.engine_comm.get_best_move(current_fen, movetime_ms=engine_movetime_ms)

                if not self.is_playing: break # Check flag again, might have changed during engine thinking

                if best_move_uci and best_move_uci != "(none)":
                    try:
                        move_obj = self.internal_board.parse_uci(best_move_uci) # Validate move
                        move_san = self.internal_board.san(move_obj)
                        self.logger(f"Engine suggests: {move_san} (UCI: {best_move_uci})", "user")
                        coords = self._uci_to_screen_coords(best_move_uci)
                        if coords:
                            from_coord, to_coord = coords
                            self.logger(f"Making move {best_move_uci} after {pyautogui_delay:.2f}s delay.", "debug")
                            time.sleep(pyautogui_delay) 
                            if not self.is_playing: break # Final check before clicking
                            self._make_move_on_screen(from_coord, to_coord)
                            time.sleep(random.uniform(0.2, 0.5)) # Pause for UI to update/opponent
                        else:
                            self.logger(f"Could not get screen coords for {best_move_uci}. Stopping.", "user"); break 
                    except ValueError: # Illegal move from engine
                        self.logger(f"Engine proposed illegal move {best_move_uci} for FEN {current_fen}. Stopping.", "user"); break
                    except Exception as e: # pylint: disable=broad-except
                        self.logger(f"Unexpected error processing/making move {best_move_uci}: {e}", "user"); break
                elif best_move_uci == "(none)":
                    self.logger("Engine returned (none) - game might be over or no legal moves. Stopping.", "user"); break
                else: # Engine timed out or returned empty/invalid string
                    self.logger("Engine did not return a valid best move. Stopping.", "user"); break
        except pyautogui.FailSafeException:
            self.logger("PyAutoGUI FailSafe triggered. Auto-play stopped.", "user")
            self.is_playing = False # Ensure flag is set
        except Exception as e: # pylint: disable=broad-except
            self.logger(f"Critical error in auto-play loop: {e}", "user")
        finally:
            self.is_playing = False 
            self.logger(f"Auto-play loop for {self.game_mode or 'unknown mode'} terminated.", "debug")
            # UI update is handled by ChessApp after this thread joins or via callback in _stop_auto_play_components