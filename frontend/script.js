// script.js — full integrated frontend (map views, controls, heatmap, play, risk)
const backend = 'http://127.0.0.1:8000'

// control elements
const windInput = document.getElementById('wind_speed')
const windVal = document.getElementById('wind_speed_val')
const windDirInput = document.getElementById('wind_dir')
const windDirVal = document.getElementById('wind_dir_val')
const humInput = document.getElementById('humidity')
const humVal = document.getElementById('humidity_val')
const tempInput = document.getElementById('temperature')
const tempVal = document.getElementById('temperature_val')
const stepsInput = document.getElementById('steps')
const stepsVal = document.getElementById('steps_val')
const gridInput = document.getElementById('grid_size')
const gridVal = document.getElementById('grid_size_val')
const cellInput = document.getElementById('cell_size')
const cellVal = document.getElementById('cell_size_val')

const statusEl = document.getElementById('status')
const timestepSlider = document.getElementById('timestep')
const infoStep = document.getElementById('infoStep')
const infoCells = document.getElementById('infoCells')
const infoArea = document.getElementById('infoArea')
const mapStyleSelect = document.getElementById('mapStyle')

let map, startMarker = null, heatLayer = null, riskLayer = null
let timesteps = null, riskmap = null
let playInterval = null, isPlaying = false

function setStatus(txt){ statusEl.innerText = txt }

// --- badges setup
function bindBadgeListeners(){
  const pairs = [
    [windInput, windVal, v => `${v} km/h`],
    [windDirInput, windDirVal, v => `${v}°`],
    [humInput, humVal, v => `${v}%`],
    [tempInput, tempVal, v => `${v}°C`],
    [stepsInput, stepsVal, v => `${v}`],
    [gridInput, gridVal, v => `${v}`],
    [cellInput, cellVal, v => `${parseFloat(v).toFixed(3)}°`]
  ]
  pairs.forEach(([input, badge, fmt])=>{
    if(!input || !badge) return
    badge.innerText = fmt(input.value)
    input.addEventListener('input', ()=> badge.innerText = fmt(input.value))
  })
}

// --- map init with base layers and layer control
let streetLayer, satelliteLayer, labelsLayer, hybridLayer, darkLayer, currentBaseLayer

function initMap(){
  // Street
  streetLayer = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19, attribution: '&copy; OSM'
  })

  // Satellite (Esri World Imagery)
  satelliteLayer = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
    attribution: 'Tiles © Esri'
  })

  // labels (OSM) used for hybrid overlay
  labelsLayer = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OSM', opacity: 0.8
  })

  // hybrid = satellite + labels (group)
  hybridLayer = L.layerGroup([satelliteLayer, labelsLayer])

  // dark basemap
  darkLayer = L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
    attribution: '&copy; CARTO &copy; OSM', subdomains:'abcd', maxZoom:19
  })

  // create map (single instance)
  map = L.map('map', { center:[22.9734,78.6569], zoom:5, layers: [streetLayer] })
  currentBaseLayer = streetLayer

  // add control (top-right)
  const baseMaps = { "Street": streetLayer, "Satellite": satelliteLayer, "Hybrid": hybridLayer, "Dark": darkLayer }
  L.control.layers(baseMaps).addTo(map)

  // click to set start marker
  map.on('click', (e)=>{
    if(startMarker) startMarker.remove()
    startMarker = L.marker(e.latlng, {riseOnHover:true}).addTo(map)
    startMarker.bindPopup('🔥 Start Point').openPopup()
    setStatus('Start point set: ' + e.latlng.lat.toFixed(4) + ', ' + e.latlng.lng.toFixed(4))
  })
}

// --- helpers to render heat/risk
function heatDataForStep(idx){ return (timesteps && timesteps[idx]) ? timesteps[idx].map(p=>[p.lat,p.lng,p.intensity]) : [] }

function drawStep(idx){
  if(!timesteps) return
  if(heatLayer) { map.removeLayer(heatLayer); heatLayer = null }
  const data = heatDataForStep(idx)
  heatLayer = L.heatLayer(data, { radius: 22, blur: 18, maxZoom: 11, gradient: {0.4:'yellow',0.65:'orange',1.0:'red'} }).addTo(map)
  infoStep.innerText = `${idx+1} / ${timesteps.length}`
  const pts = timesteps[idx].length
  infoCells.innerText = pts
  const cellSizeDeg = parseFloat(cellInput.value) || 0.002
  const kmPerDeg = 111.0
  const areaPerCell = Math.pow(kmPerDeg * cellSizeDeg, 2)
  infoArea.innerText = (pts * areaPerCell).toFixed(2)
  timestepSlider.value = idx
}

function clearRiskLayer(){ if(riskLayer){ map.removeLayer(riskLayer); riskLayer = null } }
function drawRisk(){ if(!riskmap) return; clearRiskLayer(); const heat = riskmap.map(p=>[p.lat,p.lng,p.score]); riskLayer = L.heatLayer(heat, {radius:18, blur:14, gradient:{0.0:'#001f3f',0.4:'#6a00ff',1.0:'#ff00a8'}}).addTo(map) }

// --- backend calls
async function runSimulation(){
  if(!startMarker){ setStatus('Please click map to set a start point first.'); return }
  const payload = {
    start_lat: startMarker.getLatLng().lat,
    start_lng: startMarker.getLatLng().lng,
    wind_speed: parseFloat(windInput.value),
    wind_dir_deg: parseFloat(windDirInput.value),
    humidity: parseFloat(humInput.value),
    temperature: parseFloat(tempInput.value),
    steps: parseInt(stepsInput.value) || 10,
    grid_size: parseInt(gridInput.value) || 64,
    cell_size_deg: parseFloat(cellInput.value) || 0.002
  }
  setStatus('Running simulation...')
  try{
    const res = await fetch(backend + '/simulate_geo', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload) })
    if(!res.ok) throw new Error('Server returned ' + res.status)
    const j = await res.json()
    timesteps = j.timesteps || []
    if(!timesteps.length){ setStatus('Simulation returned no timesteps'); return }
    setStatus('Simulation ready — use Play or slider')
    timestepSlider.max = Math.max(0, timesteps.length - 1)
    drawStep(0)
    if(document.getElementById('showRisk').checked) fetchRisk(payload)
    else clearRiskLayer()
  }catch(err){
    console.error(err)
    setStatus('Simulation request failed: ' + (err.message || err))
  }
}

async function fetchRisk(payload){
  setStatus('Requesting predicted risk map...')
  try{
    const res = await fetch(backend + '/predict_risk', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload) })
    if(!res.ok) throw new Error('Server returned ' + res.status)
    const j = await res.json()
    riskmap = j.risk_map || []
    drawRisk()
    setStatus('Risk map ready (toggle to show/hide).')
  }catch(err){
    console.error(err)
    setStatus('Risk request failed: ' + (err.message || err))
  }
}

// --- UI wiring
document.getElementById('runBtn').addEventListener('click', runSimulation)
document.getElementById('playBtn').addEventListener('click', ()=>{
  if(!timesteps || !timesteps.length) return
  if(isPlaying){ clearInterval(playInterval); isPlaying=false; document.getElementById('playBtn').innerText='Play' }
  else {
    isPlaying=true; document.getElementById('playBtn').innerText='Stop'
    let i = parseInt(timestepSlider.value) || 0
    playInterval = setInterval(()=>{
      drawStep(i)
      i++
      if(i >= timesteps.length){ clearInterval(playInterval); isPlaying=false; document.getElementById('playBtn').innerText='Play' }
    }, 650)
  }
})

timestepSlider.addEventListener('input', (e)=>{ drawStep(parseInt(e.target.value)) })
document.getElementById('showRisk').addEventListener('change', (e)=>{
  if(e.target.checked){
    if(!startMarker){ setStatus('Set start point to fetch risk.'); e.target.checked=false; return }
    const payload = {
      start_lat: startMarker.getLatLng().lat,
      start_lng: startMarker.getLatLng().lng,
      wind_speed: parseFloat(windInput.value),
      wind_dir_deg: parseFloat(windDirInput.value),
      humidity: parseFloat(humInput.value),
      temperature: parseFloat(tempInput.value),
      grid_size: parseInt(gridInput.value) || 64,
      cell_size_deg: parseFloat(cellInput.value) || 0.002
    }
    fetchRisk(payload)
  } else {
    clearRiskLayer()
  }
})

// dropdown mapStyle -> switch base layer (keeps overlays)
mapStyleSelect.addEventListener('change', (e)=>{
  const v = e.target.value
  // remove current base layers if present
  [streetLayer, satelliteLayer, labelsLayer, darkLayer].forEach(l=>{
    try{ if(map && map.hasLayer(l)) map.removeLayer(l) }catch(_){}
  })
  try{ if(map && map.hasLayer(hybridLayer)) map.removeLayer(hybridLayer) }catch(_){}
  // add requested
  if(v === 'street'){ currentBaseLayer = streetLayer; currentBaseLayer.addTo(map) }
  else if(v === 'satellite'){ currentBaseLayer = satelliteLayer; currentBaseLayer.addTo(map) }
  else if(v === 'hybrid'){ currentBaseLayer = hybridLayer; hybridLayer.addTo(map) }
  else if(v === 'dark'){ currentBaseLayer = darkLayer; currentBaseLayer.addTo(map) }
})

// --- initialization
bindBadgeListeners()
initMap()
setStatus('Ready — click map to place start point, set parameters, then Run Simulation.')
