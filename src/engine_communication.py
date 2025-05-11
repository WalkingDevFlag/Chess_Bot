# engine_communication.py
# No changes needed for this request.
import subprocess
import time
import os
from typing import Callable, Optional

class ChessEngineCommunicator:
    def __init__(self, engine_path: str, logger_func: Callable[[str, str], None]):
        self.engine_path: str = engine_path
        self.logger: Callable[[str, str], None] = logger_func
        self.engine_process: Optional[subprocess.Popen] = None
        self._start_engine()

    def _start_engine(self) -> None:
        try:
            self.logger(f"Starting chess engine: {self.engine_path}", log_type="debug")
            creationflags = 0
            if os.name == 'nt': creationflags = subprocess.CREATE_NO_WINDOW
            self.engine_process = subprocess.Popen(
                [self.engine_path], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                text=True, bufsize=1, universal_newlines=True, creationflags=creationflags
            )
            self._initialize_uci()
            self.logger("Chess engine started and UCI initialized.", log_type="debug")
        except FileNotFoundError: self.logger(f"ERROR: Engine not found: {self.engine_path}", "debug"); self.engine_process = None; raise
        except OSError as e:
            self.logger(f"ERROR: OSError starting engine: {e}", "debug")
            if hasattr(e, 'winerror') and e.winerror == 193: self.logger("WinError 193: Incompatible executable.", "debug")
            self.engine_process = None; raise
        except Exception as e: # pylint: disable=broad-except
            self.logger(f"ERROR: Failed to start engine: {e}", "debug")
            if self.engine_process: 
                try: self.engine_process.kill()
                except: pass # pylint: disable=bare-except
            self.engine_process = None; raise

    def _initialize_uci(self) -> None:
        if not self.engine_process: return
        self.send_command("uci")
        uci_timeout = time.time() + 10; uciok = False
        while time.time() < uci_timeout:
            if (output := self.read_output_line()) is None: raise Exception("Engine died during UCI handshake.")
            if "uciok" in output: uciok = True; break
        if not uciok: raise Exception("Engine no uciok.")
        self.send_command("isready")
        ready_timeout = time.time() + 10; readyok = False
        while time.time() < ready_timeout:
            if (output := self.read_output_line()) is None: raise Exception("Engine died during isready.")
            if "readyok" in output: readyok = True; break
        if not readyok: raise Exception("Engine no readyok.")
        self.send_command("setoption name Hash value 128") 
        self.send_command("setoption name Threads value 2") 

    def send_command(self, command: str) -> None:
        if self.engine_process and self.engine_process.stdin and not self.engine_process.stdin.closed:
            try:
                self.engine_process.stdin.write(command + "\n"); self.engine_process.stdin.flush()
            except BrokenPipeError: self.logger("ERROR: Broken pipe to engine.", "debug"); self.engine_process = None 
            except Exception as e: self.logger(f"ERROR sending '{command}': {e}", "debug") # pylint: disable=broad-except
        elif self.engine_process and hasattr(self.engine_process.stdin, 'closed') and self.engine_process.stdin.closed:
             self.logger(f"ERROR: Engine stdin closed, cannot send '{command}'.", "debug"); self.engine_process = None

    def read_output_line(self) -> Optional[str]:
        if self.engine_process and self.engine_process.stdout and not self.engine_process.stdout.closed:
            try:
                output_line = self.engine_process.stdout.readline()
                if not output_line and self.engine_process.poll() is not None: return None # Engine terminated
                return output_line.strip()
            except Exception as e: self.logger(f"ERROR reading engine output: {e}", "debug"); return None # pylint: disable=broad-except
        return None

    def get_best_move(self, fen: str, movetime_ms: int = 2000) -> Optional[str]:
        if not self.engine_process or (self.engine_process.poll() is not None):
            self.logger("Engine not running. Attempting restart...", "debug")
            if self.engine_path: 
                try:
                    self._start_engine() 
                    if not self.engine_process or self.engine_process.poll() is not None: return None
                except Exception as e: self.logger(f"Engine restart failed: {e}", "debug"); return None # pylint: disable=broad-except
            else: return None
        self.send_command("ucinewgame"); self.send_command("isready")
        ready_timeout = time.time() + 5; ready = False
        while time.time() < ready_timeout:
            if (out := self.read_output_line()) is None: return None 
            if "readyok" in out: ready = True; break
        if not ready: self.logger("Engine not ready for new game.", "debug"); return None
        self.send_command(f"position fen {fen}"); self.send_command(f"go movetime {movetime_ms}")
        best_move: Optional[str] = None; start_time = time.time()
        timeout_duration = (movetime_ms / 1000.0) + 10 
        while time.time() - start_time < timeout_duration:
            if self.engine_process and self.engine_process.poll() is not None: return None # Engine died
            output = self.read_output_line()
            if output is None: return None
            if output.startswith("bestmove"):
                parts = output.split(); best_move = parts[1] if len(parts) > 1 else None; break
        if not best_move: self.logger(f"No bestmove received/timeout. FEN: {fen}", "debug"); self.send_command("stop")
        return best_move

    def stop_engine(self) -> None:
        if self.engine_process and self.engine_process.poll() is None:
            self.logger("Stopping chess engine...", "debug")
            try:
                self.send_command("quit"); self.engine_process.communicate(timeout=1.5) 
            except Exception: # pylint: disable=broad-except
                try: self.engine_process.kill(); self.engine_process.communicate()
                except Exception: pass # pylint: disable=bare-except
        self.engine_process = None; self.logger("Chess engine stopped.", "debug")