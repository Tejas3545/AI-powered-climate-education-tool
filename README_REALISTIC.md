# FireWise — Realistic Simulation Update

## What's new
- A new backend endpoint `/simulate_geo` that runs a more realistic stochastic fire spread simulation on a geo-grid centered at a user-provided start point.
- Frontend that lets you **click the map** to set the fire start location, supplies weather inputs, and visualizes spread using a heatmap (leaflet.heat).

## How to run (Linux / macOS / Windows PowerShell)
1. Create & activate venv:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # or on Windows PowerShell: .\.venv\Scripts\Activate.ps1
   ```
2. Install backend deps:
   ```bash
   pip install --upgrade pip
   pip install -r backend/requirements_realistic.txt
   ```
   - This uses `scipy` for gaussian smoothing; install may take a minute.

3. Start the backend (from project root):
   ```bash
   cd backend
   uvicorn app.main:app --reload --port 8000
   ```

4. Serve frontend (new terminal):
   ```bash
   cd frontend
   python -m http.server 5173
   ```

5. Open `http://127.0.0.1:5173` in your browser. Click anywhere on the map to set the start, then click "Run Simulation".

## Notes
- The simulation is stochastic but seeded (`np.random.seed(1)`) for repeatable demo runs. Remove seed for variability.
- `cell_size_deg` controls spatial resolution. 0.01 deg ~ 1.1 km * 0.01 = ~11 km? Wait — correction: 1 degree lat ~111 km, so 0.01 deg ~1.11 km. For demo you may want 0.002 (~222 m).
- The model is simplified and meant for educational demo (not for operational fire forecasting).
