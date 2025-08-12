import numpy as np

# Cell states: 0=empty, 1=fuel (unburnt), 2=burning, 3=burnt

def neighbor_coords(r, c, rows, cols):
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if dr == 0 and dc == 0:
                continue
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols:
                yield nr, nc

def wind_factor(dr, dc, wind_dir_deg, wind_speed):
    # Approx simple factor: if neighbor aligns with wind direction, raise spread prob
    # Convert wind_dir_deg (meteorological degrees, from) into a vector pointing to 'to' direction
    rad = np.deg2rad((wind_dir_deg + 180) % 360)
    wx, wy = np.cos(rad), np.sin(rad)
    # Map grid neighbor vector (dr,dc) to x,y where +x is east (dc), +y is north (-dr)
    vec = np.array([dc, -dr], dtype=float)
    # avoid zero-length
    if np.allclose(vec, 0.0):
        dot = 0.0
    else:
        dot = np.dot(vec / (np.linalg.norm(vec) + 1e-9), np.array([wx, wy]))
    # normalize between ~0.5 and ~1.5 depending on alignment and wind speed
    return 1.0 + 0.5 * np.tanh(2 * dot) * (wind_speed / 10.0)

def moisture_factor(humidity):
    # More humidity -> less spread
    return max(0.1, 1.0 - (humidity / 100.0))

def base_prob(cell_state):
    # base ignition probability depending on cell type
    if cell_state == 1:
        return 0.4
    return 0.0

def step(grid, wind_speed, wind_dir_deg, humidity, temperature):
    rows, cols = grid.shape
    new = grid.copy()
    for r in range(rows):
        for c in range(cols):
            if grid[r, c] == 2:  # burning
                # after burning, becomes burnt
                new[r, c] = 3
                for nr, nc in neighbor_coords(r, c, rows, cols):
                    if grid[nr, nc] == 1:  # unburnt fuel
                        dr, dc = nr - r, nc - c
                        wf = wind_factor(dr, dc, wind_dir_deg, wind_speed)
                        mf = moisture_factor(humidity)
                        prob = base_prob(grid[nr, nc]) * wf * mf
                        if np.random.rand() < prob:
                            new[nr, nc] = 2
    return new

def simulate_sequence(grid, wind_speed, wind_dir_deg, humidity, temperature, steps=10):
    seq = [grid.copy()]
    cur = grid.copy()
    for _ in range(steps):
        cur = step(cur, wind_speed, wind_dir_deg, humidity, temperature)
        seq.append(cur.copy())
    return seq
