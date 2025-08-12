import numpy as np
import pickle
import os

class MLModel:
    def __init__(self, model_path=None):
        self.model = None
        if model_path is None:
            model_path = os.path.join(os.path.dirname(__file__), '..', 'models', 'xgb_model.pkl')
        model_path = os.path.normpath(model_path)
        if os.path.exists(model_path):
            try:
                with open(model_path, 'rb') as f:
                    self.model = pickle.load(f)
            except Exception as e:
                print('Warning: failed to load model:', e)

    def build_features(self, grid, wind_speed, wind_dir_deg, humidity, temperature):
        rows, cols = grid.shape
        feat = []
        for r in range(rows):
            for c in range(cols):
                neighbors = 0
                for dr in (-1,0,1):
                    for dc in (-1,0,1):
                        if dr==0 and dc==0: continue
                        nr, nc = r+dr, c+dc
                        if 0<=nr<rows and 0<=nc<cols and grid[nr,nc]==2:
                            neighbors += 1
                # features: is_fuel, neighbor_burning_count, wind_speed, wind_dir_deg, humidity, temperature
                feat.append([1 if grid[r,c]==1 else 0, neighbors, wind_speed, wind_dir_deg, humidity, temperature])
        return np.array(feat)

    def predict_proba_map(self, features):
        if self.model is None:
            # fallback heuristic: higher neighbor count + low humidity -> higher risk
            base = features[:,0] * (0.15 + 0.12*features[:,1]) * (1 - features[:,4]/100.0)
            clipped = np.clip(base, 0.0, 1.0)
            return clipped.reshape((-1,))
        else:
            try:
                probs = self.model.predict_proba(features)[:,1]
                return probs
            except Exception as e:
                print('Model prediction failed, falling back to heuristic:', e)
                base = features[:,0] * (0.15 + 0.12*features[:,1]) * (1 - features[:,4]/100.0)
                return np.clip(base, 0.0, 1.0)
