import numpy as np
import os, pickle, math

def predict_risk_geo(start_lat, start_lng, wind_speed, wind_dir_deg, humidity, temperature, grid_size=64, cell_size_deg=0.002):
    rows = cols = grid_size
    half = grid_size // 2
    # create a simple fuel map
    base = np.random.rand(rows, cols)
    try:
        from scipy.ndimage import gaussian_filter
        fuel = gaussian_filter(base, sigma=3)
    except Exception:
        fuel = base
    fuel_mask = (fuel > 0.45).astype(np.int8)
    # features per cell: fuel, distance from start, alignment with wind, humidity, temp
    rad = math.radians((wind_dir_deg + 180) % 360)
    wx, wy = math.cos(rad), math.sin(rad)
    pts = []
    features = []
    coords = []
    for r in range(rows):
        for c in range(cols):
            lat = start_lat + (r - half) * cell_size_deg
            lng = start_lng + (c - half) * cell_size_deg
            # vector from start to cell
            vec_x = (c - half)
            vec_y = -(r - half)
            dist = math.hypot(vec_x, vec_y)
            if dist == 0: align = 1.0
            else:
                align = (vec_x/dist)*wx + (vec_y/dist)*wy
            fuel_val = float(fuel[r,c])
            feat = [fuel_val, dist, align, wind_speed, humidity, temperature]
            features.append(feat)
            coords.append((lat,lng))
    X = np.array(features)
    # try to load xgboost model
    model_path = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', 'models', 'xgb_geo_model.pkl'))
    if os.path.exists(model_path):
        try:
            with open(model_path, 'rb') as f:
                model = pickle.load(f)
            probs = model.predict_proba(X)[:,1]
        except Exception as e:
            # fallback heuristic
            probs = heuristic(X)
    else:
        probs = heuristic(X)
    # normalize probs 0..1 and output points list
    probs = np.clip(probs, 0.0, 1.0)
    points = []
    for (lat,lng), p in zip(coords, probs):
        points.append({'lat': lat, 'lng': lng, 'score': float(p)})
    return points

def heuristic(X):
    # X columns: fuel, dist, align, wind_speed, humidity, temperature
    fuel = X[:,0]
    dist = X[:,1]
    align = X[:,2]
    wind = X[:,3]
    hum = X[:,4]
    temp = X[:,5]
    base = 0.2 * fuel * (1.0 + 0.2*align) * (1.0 + wind/20.0) * (1.0 - hum/100.0) * (1.0 + (temp-15.0)/40.0)
    # decay with distance
    base = base * np.exp(-dist/10.0)
    return np.clip(base, 0.0, 1.0)
