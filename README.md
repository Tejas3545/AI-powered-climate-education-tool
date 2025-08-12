# FireWise — Starter Repo (Demo)

This archive contains a lightweight starter for the FireWise hackathon project: a FastAPI backend that runs a cellular-automaton fire simulation and an optional XGBoost demo model, plus a minimal static frontend (Leaflet + canvas) that calls the backend and visualizes results.

## Files & structure (important ones)
- `backend/` — FastAPI app, simulation core, ML wrapper, and requirements file.
  - `backend/app/main.py` — API endpoints `/simulate` and `/predict`.
  - `backend/app/simulation.py` — cellular automaton simulation logic.
  - `backend/app/ml_model.py` — small ML wrapper that loads `backend/models/xgb_model.pkl` if present.
  - `backend/requirements_minimal.txt` — minimal Python dependencies for demo.
- `ml/train_xgb.py` — script that creates a demo XGBoost model (synthetic data) and writes `backend/models/xgb_model.pkl`.
- `frontend/` — minimal static frontend (no node required): `index.html`, `app.js`, `styles.css`.

## Quickstart (Linux / macOS / Windows with PowerShell)
1. **Create and activate a Python venv** (recommended):
   ```bash
   python -m venv .venv
   source .venv/bin/activate      # macOS/Linux
   # or on Windows PowerShell:
   # .\.venv\Scripts\Activate.ps1
   ```

2. **Install minimal backend dependencies**:
   ```bash
   pip install --upgrade pip
   pip install -r backend/requirements_minimal.txt
   ```
   - If `pip install xgboost` fails on Windows, try using conda: `conda install -c conda-forge xgboost`.

3. **(Optional) Train the demo XGBoost model** (creates `backend/models/xgb_model.pkl`):
   ```bash
   python -m ml.train_xgb
   ```
   - This uses the simulation to generate synthetic training examples and saves a small model for the `/predict` endpoint.
   - If you skip this step, the API will use a simple heuristic fallback for predictions.

4. **Run the FastAPI backend** (start from the `backend/` folder to make imports simple):
   ```bash
   cd backend
   uvicorn app.main:app --reload --port 8000
   ```
   - Open `http://127.0.0.1:8000/docs` to see the interactive API docs.

5. **Serve the frontend** (so browser allows fetch requests):
   ```bash
   cd ../frontend
   python -m http.server 5173
   ```
   - Open `http://127.0.0.1:5173` in your browser. Click **Run Simulation** to call the backend.
   - The frontend creates a random 32x32 grid and sends it to the backend `/simulate` endpoint. Use the slider to view timesteps.

## Common issues & fixes
- **Import errors when running training or server**: ensure you run commands from the project root (for `python -m ml.train_xgb`) or from `backend/` for `uvicorn app.main:app`.
- **`pip install xgboost` fails**: on Windows use conda or upgrade pip/wheel: `pip install --upgrade pip wheel setuptools` then retry. Use conda if needed.
- **Browser fetch CORS errors**: the backend allows `*` origins by default. If you still see errors, ensure backend is running and reachable at `http://127.0.0.1:8000`.
- **Deterministic demo for recording**: add `np.random.seed(0)` at the top of `backend/app/simulation.py` to get repeatable simulation runs for demos/videos.

## Next steps & improvements
- Replace static frontend with React + Leaflet for richer UI (I provided a scaffold in the conversation if you want React).
- Swap synthetic training with historical fire labels (MODIS/VIIRS) and weather reanalysis (ERA5) for a realistic model.
- Add SHAP explainability for the XGBoost model and a chatbot (retrieval-based) for Q&A/tutorial text.
