# perlin_noise_helpers.py
import numpy as np
import random
import math
import time
from typing import Callable, Tuple, Dict, Any, Optional

class Perlin:
    """
    Generates 2D Perlin noise.
    """
    def __init__(self):
        p_range = list(range(256))
        random.shuffle(p_range)
        self.p = np.array(p_range + p_range, dtype=int)

    def _fade(self, t: np.ndarray) -> np.ndarray:
        return t*t*t*(t*(t*6-15)+10)

    def _lerp(self, a: np.ndarray, b: np.ndarray, t: np.ndarray) -> np.ndarray:
        return a + t*(b-a)

    def _grad(self, h: np.ndarray, x: np.ndarray, y: np.ndarray) -> np.ndarray:
        h_mod = h & 3
        u = np.where(h_mod < 2, x, y)
        v = np.where(h_mod < 2, y, x)
        part1 = np.where((h & 1) == 0, u, -u)
        part2 = np.where((h & 2) == 0, v, -v)
        return part1 + part2

    def noise_array(self, w: int, h: int, scale: float) -> np.ndarray:
        if scale <= 0: scale = 0.001
        xs = np.linspace(0, w/scale, w, endpoint=False)
        ys = np.linspace(0, h/scale, h, endpoint=False)
        xi0, yi0 = xs.astype(int), ys.astype(int)
        xf0, yf0 = xs - xi0, ys - yi0
        xf1, yf1 = xf0 - 1.0, yf0 - 1.0
        u, v_fade = self._fade(xf0), self._fade(yf0)
        perm = self.p
        xi0_mod, yi0_mod = xi0 & 255, yi0 & 255
        
        noise_map = np.empty((h, w), dtype=float)
        for j_idx in range(h):
            idx00 = perm[xi0_mod] + yi0_mod[j_idx]
            idx10 = perm[xi0_mod + 1] + yi0_mod[j_idx]
            idx01 = perm[xi0_mod] + yi0_mod[j_idx] + 1
            idx11 = perm[xi0_mod + 1] + yi0_mod[j_idx] + 1
            g00, g10, g01, g11 = perm[idx00], perm[idx10], perm[idx01], perm[idx11]
            n00 = self._grad(g00, xf0, yf0[j_idx])
            n10 = self._grad(g10, xf1, yf0[j_idx])
            n01 = self._grad(g01, xf0, yf1[j_idx])
            n11 = self._grad(g11, xf1, yf1[j_idx])
            x_interp1 = self._lerp(n00, n10, u)
            x_interp2 = self._lerp(n01, n11, u)
            noise_map[j_idx] = (self._lerp(x_interp1, x_interp2, v_fade[j_idx]) + 1) * 0.5
        return noise_map

def perform_perlin_move(
    start_pos: Tuple[float, float],
    end_pos: Tuple[float, float],
    noise_map: np.ndarray,
    screen_width: int,
    screen_height: int, # Actual screen dimensions noise_map was scaled to conceptually cover
    perlin_cfg: Dict[str, Any],
    set_cursor_func: Callable[[int, int], None],
    logger: Callable[[str, str], None]
):
    """
    Moves the mouse from start_pos to end_pos using Perlin noise.
    Assumes noise_map corresponds to screen_width, screen_height conceptually.
    The noise_map itself has dimensions (screen_height * res_scale, screen_width * res_scale).
    """
    current_x, current_y = float(start_pos[0]), float(start_pos[1])
    target_x, target_y = float(end_pos[0]), float(end_pos[1])

    # Noise map dimensions (actual shape of the array)
    noise_map_h, noise_map_w = noise_map.shape

    min_dist_sq = perlin_cfg["min_dist_sq"]
    
    loop_count = 0
    max_loops = 500 # Safety break for unexpected situations

    while loop_count < max_loops:
        loop_count += 1
        dx_to_target = target_x - current_x
        dy_to_target = target_y - current_y
        dist_to_target_sq = dx_to_target*dx_to_target + dy_to_target*dy_to_target

        if dist_to_target_sq < min_dist_sq:
            next_x, next_y = target_x, target_y # Snap to target
        else:
            # Normalize current screen position to [0,1] range for noise map lookup
            # Use actual screen dimensions for this normalization
            norm_screen_x = np.clip(current_x / screen_width, 0.0, 0.99999)
            norm_screen_y = np.clip(current_y / screen_height, 0.0, 0.99999)
            
            # Get corresponding index in the (potentially res_scaled) noise_map
            noise_idx_x = int(norm_screen_x * noise_map_w)
            noise_idx_y = int(norm_screen_y * noise_map_h)
            
            noise_val = float(noise_map[noise_idx_y, noise_idx_x]) # Ensure it's a float scalar

            speed = perlin_cfg["speed_min"] + noise_val * perlin_cfg["speed_max_mul"]
            jitter_x = (random.random() - 0.5) * noise_val * perlin_cfg["jitter_mul"]
            jitter_y = (random.random() - 0.5) * noise_val * perlin_cfg["jitter_mul"]
            deviation = (noise_val - 0.5) * math.radians(perlin_cfg["dev_deg"])
            
            angle_to_target = math.atan2(dy_to_target, dx_to_target)
            move_angle = angle_to_target + deviation
            
            step_dx = math.cos(move_angle) * speed + jitter_x
            step_dy = math.sin(move_angle) * speed + jitter_y
            step_len_sq = step_dx*step_dx + step_dy*step_dy

            if step_len_sq >= dist_to_target_sq:
                next_x, next_y = target_x, target_y # Snap to target if overshoot
            else:
                next_x = current_x + step_dx
                next_y = current_y + step_dy
        
        # Ensure movement stays within screen boundaries (optional, but good for safety)
        next_x_clamped = np.clip(next_x, 0, screen_width -1)
        next_y_clamped = np.clip(next_y, 0, screen_height -1)

        set_cursor_func(int(next_x_clamped), int(next_y_clamped))
        
        current_x, current_y = next_x_clamped, next_y_clamped

        if abs(current_x - target_x) < 1e-1 and abs(current_y - target_y) < 1e-1 : # Effectively at target
             if current_x != target_x or current_y != target_y: # Final snap if not exact
                set_cursor_func(int(target_x), int(target_y))
             break 
        
        time.sleep(perlin_cfg["sleep_interval"])
    
    if loop_count >= max_loops:
        logger("Perlin move reached max loops. Snapping to target.", "debug")
        set_cursor_func(int(target_x), int(target_y))