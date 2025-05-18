import time
import random
import chess
from typing import Callable, Optional, Tuple

from chess_utils import uci_to_screen_coords
import input_automation

class AutoPlayer:
    def __init__(self,
                 engine_communicator,
                 internal_board_ref: chess.Board,
                 update_internal_board_cb: Callable[[], bool],
                 add_to_output_cb: Callable[[str, str], None],
                 get_player_clock_cb: Callable[[chess.Color], Optional[float]],
                 get_board_orientation_cb: Callable[[], str]
                ):
        self.engine_comm = engine_communicator
        self.internal_board = internal_board_ref # This board's turn is the perspective of the FEN sent
        self.update_internal_board = update_internal_board_cb
        self.logger = add_to_output_cb
        self.get_player_clock = get_player_clock_cb
        self.get_board_orientation = get_board_orientation_cb

        self.is_playing: bool = False
        self.game_mode: Optional[str] = None
        self.bot_color: Optional[chess.Color] = None # The color the bot is playing as
        self.ui_update_on_stop_cb: Optional[Callable[[], None]] = None

    # ... (set_ui_update_on_stop_cb, _get_move_delay_and_engine_time, _make_move_on_screen, start_playing, stop_playing are unchanged) ...
    def set_ui_update_on_stop_cb(self, cb: Callable[[], None]):
        self.ui_update_on_stop_cb = cb

    def _get_move_delay_and_engine_time(self, remaining_time_s: Optional[float]) -> Tuple[float, int]:
        pre_move_action_delay: float
        engine_movetime_ms: int
        is_low_time = remaining_time_s is not None and remaining_time_s < 20

        if self.game_mode == "bullet":
            engine_movetime_ms = random.randint(70, 120)
            base_delay_min, base_delay_max = (0.05, 0.20) if is_low_time else (0.15, 0.40)
        elif self.game_mode == "blitz":
            engine_movetime_ms = random.randint(150, 400)
            base_delay_min, base_delay_max = (0.1, 0.5) if is_low_time else (2.0, 7.0)
        else: # Default fallback
            engine_movetime_ms = 500
            base_delay_min, base_delay_max = (0.5, 1.0)

        pre_move_action_delay = random.uniform(base_delay_min, base_delay_max)
        pre_move_action_delay = max(0.01, pre_move_action_delay)

        self.logger(f"Mode: {self.game_mode}, Clock: {remaining_time_s if remaining_time_s is not None else 'N/A'}. "
                    f"Human Delay: {pre_move_action_delay:.2f}s, Engine Time: {engine_movetime_ms}ms", "debug")
        return pre_move_action_delay, engine_movetime_ms

    def _make_move_on_screen(self, from_sq_coord: Tuple[int, int], to_sq_coord: Tuple[int, int]):
        try:
            self.logger(f"Performing screen move from {from_sq_coord} to {to_sq_coord}", "debug")
            input_automation.perform_mouse_action_at(
                from_sq_coord[0], from_sq_coord[1], action="move_and_click"
            )
            time.sleep(random.uniform(0.05, 0.12))
            input_automation.perform_mouse_action_at(
                to_sq_coord[0], to_sq_coord[1], action="move_and_click"
            )
            self.logger(f"Screen move executed.", "debug")
        except Exception as e:
            self.logger(f"Error making move on screen: {e}", "user")


    def start_playing(self, mode: str, bot_plays_as_color: chess.Color):
        if self.is_playing: self.logger("AutoPlayer is already playing.", "user"); return
        if not self.engine_comm: self.logger("Engine communicator not available.", "user"); return
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
                    self.logger("Board update failed. Retrying...", "debug")
                    time.sleep(1); continue
                if self.internal_board.is_game_over():
                    self.logger(f"Game over: {self.internal_board.result()}. Stopping auto-play.", "user")
                    break
                
                # Crucial: engine evaluation is from the perspective of self.internal_board.turn
                # For the bot's move, self.internal_board.turn should BE self.bot_color
                if self.internal_board.turn != self.bot_color:
                    time.sleep(0.2); continue

                self.logger(f"Bot's turn ({'White' if self.bot_color == chess.WHITE else 'Black'}). Analyzing...", "debug")
                remaining_time_s = self.get_player_clock(self.bot_color) if self.get_player_clock else None
                pre_move_action_delay, engine_movetime_ms = self._get_move_delay_and_engine_time(remaining_time_s)
                current_fen = self.internal_board.fen()

                best_move_uci, raw_score, is_mate_score = self.engine_comm.get_best_move_and_eval(current_fen, movetime_ms=engine_movetime_ms)

                if not self.is_playing: break

                if best_move_uci and best_move_uci != "(none)":
                    try:
                        move_obj = self.internal_board.parse_uci(best_move_uci)
                        move_san = self.internal_board.san(move_obj)
                        self.logger(f"Engine suggests: {move_san} (UCI: {best_move_uci})", "user")

                        if raw_score is not None:
                            perspective_str = "Bot's Perspective" # Since self.internal_board.turn == self.bot_color here
                            if is_mate_score:
                                if raw_score > 0: # Bot is mating
                                    self.logger(f"Board Evaluation ({perspective_str}): Mate in {raw_score}", "user")
                                else: # Bot is being mated
                                    self.logger(f"Board Evaluation ({perspective_str}): Mated in {abs(raw_score)}", "user")
                            else: # Centipawn score
                                eval_pawn_units = raw_score / 100.0
                                self.logger(f"Board Evaluation ({perspective_str}): {eval_pawn_units:+.2f}", "user")
                        else:
                            self.logger("Board Evaluation: Not available.", "user")

                        coords = uci_to_screen_coords(best_move_uci, self.get_board_orientation, self.logger)
                        if coords:
                            from_coord, to_coord = coords
                            self.logger(f"Making move {best_move_uci} after {pre_move_action_delay:.2f}s delay.", "debug")
                            time.sleep(pre_move_action_delay)
                            if not self.is_playing: break
                            self._make_move_on_screen(from_coord, to_coord)
                            time.sleep(random.uniform(0.2, 0.5))
                        else:
                            self.logger(f"Could not get screen coords for {best_move_uci}. Stopping.", "user"); break
                    except ValueError:
                        self.logger(f"Engine proposed illegal move {best_move_uci} for FEN {current_fen}. Stopping.", "user"); break
                    except Exception as e:
                        self.logger(f"Unexpected error processing/making move {best_move_uci}: {e}", "user"); break
                elif best_move_uci == "(none)": # Game might be over (stalemate, checkmate)
                    self.logger("Engine returned (none) - game might be over or no legal moves. Stopping.", "user")
                    if raw_score is not None: # Log final eval if available
                        perspective_str = "Bot's Perspective"
                        if is_mate_score:
                            if raw_score > 0: self.logger(f"Final Board Evaluation ({perspective_str}): Mate in {raw_score}", "user")
                            else: self.logger(f"Final Board Evaluation ({perspective_str}): Mated in {abs(raw_score)}", "user")
                        else:
                            eval_pawn_units = raw_score / 100.0
                            self.logger(f"Final Board Evaluation ({perspective_str}): {eval_pawn_units:+.2f}", "user")
                    break
                else:
                    self.logger("Engine did not return a valid best move. Stopping.", "user"); break
        except Exception as e:
            self.logger(f"Critical error in auto-play loop: {e}", "user")
        finally:
            self.is_playing = False
            self.logger(f"Auto-play loop for {self.game_mode or 'unknown mode'} terminated.", "debug")
            if self.ui_update_on_stop_cb:
                self.ui_update_on_stop_cb()