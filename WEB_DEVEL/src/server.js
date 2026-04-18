const http = require('http');
const express = require('express');
const path = require('path');
const fs = require('fs');
const { execFile, spawn } = require('child_process');
const { Server } = require('socket.io');

const app = express();
const httpServer = http.createServer(app);
const io = new Server(httpServer);
const PORT = 3000;

const DATA_DIR = path.join(__dirname, '..', 'data', 'logs');
const PAGES_DIR = path.join(__dirname, 'pages');
const IMGS_DIR = path.join(__dirname,'..', 'img');


app.use(express.json({ limit: '100mb' }));
app.use('/styles', express.static(path.join(__dirname, 'styles')));
app.use('/scripts', express.static(path.join(__dirname, 'scripts')));
app.use('/data', express.static(path.join(__dirname, '..', 'data')));
app.use('/img', express.static(IMGS_DIR));
// ---- Pages ----

app.get('/', (req, res) => {
  res.sendFile(path.join(PAGES_DIR, 'index.html'));
});

app.get('/simulation/:id', (req, res) => {
  res.sendFile(path.join(PAGES_DIR, 'simulation.html'));
});

app.get('/config/:id', (req, res) => {
  res.sendFile(path.join(PAGES_DIR, 'config.html'));
});

app.get('/favicon.ico', (req, res) => {
  res.sendFile(path.join(IMGS_DIR, 'EMTLogo_32.png'));
});




// Resolve the INPUTS directory for a simulation (supports both old and new layouts)
function resolveInputsPath(simPath) {
  const newLayout = path.join(simPath, 'TEST_MOBILITY', 'includes', 'INPUTS');
  if (fs.existsSync(newLayout)) return newLayout;
  const oldLayout = path.join(simPath, 'includes', 'INPUTS');
  if (fs.existsSync(oldLayout)) return oldLayout;
  return null;
}

// Parse description.txt: `title "..."`, `description "..."`, `line "..."`
function parseDescription(simPath) {
  const descPath = path.join(simPath, 'description.txt');
  if (!fs.existsSync(descPath)) return { title: null, description: null, line: null };
  try {
    const lines = fs.readFileSync(descPath, 'utf8').split('\n');
    let title = null, description = null, line = null;
    for (const rawLine of lines) {
      const sp = rawLine.indexOf(' ');
      if (sp === -1) continue;
      const key = rawLine.slice(0, sp).trim();
      let val = rawLine.slice(sp + 1).trim();
      val = val.replace(/^"(.*)"$/, '$1'); // strip surrounding quotes
      if (key === 'title') title = val;
      else if (key === 'description') description = val;
      else if (key === 'line') line = val;
    }
    return { title, description, line };
  } catch (_) {
    return { title: null, description: null, line: null };
  }
}

// List all simulations
app.get('/api/simulations', (req, res) => {
  try {
    const entries = fs.readdirSync(DATA_DIR, { withFileTypes: true });
    const sims = entries
      .filter(e => e.isDirectory() && e.name.startsWith('SIMULATION_'))
      .map(e => {
        const id = e.name;
        const simPath = path.join(DATA_DIR, id);
        const resultsPath = path.join(simPath, 'RESULTS');
        const chartsPath = path.join(simPath, 'PLOTS');
        let status = 'En progreso';
        let runCount = 0;
        try {
          runCount = fs.readdirSync(resultsPath).filter(f => f.endsWith('.csv')).length;
        } catch (_) {}

        const hasCharts = fs.existsSync(chartsPath) &&
          fs.readdirSync(chartsPath).some(f => f.endsWith('.png') || f.endsWith('.jpg') || f.endsWith('.json'));

        // Parse datetime from folder name: SIMULATION_YYYYMMDD_HHMMSS
        const match = id.match(/SIMULATION_(\d{8})_(\d{6})/);
        let datetime = null;
        if (match) {
          const d = match[1];
          const t = match[2];
          datetime = `${d.slice(0, 4)}-${d.slice(4, 6)}-${d.slice(6, 8)} ${t.slice(0, 2)}:${t.slice(2, 4)}:${t.slice(4, 6)}`;
        }
        if (runCount === 1000){
          status = 'Completada';
        }
        else{ 
          status = 'En progreso';
        }
        const { title, description } = parseDescription(simPath);
        return { id, datetime, runCount, hasCharts, title, description, status };
      })
      .sort((a, b) => b.id.localeCompare(a.id));

    res.json(sims);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Get simulation detail
app.get('/api/simulations/:id', (req, res) => {
  const { id } = req.params;
  if (!id.match(/^SIMULATION_\d{8}_\d{6}$/)) {
    return res.status(400).json({ error: 'Invalid simulation ID' });
  }

  const simPath = path.join(DATA_DIR, id);
  if (!fs.existsSync(simPath)) {
    return res.status(404).json({ error: 'Simulation not found' });
  }

  const resultsPath = path.join(simPath, 'RESULTS');
  const chartsPath = path.join(simPath, 'PLOTS');

  // Count runs
  let runCount = 0;
  try {
    runCount = fs.readdirSync(resultsPath).filter(f => f.endsWith('.csv')).length;
  } catch (_) {}

  // List chart images
  let charts = [];
  if (fs.existsSync(chartsPath)) {
    charts = fs.readdirSync(chartsPath)
      .filter(f => f.match(/\.(png|jpg|jpeg|svg)$/i))
      .map(f => `/data/logs/${id}/PLOTS/${f}`);
  }

  // Read log file
  let logContent = null;
  try {
    const logFiles = fs.readdirSync(simPath).filter(f => f.endsWith('.log'));
    if (logFiles.length > 0) {
      const raw = fs.readFileSync(path.join(simPath, logFiles[0]), 'utf8');
      logContent = raw.split('\n').join('\n');
    }
  } catch (_) {}

  // Parse datetime
  const match = id.match(/SIMULATION_(\d{8})_(\d{6})/);
  let datetime = null;
  if (match) {
    const d = match[1];
    const t = match[2];
    datetime = `${d.slice(0, 4)}-${d.slice(4, 6)}-${d.slice(6, 8)} ${t.slice(0, 2)}:${t.slice(2, 4)}:${t.slice(4, 6)}`;
  }

  const { title, description } = parseDescription(simPath);
  res.json({ id, datetime, runCount, charts, logContent, title, description });
});

// Get aggregated CSV stats for a simulation
app.get('/api/simulations/:id/stats', (req, res) => {
  const { id } = req.params;
  if (!id.match(/^SIMULATION_\d{8}_\d{6}$/)) {
    return res.status(400).json({ error: 'Invalid simulation ID' });
  }

  const resultsPath = path.join(DATA_DIR, id, 'RESULTS');
  if (!fs.existsSync(resultsPath)) {
    return res.status(404).json({ error: 'No results found' });
  }

  try {
    const files = fs.readdirSync(resultsPath).filter(f => f.endsWith('.csv'));
    let totalBoards = 0, totalDropoffs = 0, totalPassengers = 0, rows = 0;
    const byDirection = { toA: { boards: 0, dropoffs: 0 }, toB: { boards: 0, dropoffs: 0 } };
    const byTimeSlot = {};

    for (const file of files.slice(0, 50)) { // sample first 50 for performance
      const content = fs.readFileSync(path.join(resultsPath, file), 'utf8');
      const lines = content.split('\n').slice(1); // skip header
      for (const line of lines) {
        if (!line.trim()) continue;
        const cols = line.split(',');
        if (cols.length < 11) continue;
        const direction = cols[3]?.trim();
        const timeSlot = cols[6]?.trim();
        const boards = parseFloat(cols[7]) || 0;
        const dropoffs = parseFloat(cols[9]) || 0;
        const passengers = parseFloat(cols[10]) || 0;

        totalBoards += boards;
        totalDropoffs += dropoffs;
        totalPassengers += passengers;
        rows++;

        if (direction === 'toA') { byDirection.toA.boards += boards; byDirection.toA.dropoffs += dropoffs; }
        else if (direction === 'toB') { byDirection.toB.boards += boards; byDirection.toB.dropoffs += dropoffs; }

        if (timeSlot) {
          if (!byTimeSlot[timeSlot]) byTimeSlot[timeSlot] = { boards: 0, dropoffs: 0 };
          byTimeSlot[timeSlot].boards += boards;
          byTimeSlot[timeSlot].dropoffs += dropoffs;
        }
      }
    }

    const avgPassengers = rows > 0 ? (totalPassengers / rows).toFixed(2) : 0;
    res.json({ totalBoards, totalDropoffs, avgPassengers, byDirection, byTimeSlot, sampledRuns: Math.min(files.length, 50), totalRuns: files.length });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Get geodata (experiment IDs + geojson paths) for a simulation
app.get('/api/simulations/:id/geodata', (req, res) => {
  const { id } = req.params;
  if (!id.match(/^SIMULATION_\d{8}_\d{6}$/)) {
    return res.status(400).json({ error: 'Invalid simulation ID' });
  }

  const simPath = path.join(DATA_DIR, id);
  if (!fs.existsSync(simPath)) {
    return res.status(404).json({ error: 'Simulation not found' });
  }

  // Detect experiment IDs from includes/ROUTE subdirs (e.g. E01, E02)
  const routeIncludesPath = path.join(simPath, 'includes', 'ROUTE');
  let expIds = [];
  if (fs.existsSync(routeIncludesPath)) {
    expIds = fs.readdirSync(routeIncludesPath, { withFileTypes: true })
      .filter(e => e.isDirectory())
      .map(e => e.name)
      .sort();
  }

  const GEODATA_BASE = path.join(__dirname, '..', 'data', 'known_data', 'geodata');

  const experiments = expIds.map(expId => {
    const expGeoPath = path.join(GEODATA_BASE, expId);
    if (!fs.existsSync(expGeoPath)) return null;

    // Build URL paths (served via /data static route)
    const base = `/data/known_data/geodata/${expId}`;
    return {
      expId,
      toA: {
        route: `${base}/to_A/ROUTE/${expId}route_toA.geojson`,
        stops: `${base}/to_A/STOPS/${expId}stops_toA.geojson`,
      },
      toB: {
        route: `${base}/to_B/ROUTE/${expId}route_toB.geojson`,
        stops: `${base}/to_B/STOPS/${expId}stops_toB.geojson`,
      },
    };
  }).filter(Boolean);

  res.json({ experiments });
});

// Prepare new simulation: run prepare_simulation.sh and return the new simId
app.post('/api/simulations/prepare', (req, res) => {
  const bashScriptsDir = path.join(__dirname, '..', 'bash_scripts');
  const scriptPath = path.join(bashScriptsDir, 'prepare_simulation.sh');
  const lastSimFile = path.join(bashScriptsDir, '.last_simulation');

  if (!fs.existsSync(scriptPath)) {
    return res.status(404).json({ error: 'prepare_simulation.sh not found' });
  }

  execFile('bash', [scriptPath], { cwd: bashScriptsDir, timeout: 120000 }, (err, stdout, stderr) => {
    if (err) return res.status(500).json({ error: err.message, stderr });
    try {
      const baseDirLine = fs.readFileSync(lastSimFile, 'utf8').trim();
      const simId = path.basename(baseDirLine);
      if (!simId.match(/^SIMULATION_\d{8}_\d{6}$/)) {
        return res.status(500).json({ error: 'Invalid simulation ID returned by prepare script: ' + simId });
      }
      res.json({ simId });
    } catch (readErr) {
      res.status(500).json({ error: 'Could not read simulation ID: ' + readErr.message });
    }
  });
});

// Get simulation input files (buses JSON + CSV params)
app.get('/api/simulations/:id/inputs', (req, res) => {
  const { id } = req.params;
  if (!id.match(/^SIMULATION_\d{8}_\d{6}$/)) {
    return res.status(400).json({ error: 'Invalid simulation ID' });
  }

  const simPath = path.join(DATA_DIR, id);
  const inputsPath = resolveInputsPath(simPath);

  if (!inputsPath) {
    return res.status(404).json({ error: 'Inputs directory not found. Has the simulation been prepared?' });
  }

  try {
    const buses = JSON.parse(fs.readFileSync(path.join(inputsPath, 'input_data_buses.json'), 'utf8'));

    const parseCSVRows = (filepath) => {
      const content = fs.readFileSync(filepath, 'utf8');
      const lines = content.trim().split('\n');
      if (lines.length === 0) return [];
      const headers = lines[0].split(',').map(h => h.trim());
      return lines.slice(1).filter(l => l.trim()).map(line => {
        const values = line.split(',');
        const row = {};
        headers.forEach((h, i) => { row[h] = values[i]?.trim() ?? ''; });
        return row;
      });
    };

    const stopsToA      = parseCSVRows(path.join(inputsPath, 'input_data_E01_toA.csv'));
    const stopsToB      = parseCSVRows(path.join(inputsPath, 'input_data_E01_toB.csv'));
    const timesStopsToA = parseCSVRows(path.join(inputsPath, 'input_times_stops_toA.csv'));
    const timesStopsToB = parseCSVRows(path.join(inputsPath, 'input_times_stops_toB.csv'));
    const description   = parseDescription(simPath);

    res.json({ buses, stopsToA, stopsToB, timesStopsToA, timesStopsToB, description });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Save simulation input files + description.txt
app.post('/api/simulations/:id/inputs', (req, res) => {
  const { id } = req.params;
  if (!id.match(/^SIMULATION_\d{8}_\d{6}$/)) {
    return res.status(400).json({ error: 'Invalid simulation ID' });
  }

  const simPath = path.join(DATA_DIR, id);
  const inputsPath = resolveInputsPath(simPath);

  if (!inputsPath) {
    return res.status(404).json({ error: 'Inputs directory not found' });
  }

  try {
    const { description, buses, stopsToA, stopsToB, timesStopsToA, timesStopsToB } = req.body;

    // Write description.txt
    const descLines = [];
    if (description?.title)       descLines.push(`title "${description.title}"`);
    if (description?.description) descLines.push(`description "${description.description}"`);
    descLines.push(`line ${description?.line || 401}`); //HARDCODDED
    fs.writeFileSync(path.join(simPath, 'description.txt'), descLines.join('\n') + '\n');

    // Write buses JSON
    if (buses) {
      fs.writeFileSync(path.join(inputsPath, 'input_data_buses.json'), JSON.stringify(buses, null, 2));
    }

    const writeCSV = (filepath, rows) => {
      if (!rows || rows.length === 0) return;
      const headers = Object.keys(rows[0]);
      const lines = [headers.join(',')];
      for (const row of rows) lines.push(headers.map(h => row[h] ?? '').join(','));
      fs.writeFileSync(filepath, lines.join('\n') + '\n');
    };

    if (stopsToA)      writeCSV(path.join(inputsPath, 'input_data_E01_toA.csv'),      stopsToA);
    if (stopsToB)      writeCSV(path.join(inputsPath, 'input_data_E01_toB.csv'),      stopsToB);
    if (timesStopsToA) writeCSV(path.join(inputsPath, 'input_times_stops_toA.csv'), timesStopsToA);
    if (timesStopsToB) writeCSV(path.join(inputsPath, 'input_times_stops_toB.csv'), timesStopsToB);

    res.json({ message: 'Configuración guardada correctamente' });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Launch batch simulation (run_simulation.sh) for a prepared simulation
app.post('/api/simulations/:id/run', (req, res) => {
  const { id } = req.params;
  if (!id.match(/^SIMULATION_\d{8}_\d{6}$/)) {
    return res.status(400).json({ error: 'Invalid simulation ID' });
  }

  const bashScriptsDir = path.join(__dirname, '..', 'bash_scripts');
  const scriptPath = path.join(bashScriptsDir, 'run_simulation.sh');

  if (!fs.existsSync(scriptPath)) {
    return res.status(404).json({ error: 'run_simulation.sh not found' });
  }

  // Point .last_simulation at this simulation so run_simulation.sh picks it up
  const lastSimFile = path.join(bashScriptsDir, '.last_simulation');
  fs.writeFileSync(lastSimFile, `../data/logs/${id}\n`);

  const proc = spawn('bash', [scriptPath], {
    cwd: bashScriptsDir,
    detached: true,
    stdio: 'ignore',
  });
  proc.unref();

  

  res.json({ message: 'Simulación lanzada', simId: id });
});

// Trigger new simulation
app.post('/api/simulations/generate', (req, res) => {
  const scriptPath = path.join(__dirname, '..', '..', 'run_simulation.sh');
  if (!fs.existsSync(scriptPath)) {
    return res.status(202).json({ message: 'Simulation trigger not configured. Place run_simulation.sh in the project root.' });
  }
  execFile('bash', [scriptPath], { timeout: 5000 }, (err) => {
    if (err) return res.status(500).json({ error: err.message });
    res.json({ message: 'Simulation started' });
  });
});

// Delete a simulation (irreversible — removes the entire data/logs/:id directory)
app.delete('/api/simulations/:id', (req, res) => {
  const { id } = req.params;
  if (!id.match(/^SIMULATION_\d{8}_\d{6}$/)) {
    return res.status(400).json({ error: 'Invalid simulation ID' });
  }
  const simPath = path.join(DATA_DIR, id);
  if (!fs.existsSync(simPath)) {
    return res.status(404).json({ error: 'Simulation not found' });
  }
  try {
    fs.rmSync(simPath, { recursive: true, force: true });
    res.json({ message: 'Simulation deleted' });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Trigger chart generation via Python
app.post('/api/simulations/:id/generate-charts', (req, res) => {
  const { id } = req.params;
  if (!id.match(/^SIMULATION_\d{8}_\d{6}$/)) {
    return res.status(400).json({ error: 'Invalid simulation ID' });
  }

  const simPath = path.join(DATA_DIR, id);
  if (!fs.existsSync(simPath)) {
    return res.status(404).json({ error: 'Simulation not found' });
  }

  const pythonScript = path.join(__dirname, '..', '..', 'generate_charts.py');
  if (!fs.existsSync(pythonScript)) {
    return res.status(202).json({ message: 'Chart generation not configured. Place generate_charts.py in the project root.' });
  }

  execFile('python3', [pythonScript, simPath], { timeout: 60000 }, (err) => {
    if (err) return res.status(500).json({ error: err.message });
    res.json({ message: 'Charts generated' });
  });
});

// Get all plots info for a simulation (general stats, stop plots, bus plots, schedule)
app.get('/api/simulations/:id/plots-info', (req, res) => {
  const { id } = req.params;
  if (!id.match(/^SIMULATION_\d{8}_\d{6}$/)) {
    return res.status(400).json({ error: 'Invalid simulation ID' });
  }

  const simPath = path.join(DATA_DIR, id);
  if (!fs.existsSync(simPath)) {
    return res.status(404).json({ error: 'Simulation not found' });
  }

  const plotsPath = path.join(simPath, 'PLOTS');
  const urlBase = `/data/logs/${id}/PLOTS`;

  // General occupation stats
  let generalStats = null;
  try {
    generalStats = JSON.parse(
      fs.readFileSync(path.join(plotsPath, 'json_output_general_info.json'), 'utf8')
    );
  } catch (_) {}

  // Per-bus metrics (NaN is invalid JSON — replace before parsing)
  let busMetrics = null;
  try {
    const raw = fs.readFileSync(path.join(plotsPath, 'buses', 'general_info.json'), 'utf8');
    busMetrics = JSON.parse(raw.replace(/\bNaN\b/g, 'null'));
  } catch (_) {}

  // Bus schedule (departure timetable)
  let busSchedule = null;
  try {
    const inputsPath = resolveInputsPath(simPath);
    if (inputsPath) {
      busSchedule = JSON.parse(
        fs.readFileSync(path.join(inputsPath, 'input_data_buses.json'), 'utf8')
      );
    }
  } catch (_) {}

  // Stop plots (general): { toA: { stopId: url }, toB: { stopId: url } }
  // PNG names: occupation_per_timeslot_STOPID.png
  const stopPlotsGeneral = { toA: {}, toB: {} };
  const stopGeneralPattern = /^occupation_per_timeslot_(\d+)\.png$/;

  // Stop plots (per-timeslot comparison): { toA: { stopId: { hour: url } }, toB: ... }
  // PNG names: occupation_comparaison_STOPID_per_timeslot_HOUR.png
  const stopPlots = { toA: {}, toB: {} };
  const stopPattern = /^occupation_comparaison_(\d+)_per_timeslot_(\d+)\.png$/;

  const toAStopsPath = path.join(plotsPath, 'to_A', 'stops');
  if (fs.existsSync(toAStopsPath)) {
    fs.readdirSync(toAStopsPath).forEach(f => {
      const mg = f.match(stopGeneralPattern);
      if (mg) { stopPlotsGeneral.toA[mg[1]] = `${urlBase}/to_A/stops/${f}`; return; }
      const m = f.match(stopPattern);
      if (!m) return;
      const [, stopId, hour] = m;
      if (!stopPlots.toA[stopId]) stopPlots.toA[stopId] = {};
      stopPlots.toA[stopId][hour] = `${urlBase}/to_A/stops/${f}`;
    });
  }

  const toBStopsPath = path.join(plotsPath, 'to_B', 'stops');
  if (fs.existsSync(toBStopsPath)) {
    fs.readdirSync(toBStopsPath).forEach(f => {
      const mg = f.match(stopGeneralPattern);
      if (mg) { stopPlotsGeneral.toB[mg[1]] = `${urlBase}/to_B/stops/${f}`; return; }
      const m = f.match(stopPattern);
      if (!m) return;
      const [, stopId, hour] = m;
      if (!stopPlots.toB[stopId]) stopPlots.toB[stopId] = {};
      stopPlots.toB[stopId][hour] = `${urlBase}/to_B/stops/${f}`;
    });
  }

  // Per-stop and times-between-stops general info
  // { toA: { stopId: { Occupation_percentage, Mean_await_time_general, ... }, times_stops: { 'from-to': {...} } }, toB: {...} }
  const stopGeneralInfo = { toA: null, toB: null };
  try {
    stopGeneralInfo.toA = JSON.parse(
      fs.readFileSync(path.join(plotsPath, 'to_A', 'general_info_toA.json'), 'utf8')
    );
  } catch (_) {}
  try {
    stopGeneralInfo.toB = JSON.parse(
      fs.readFileSync(path.join(plotsPath, 'to_B', 'general_info_toB.json'), 'utf8')
    );
  } catch (_) {}

  // Times-between-stops plots: { toA: { 'fromStop-toStop': { hour: url } }, toB: {...} }
  // PNG names: time_between_stops_comparaison_FROM-TO_per_timeslot_HOUR.png
  const timesPlots = { toA: {}, toB: {} };
  const timesPattern = /^time_between_stops_comparaison_(\d+-\d+)_per_timeslot_(\d+)\.png$/;

  const toATimesPath = path.join(plotsPath, 'to_A', 'times');
  if (fs.existsSync(toATimesPath)) {
    fs.readdirSync(toATimesPath).forEach(f => {
      const m = f.match(timesPattern);
      if (!m) return;
      const [, sectionKey, hour] = m;
      if (!timesPlots.toA[sectionKey]) timesPlots.toA[sectionKey] = {};
      timesPlots.toA[sectionKey][hour] = `${urlBase}/to_A/times/${f}`;
    });
  }

  const toBTimesPath = path.join(plotsPath, 'to_B', 'times');
  if (fs.existsSync(toBTimesPath)) {
    fs.readdirSync(toBTimesPath).forEach(f => {
      const m = f.match(timesPattern);
      if (!m) return;
      const [, sectionKey, hour] = m;
      if (!timesPlots.toB[sectionKey]) timesPlots.toB[sectionKey] = {};
      timesPlots.toB[sectionKey][hour] = `${urlBase}/to_B/times/${f}`;
    });
  }

  // Bus plots: { busId: { toA: [url_trip0, url_trip1, ...], toB: [...] } }
  // PNG names: mean_occupation_per_stop_(toA|toB)_BUSID_TRIPIDX.png
  const busPlots = {};
  const busesPlotPath = path.join(plotsPath, 'buses');
  const busPlotPattern = /^mean_occupation_per_stop_(toA|toB)_(\d+)_(\d+)\.png$/;

  if (fs.existsSync(busesPlotPath)) {
    fs.readdirSync(busesPlotPath).forEach(f => {
      const m = f.match(busPlotPattern);
      if (!m) return;
      const [, dir, busId, idx] = m;
      if (!busPlots[busId]) busPlots[busId] = { toA: [], toB: [] };
      busPlots[busId][dir][parseInt(idx)] = `${urlBase}/buses/${f}`;
    });
    // Remove sparse array holes
    Object.values(busPlots).forEach(b => {
      b.toA = b.toA.filter(Boolean);
      b.toB = b.toB.filter(Boolean);
    });
  }

  // Aggregate direction/general plots
  const generalPlots = {};
  const gpBase = urlBase;
  if (fs.existsSync(path.join(plotsPath, 'general', 'occupation_per_timeslot_general.png')))
    generalPlots.general = `${gpBase}/general/occupation_per_timeslot_general.png`;
  if (fs.existsSync(path.join(plotsPath, 'to_A', 'occupation_per_timeslot_toA.png')))
    generalPlots.toA = `${gpBase}/to_A/occupation_per_timeslot_toA.png`;
  if (fs.existsSync(path.join(plotsPath, 'to_B', 'occupation_per_timeslot_toB.png')))
    generalPlots.toB = `${gpBase}/to_B/occupation_per_timeslot_toB.png`;

  res.json({ generalStats, busSchedule, busMetrics, stopPlots, stopPlotsGeneral, busPlots, generalPlots, stopGeneralInfo, timesPlots });
});


// ---- WebSocket: simulation progress publisher ----

// Returns progress info for every simulation that is not yet complete.
// During the GAMA batch run, CSVs land in TEST_MOBILITY/logs/RESULTS/;
// after the cleanup phase they are moved to RESULTS/ at the sim root.
function getInProgressSimulations() {
  try {
    const entries = fs.readdirSync(DATA_DIR, { withFileTypes: true });
    return entries
      .filter(e => e.isDirectory() && /^SIMULATION_\d{8}_\d{6}$/.test(e.name))
      .map(e => {
        const id = e.name;
        const simPath = path.join(DATA_DIR, id);

        // Try active-run path first, fall back to post-cleanup path
        const activePath    = path.join(simPath, 'TEST_MOBILITY', 'logs', 'RESULTS');
        const completedPath = path.join(simPath, 'RESULTS');
        const resultsPath   = fs.existsSync(activePath) ? activePath : completedPath;

        let runCount = 0;
        try {
          runCount = fs.readdirSync(resultsPath).filter(f => f.endsWith('.csv')).length;
        } catch (_) {}

        const percentage = Math.min(100, Math.round(runCount / 10)); // 1000 total
        const status = runCount >= 1000 ? 'Completada' : 'En progreso';
        return { id, runCount, percentage, status };
      })
      .filter(s => s.status !== 'Completada');
  } catch (_) {
    return [];
  }
}

io.on('connection', (socket) => {
  // Send current snapshot immediately so the subscriber is up-to-date on connect
  socket.emit('sim_progress', getInProgressSimulations());
});

// Tracks sim IDs that were in-progress on the previous tick, used to detect
// the transition to "stage 1 complete" (1000 CSVs generated).
// When stage 2 (chart generation) is integrated into the pipeline, update TODO
// getInProgressSimulations() to also require hasCharts === true before removing
// a sim from the in-progress set, and change the condition below accordingly.
const _trackedInProgress = new Set();

// Broadcast in-progress sim states to all connected clients every second.
// Also fires sim_completed when a sim transitions out of the in-progress list.
setInterval(() => {
  const inProgress = getInProgressSimulations();
  const currentIds = new Set(inProgress.map(s => s.id));

  // Detect completions: was tracked last tick, now gone from in-progress list
  for (const id of _trackedInProgress) {
    if (!currentIds.has(id)) {
      const { title } = parseDescription(path.join(DATA_DIR, id));
      io.emit('sim_completed', { id, title });
    }
  }

  // Sync tracker to current state
  _trackedInProgress.clear();
  currentIds.forEach(id => _trackedInProgress.add(id));

  if (io.engine.clientsCount > 0) {
    io.emit('sim_progress', inProgress);
  }
}, 1000);

// ---- Start server ----

httpServer.listen(PORT, () => {
  console.log(`EMT GAMA Dashboard running at http://localhost:${PORT}`);
});
