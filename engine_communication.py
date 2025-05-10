import subprocess
import time
import os
from typing import Callable, Optional

class ChessEngineCommunicator:
    """
    Manages communication with a UCI-compliant chess engine.
    """
    def __init__(self, engine_path: str, logger_func: Callable[[str, str], None]):
        """
        Initializes the ChessEngineCommunicator.

        Args:
            engine_path: Absolute path to the chess engine executable.
            logger_func: A callable for logging messages, accepting (message, log_type).
        """
        self.engine_path: str = engine_path
        self.logger: Callable[[str, str], None] = logger_func
        self.engine_process: Optional[subprocess.Popen] = None
        self._start_engine()

    def _start_engine(self) -> None:
        """Starts the chess engine subprocess."""
        try:
            self.logger(f"Starting chess engine: {self.engine_path}", log_type="debug")
            creationflags = 0
            if os.name == 'nt': # For Windows, hide the console window
                creationflags = subprocess.CREATE_NO_WINDOW
            
            self.engine_process = subprocess.Popen(
                [self.engine_path],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, # Capture stderr for debugging engine startup issues
                text=True,
                bufsize=1,  # Line buffered
                universal_newlines=True,
                creationflags=creationflags
            )
            self._initialize_uci()
            self.logger("Chess engine started and UCI initialized.", log_type="debug")
        except FileNotFoundError:
            self.logger(f"ERROR: Engine executable not found at {self.engine_path}", log_type="debug")
            self.engine_process = None
            raise
        except OSError as e:
            self.logger(f"ERROR: OSError while trying to start engine: {e}", log_type="debug")
            if hasattr(e, 'winerror') and e.winerror == 193: # Specific Windows error for incompatible executable
                self.logger("This error (WinError 193) often means the engine executable is not compatible with your Windows OS (e.g., Linux build on Windows).", log_type="debug")
            self.engine_process = None
            raise
        except Exception as e:
            self.logger(f"ERROR: Failed to start engine process: {e}", log_type="debug")
            if self.engine_process: # Attempt to clean up if Popen succeeded but initialization failed
                try: self.engine_process.kill()
                except: pass # Ignore errors during kill
            self.engine_process = None
            raise

    def _initialize_uci(self) -> None:
        """Sends initial UCI commands to the engine."""
        if not self.engine_process:
            self.logger("Engine process not running, cannot send UCI.", log_type="debug")
            return

        self.send_command("uci")
        uci_handshake_timeout = time.time() + 10  # 10 seconds timeout
        uciok_received = False
        while time.time() < uci_handshake_timeout:
            output = self.read_output_line()
            if output is None:
                self.logger("ERROR: No output from engine during UCI handshake or engine terminated.", log_type="debug")
                raise Exception("Engine terminated or did not respond to UCI.")
            # No need to log 'Engine UCI Init: {output}' here, read_output_line does it.
            if "uciok" in output:
                uciok_received = True
                break
        if not uciok_received:
            self.logger("ERROR: Timeout waiting for 'uciok' from engine.", log_type="debug")
            raise Exception("Engine did not respond with 'uciok'.")

        self.send_command("isready")
        isready_timeout = time.time() + 10
        readyok_received = False
        while time.time() < isready_timeout:
            ready_output = self.read_output_line()
            if ready_output is None:
                self.logger("ERROR: No output from engine during isready or engine terminated.", log_type="debug")
                raise Exception("Engine terminated or did not respond to isready.")
            if "readyok" in ready_output:
                readyok_received = True
                break
        if not readyok_received:
            self.logger("ERROR: Timeout waiting for 'readyok' from engine.", log_type="debug")
            raise Exception("Engine did not respond with 'readyok'.")
        
        # Example: Set a common UCI option. Adjust as needed for Ethereal.
        self.send_command("setoption name Hash value 32") 

    def send_command(self, command: str) -> None:
        """Sends a command string to the engine's stdin."""
        if self.engine_process and self.engine_process.stdin and not self.engine_process.stdin.closed:
            try:
                self.logger(f"To Engine: {command}", log_type="debug")
                self.engine_process.stdin.write(command + "\n")
                self.engine_process.stdin.flush()
            except BrokenPipeError:
                self.logger("ERROR: Broken pipe. Engine may have crashed or stdin closed.", log_type="debug")
                self.engine_process = None # Mark as dead
            except Exception as e:
                self.logger(f"ERROR sending command '{command}': {e}", log_type="debug")
                self.engine_process = None # Consider it potentially unstable
        elif self.engine_process and hasattr(self.engine_process.stdin, 'closed') and self.engine_process.stdin.closed:
             self.logger(f"ERROR: Cannot send command '{command}', engine stdin is closed.", log_type="debug")
             self.engine_process = None


    def read_output_line(self) -> Optional[str]:
        """Reads a single line of output from the engine's stdout."""
        if self.engine_process and self.engine_process.stdout and not self.engine_process.stdout.closed:
            try:
                output_line = self.engine_process.stdout.readline()
                # Check if process terminated while trying to read
                if not output_line and self.engine_process.poll() is not None:
                    self.logger("Engine process terminated while expecting output.", log_type="debug")
                    return None
                output = output_line.strip()
                if output: # Log only if there's actual output
                    self.logger(f"From Engine: {output}", log_type="debug")
                return output
            except Exception as e:
                self.logger(f"ERROR reading engine output: {e}", log_type="debug")
                return None # Indicate error or end of stream
        return None

    def get_best_move(self, fen: str, movetime_ms: int = 2000) -> Optional[str]:
        """
        Requests the best move from the engine for a given FEN position.

        Args:
            fen: The FEN string of the current board position.
            movetime_ms: Time in milliseconds for the engine to think.

        Returns:
            The best move in UCI format (e.g., "e2e4"), or None if an error occurs.
        """
        if not self.engine_process or (self.engine_process.poll() is not None): # Check if process is running
            self.logger("Engine not running or has terminated. Cannot get best move.", log_type="debug")
            # Attempt to restart if it was previously initialized but now dead
            if self.engine_path and self.engine_process and self.engine_process.poll() is not None:
                self.logger("Attempting to restart the engine...", log_type="debug")
                try:
                    self._start_engine() # Try to restart
                    if not self.engine_process or self.engine_process.poll() is not None:
                        self.logger("Engine restart failed.", log_type="debug")
                        return None
                except Exception as e:
                    self.logger(f"Engine restart failed: {e}", log_type="debug")
                    return None
            else:
                return None # If no path or never started, don't try to restart

        self.send_command("ucinewgame") # Good practice for some engines before a new position
        self.send_command("isready")
        ready_timeout = time.time() + 5
        is_engine_ready = False
        while time.time() < ready_timeout:
            output = self.read_output_line()
            if output is None: return None # Engine died
            if "readyok" in output:
                is_engine_ready = True
                break
        if not is_engine_ready:
            self.logger("Engine not ready after ucinewgame. Aborting get_best_move.", log_type="debug")
            return None
        
        self.send_command(f"position fen {fen}")
        self.send_command(f"go movetime {movetime_ms}")

        best_move: Optional[str] = None
        search_start_time = time.time()
        # Generous timeout: movetime + buffer for communication and engine overhead
        search_wait_timeout_duration = (movetime_ms / 1000.0) + 10 

        while True:
            if time.time() - search_start_time > search_wait_timeout_duration:
                self.logger(f"ERROR: Timeout ({search_wait_timeout_duration:.1f}s) waiting for 'bestmove' from engine.", log_type="debug")
                self.send_command("stop") # Try to stop the search gracefully
                return None # Or handle as error

            output = self.read_output_line()
            if output is None: # Engine might have crashed
                self.logger("ERROR: Engine stream ended unexpectedly while waiting for bestmove.", log_type="debug")
                return None
            
            if output.startswith("bestmove"):
                parts = output.split()
                if len(parts) > 1:
                    best_move = parts[1]
                # Potentially ponder move in parts[3] if engine supports it and you want to use it
                break
            # Optionally, parse "info" lines here if you want to display engine analysis depth, score, etc.
        
        return best_move

    def stop_engine(self) -> None:
        """Stops the engine process gracefully if possible, otherwise kills it."""
        if self.engine_process:
            self.logger("Stopping chess engine...", log_type="debug")
            if self.engine_process.poll() is None: # If still running
                try:
                    self.send_command("quit")
                    # Wait for a short period for the engine to quit gracefully
                    self.engine_process.communicate(timeout=3) # Reads remaining output, waits
                except subprocess.TimeoutExpired:
                    self.logger("Engine did not quit gracefully, killing process.", log_type="debug")
                    self.engine_process.kill()
                    self.engine_process.communicate() # Ensure pipes are closed
                except Exception as e: # Catch other exceptions like broken pipe if engine crashes on quit
                    self.logger(f"Exception during engine stop: {e}. Attempting to kill.", log_type="debug")
                    try:
                        self.engine_process.kill() # Fallback kill
                        self.engine_process.communicate()
                    except Exception as kill_e:
                        self.logger(f"Exception during fallback kill: {kill_e}", log_type="debug")
            else: # Already terminated
                self.logger("Engine process was already terminated.", log_type="debug")
            self.engine_process = None # Clear the process attribute
            self.logger("Chess engine stopped.", log_type="debug")