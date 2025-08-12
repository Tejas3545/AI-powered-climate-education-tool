// Realistic frontend v2: Play button, autoplay, and predicted risk overlay via /predict_risk
const backend = 'http://127.0.0.1:8000'
const statusEl = document.getElementById('status')
const timestepSlider = document.getElementById('timestep')
let timesteps = null
let riskmap = null
let heatLayer = null
let riskLayer = null
let map, startMarker = null
let playInterval = null

function setStatus(s){ statusEl.innerText = s }

function initMap(){
  map = L.map('map', {center:[21.5, 71.0], zoom:7})
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {maxZoom: 19}).addTo(map)
  map.on('click', (e)=>{
    if(startMarker) map.removeLayer(startMarker)
    startMarker = L.marker(e.latlng).addTo(map)
    startMarker.bindPopup('Start: ' + e.latlng.lat.toFixed(4) + ', ' + e.latlng.lng.toFixed(4)).openPopup()
  })
}

function drawHeatForStep(idx){
  if(!timesteps) return
  const pts = timesteps[idx]
  const heatData = pts.map(p=>[p.lat, p.lng, p.intensity])
  if(heatLayer) map.removeLayer(heatLayer)
  heatLayer = L.heatLayer(heatData, {radius: 25, blur: 15, maxZoom: 12}).addTo(map)
}

function drawRiskLayer(){
  if(!riskmap) return
  // riskmap is full grid points; show as heat with smaller radius
  const heatData = riskmap.map(p=>[p.lat, p.lng, p.score])
  if(riskLayer) map.removeLayer(riskLayer)
  riskLayer = L.heatLayer(heatData, {radius: 20, blur: 12, maxZoom: 12}).addTo(map)
}

async function runSimulation(){
  if(!startMarker){ setStatus('Click on the map to set the start point first.'); return }
  const payload = {
    start_lat: startMarker.getLatLng().lat,
    start_lng: startMarker.getLatLng().lng,
    wind_speed: parseFloat(document.getElementById('wind_speed').value),
    wind_dir_deg: parseFloat(document.getElementById('wind_dir').value),
    humidity: parseFloat(document.getElementById('humidity').value),
    temperature: parseFloat(document.getElementById('temperature').value),
    steps: parseInt(document.getElementById('steps').value),
    grid_size: parseInt(document.getElementById('grid_size').value),
    cell_size_deg: parseFloat(document.getElementById('cell_size').value)
  }
  setStatus('Sending simulation request...')
  try{
    const res = await fetch(backend + '/simulate_geo', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload)})
    const j = await res.json()
    timesteps = j.timesteps
    setStatus('Received ' + timesteps.length + ' timesteps. Use slider or Play.')
    timestepSlider.max = Math.max(0, timesteps.length - 1)
    timestepSlider.value = 0
    drawHeatForStep(0)
    // if showRisk checked, fetch risk
    if(document.getElementById('showRisk').checked){ fetchRisk(payload) }
  }catch(e){ console.error(e); setStatus('Simulation request failed: ' + e.message) }
}

async function fetchRisk(payload){
  setStatus('Requesting risk map...')
  try{
    const res = await fetch(backend + '/predict_risk', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload)})
    const j = await res.json()
    riskmap = j.risk_map
    drawRiskLayer()
    setStatus('Risk map ready. Toggle "Show predicted risk" to view.')
  }catch(e){ console.error(e); setStatus('Risk request failed: ' + e.message) }
}

document.getElementById('runBtn').addEventListener('click', runSimulation)
document.getElementById('playBtn').addEventListener('click', ()=>{
  if(playInterval){ clearInterval(playInterval); playInterval = null; document.getElementById('playBtn').innerText = 'Play'; return }
  if(!timesteps) return
  let i = 0
  document.getElementById('playBtn').innerText = 'Stop'
  playInterval = setInterval(()=>{
    drawHeatForStep(i)
    timestepSlider.value = i
    i++
    if(i >= timesteps.length){ clearInterval(playInterval); playInterval = null; document.getElementById('playBtn').innerText = 'Play' }
  }, 700)
})

timestepSlider.addEventListener('input', (e)=>{ const idx = parseInt(e.target.value); drawHeatForStep(idx) })
document.getElementById('showRisk').addEventListener('change', (e)=>{
  if(e.target.checked) drawRiskLayer(); else { if(riskLayer) map.removeLayer(riskLayer) }
})

initMap()
