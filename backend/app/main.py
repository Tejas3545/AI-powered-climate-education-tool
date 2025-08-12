from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import numpy as np
from app.realistic_sim import simulate_fire_geo
from app.predictor import predict_risk_geo

app = FastAPI(title="FireWise Realistic API v2")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

class GeoSimRequest(BaseModel):
    start_lat: float
    start_lng: float
    wind_speed: float
    wind_dir_deg: float
    humidity: float
    temperature: float
    steps: int = 10
    grid_size: int = 64
    cell_size_deg: float = 0.002  # default changed to 0.002 (~222m)

@app.post('/simulate_geo')
async def simulate_geo(req: GeoSimRequest):
    seq = simulate_fire_geo(req.start_lat, req.start_lng, req.wind_speed, req.wind_dir_deg,
                            req.humidity, req.temperature, req.steps, req.grid_size, req.cell_size_deg)
    return {"timesteps": seq}

@app.post('/predict_risk')
async def predict_risk(req: GeoSimRequest):
    # returns list of {lat,lng,score} for each grid cell center, score in 0..1
    risk = predict_risk_geo(req.start_lat, req.start_lng, req.wind_speed, req.wind_dir_deg,
                            req.humidity, req.temperature, req.grid_size, req.cell_size_deg)
    return {"risk_map": risk}
