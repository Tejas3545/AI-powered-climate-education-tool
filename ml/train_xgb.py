# Lightweight training script for demo purposes.
# Run from project root as: python -m ml.train_xgb
import numpy as np
from xgboost import XGBClassifier
import pickle
from pathlib import Path
from backend.app.simulation import simulate_sequence

def gen_random_grid(rows=32, cols=32, fuel_prob=0.5, init_fires=3):
    grid = np.zeros((rows, cols), dtype=np.int8)
    mask = np.random.rand(rows, cols) < fuel_prob
    grid[mask] = 1
    coords = np.argwhere(grid==1)
    if len(coords) > 0:
        idx = np.random.choice(len(coords), size=min(init_fires, len(coords)), replace=False)
        for i in idx:
            r,c = coords[i]
            grid[r,c] = 2
    return grid

X = []
y = []
runs = 300
for _ in range(runs):
    grid = gen_random_grid()
    seq = simulate_sequence(grid, wind_speed=np.random.uniform(0,15),
                            wind_dir_deg=np.random.uniform(0,360),
                            humidity=np.random.uniform(5,80),
                            temperature=np.random.uniform(10,40),
                            steps=3)
    for t in range(len(seq)-1):
        g_t = seq[t]
        g_next = seq[t+1]
        rows, cols = g_t.shape
        for r in range(rows):
            for c in range(cols):
                if g_t[r,c]==1:
                    neighbors = 0
                    for dr in (-1,0,1):
                        for dc in (-1,0,1):
                            if dr==0 and dc==0: continue
                            nr, nc = r+dr, c+dc
                            if 0<=nr<rows and 0<=nc<cols and g_t[nr,nc]==2:
                                neighbors += 1
                    feat = [1 if g_t[r,c]==1 else 0, neighbors, 0.0, 0.0, np.random.uniform(5,80), np.random.uniform(10,40)]
                    X.append(feat)
                    y.append(1 if g_next[r,c]==2 else 0)

X = np.array(X)
y = np.array(y)
print('Training data shape:', X.shape, 'labels:', y.shape)
model = XGBClassifier(use_label_encoder=False, eval_metric='logloss', n_estimators=50, max_depth=4)
model.fit(X, y)
out_dir = Path('backend/models')
out_dir.mkdir(parents=True, exist_ok=True)
with open(out_dir / 'xgb_model.pkl', 'wb') as f:
    pickle.dump(model, f)
print('Saved demo model to', out_dir / 'xgb_model.pkl')
