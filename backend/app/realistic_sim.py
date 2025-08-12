import numpy as np
import math
from typing import List, Dict

# Realistic-ish fire spread over a geo-grid centered at start_lat/start_lng.
# Grid cells have states: 0=no-fuel/empty, 1=fuel (unburnt), 2=burning, 3=burnt.
# The function returns for each timestep a list of points with lat,lng,intensity (0..1).

def simulate_fire_geo(start_lat: float, start_lng: float, wind_speed: float, wind_dir_deg: float,
                      humidity: float, temperature: float, steps: int = 10,
                      grid_size: int = 64, cell_size_deg: float = 0.002):
    # NOTE: removed deterministic seed for variability in runs
    rows = cols = grid_size
    half = grid_size // 2

    # Create fuel map: use a smoothed random field to simulate vegetation
    base = np.random.rand(rows, cols)
    try:
        from scipy.ndimage import gaussian_filter
        fuel = gaussian_filter(base, sigma=3)
    except Exception:
        # fallback simple smoothing
        fuel = base
    fuel_mask = (fuel > 0.45).astype(np.int8)

    grid = np.zeros((rows, cols), dtype=np.int8)
    grid[fuel_mask==1] = 1

    sr, sc = half, half
    grid[sr, sc] = 2  # burning start

    # precompute wind vector (to direction)
    rad = math.radians((wind_dir_deg + 180) % 360)
    wx, wy = math.cos(rad), math.sin(rad)

    timesteps = []
    intensity = np.zeros_like(grid, dtype=float)
    intensity[grid==2] = 1.0

    for t in range(steps):
        points = []
        for r in range(rows):
            for c in range(cols):
                if grid[r, c] == 2:
                    lat = start_lat + (r - sr) * cell_size_deg
                    lng = start_lng + (c - sc) * cell_size_deg
                    points.append({"lat": lat, "lng": lng, "intensity": float(min(1.0, intensity[r,c]))})
        timesteps.append(points)

        new = grid.copy()
        new_intensity = intensity.copy()
        for r in range(rows):
            for c in range(cols):
                if grid[r, c] == 2:
                    new_intensity[r, c] = max(0.0, intensity[r, c] - 0.35)
                    if new_intensity[r,c] < 0.15:
                        new[r,c] = 3
                        new_intensity[r,c] = 0.0
                    for dr in (-1, 0, 1):
                        for dc in (-1, 0, 1):
                            if dr == 0 and dc == 0:
                                continue
                            nr, nc = r + dr, c + dc
                            if nr < 0 or nr >= rows or nc < 0 or nc >= cols:
                                continue
                            if grid[nr, nc] != 1:
                                continue
                            vec_x = dc
                            vec_y = -dr
                            norm = math.hypot(vec_x, vec_y) + 1e-9
                            vx, vy = vec_x / norm, vec_y / norm
                            align = vx * wx + vy * wy
                            base_prob = 0.06
                            wind_effect = max(0.0, 1.0 + (wind_speed / 20.0) * align)
                            hum_effect = max(0.05, 1.0 - humidity / 100.0)
                            temp_effect = 1.0 + max(0.0, (temperature - 15.0) / 40.0)
                            fuel_factor = 1.0 + 0.6 * (fuel[r, c] - 0.5)
                            neigh_burning = 0
                            for dr2 in (-1,0,1):
                                for dc2 in (-1,0,1):
                                    if dr2==0 and dc2==0: continue
                                    rr, cc = r+dr2, c+dc2
                                    if 0<=rr<rows and 0<=cc<cols and grid[rr,cc]==2:
                                        neigh_burning += 1
                            neigh_effect = 1.0 + 0.3 * neigh_burning
                            noise = np.random.rand() * 0.12
                            prob = base_prob * wind_effect * hum_effect * temp_effect * fuel_factor * neigh_effect + noise
                            prob = min(1.0, prob)
                            if np.random.rand() < prob:
                                new[nr, nc] = 2
                                new_intensity[nr, nc] = max(new_intensity[nr, nc], min(1.0, prob))
        grid = new
        intensity = new_intensity

    return timesteps
