const http = require('http');
const express = require('express');
const path = require('path');
const fs = require('fs');
const { execFile, spawn } = require('child_process');
const { Server } = require('socket.io');
const crypto = require('crypto');

const app = express();
const httpServer = http.createServer(app);
const io = new Server(httpServer);
const PORT = 3000;

const DATA_DIR = path.join(__dirname, '..', 'data', 'logs');
const PAGES_DIR = path.join(__dirname, 'pages');
const IMGS_DIR = path.join(__dirname,'..', 'img');


const ENGINES = {
  with_agents:    { type: 'gama', model: 'modelpassengersfinal_with_passenger_agents.gaml' },
  without_agents: { type: 'gama', model: 'mobility_performance.gaml' },
  c_engine:       { type: 'c' },
};
const DEFAULT_MODEL_KEY = 'without_agents';
const engineFor = (key) => ENGINES[key] || ENGINES[DEFAULT_MODEL_KEY];


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




// ---- Simulation inputs ----
//
// Input contract (all files come from BASE_DATA via prepare_simulation.sh):
//   final_input.json                buses/departures      web r/w  C, GAMA, analysis
//   input_data_E01_to{A,B}.csv      boardings             web r/w  C, GAMA
//     Stop,Timeslot,DistributionType,Param1,Param2
//     DistributionType: NORMAL (mu,sigma) | NEGATIVE BINOMIAL (r,p) | GEOMETRICAL (p,-)
//   alighting_params_to{A,B}.csv    alightings            web r/w  C only
//     Stop,TimeSlot,family,alpha,beta,P
//     family: betabinom (alpha,beta) | binomial (P) | TERMINAL | TERMINAL_STOP
//     Fraction of the bus occupancy that gets off at the stop.
//   input_times_stops_to{A,B}.csv   travel times          web r/w  C, GAMA
//   input_stops.txt                 stop order            read-only (C reference copy)
//
// The C parser tells distribution families apart by string length, so family
// names and column order must be written back exactly as they were read.
const INPUT_FILES = {
  stopsToA:      'input_data_E01_toA.csv',
  stopsToB:      'input_data_E01_toB.csv',
  alightToA:     'alighting_params_toA.csv',
  alightToB:     'alighting_params_toB.csv',
  timesStopsToA: 'input_times_stops_toA.csv',
  timesStopsToB: 'input_times_stops_toB.csv',
};

// Every directory holding a copy of the inputs of a prepared (not yet run)
// simulation. The GAMA and C projects each get their own copy and the chosen
// engine reads its own, so edits are written to all of them.
function editableInputDirs(simPath) {
  return [
    path.join(simPath, 'TEST_MOBILITY', 'includes', 'INPUTS'),
    path.join(simPath, 'C_REWRITE', 'data'),
  ].filter(p => fs.existsSync(p));
}

// Resolve the INPUTS directory for a simulation (prepared or already run)
function resolveInputsPath(simPath) {
  const candidates = [
    ...editableInputDirs(simPath),
    path.join(simPath, 'includes', 'INPUTS'), // finished GAMA run
    path.join(simPath, 'includes'),           // finished C run
  ];
  return candidates.find(p => fs.existsSync(path.join(p, 'final_input.json'))) || null;
}

const MAX_SEED = (1n << 64n) - 1n;

// Returns the seed as a decimal string, null if empty, or throws if invalid.
function normalizeSeed(raw) {
  const s = String(raw ?? '').trim();
  if (s === '') return null;
  if (!/^\d{1,20}$/.test(s) || BigInt(s) > MAX_SEED) {
    throw new Error('La semilla debe ser un entero entre 0 y 18446744073709551615');
  }
  return BigInt(s).toString();
}

function randomSeed() {
  return crypto.randomBytes(8).readBigUInt64BE().toString();
}

// description.txt values live on a single line between quotes
function descValue(str) {
  return String(str).replace(/[\r\n]+/g, ' ').replace(/"/g, "'");
}

function replicaProgress(simPath, engineType) {
  if (engineType === 'c') {
    const done = fs.existsSync(path.join(simPath, '.done'));
    return { runCount: done ? 1000 : 0, percentage: done ? 100 : 0 };
  }
  const activePath    = path.join(simPath, 'TEST_MOBILITY', 'logs', 'RESULTS');
  const completedPath = path.join(simPath, 'RESULTS');
  const resultsPath   = fs.existsSync(activePath) ? activePath : completedPath;
  let runCount = 0;
  try {
    runCount = fs.readdirSync(resultsPath).filter(f => f.endsWith('.csv')).length;
  } catch (_) {}
  return { runCount, percentage: Math.min(100, Math.round(runCount / 10)) };
}


// Parse description.txt: `title "..."`, `description "..."`, `line "..."`
function parseDescription(simPath) {
  const descPath = path.join(simPath, 'description.txt');
  const empty = { title: null, description: null, line: null, model: null, seed: null };
  if (!fs.existsSync(descPath)) return empty;
  try {
    const lines = fs.readFileSync(descPath, 'utf8').split('\n');
    let title = null, description = null, line = null, model = null, seed = null;
    for (const rawLine of lines) {
      const sp = rawLine.indexOf(' ');
      if (sp === -1) continue;
      const key = rawLine.slice(0, sp).trim();
      let val = rawLine.slice(sp + 1).trim();
      val = val.replace(/^"(.*)"$/, '$1'); // strip surrounding quotes
      if (key === 'title') title = val;
      else if (key === 'description') description = val;
      else if (key === 'line') line = val;
      else if (key === 'model') model = val;
      else if (key === 'seed') seed = val;
    }
    return { title, description, line, model, seed };
  } catch (_) {
    return empty;
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
        runCount = replicaProgress(simPath, engineFor(parseDescription(simPath).model).type).runCount;

        const hasCharts = fs.existsSync(chartsPath) && fs.readdirSync(chartsPath).some(f => f.endsWith('.json'));

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
        const { title, description, model} = parseDescription(simPath);
        return { id, datetime, runCount, hasCharts, title, description, status, model };
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
  runCount = replicaProgress(simPath, engineFor(parseDescription(simPath).model).type).runCount;

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

  const { title, description, model } = parseDescription(simPath);
  res.json({ id, datetime, runCount, charts, logContent, title, description , model});
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


  // It should parse it from the description.txt



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
    const buses = JSON.parse(fs.readFileSync(path.join(inputsPath, 'final_input.json'), 'utf8'));

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

    const data = { buses, description: parseDescription(simPath) };
    for (const [key, file] of Object.entries(INPUT_FILES)) {
      const filepath = path.join(inputsPath, file);
      data[key] = fs.existsSync(filepath) ? parseCSVRows(filepath) : [];
    }

    res.json(data);
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
  const inputDirs = editableInputDirs(simPath);

  if (inputDirs.length === 0) {
    return res.status(404).json({ error: 'Inputs directory not found' });
  }

  const { description, buses } = req.body;

  let seed;
  try {
    seed = normalizeSeed(description?.seed) ?? randomSeed();
  } catch (err) {
    return res.status(400).json({ error: err.message });
  }

  try {
    // Write description.txt
    const descLines = [];
    if (description?.title)       descLines.push(`title "${descValue(description.title)}"`);
    if (description?.description) descLines.push(`description "${descValue(description.description)}"`);
    descLines.push(`line ${description?.line || 401}`); //HARDCODDED
    descLines.push(`model ${ENGINES[description?.model] ? description.model : DEFAULT_MODEL_KEY}`);
    descLines.push(`seed ${seed}`);
    fs.writeFileSync(path.join(simPath, 'description.txt'), descLines.join('\n') + '\n');

    const writeCSV = (filepath, rows) => {
      if (!rows || rows.length === 0) return;
      const headers = Object.keys(rows[0]);
      const lines = [headers.join(',')];
      for (const row of rows) lines.push(headers.map(h => row[h] ?? '').join(','));
      fs.writeFileSync(filepath, lines.join('\n') + '\n');
    };

    for (const dir of inputDirs) {
      if (buses) {
        fs.writeFileSync(path.join(dir, 'final_input.json'), JSON.stringify(buses, null, 2));
      }
      for (const [key, file] of Object.entries(INPUT_FILES)) {
        if (req.body[key]) writeCSV(path.join(dir, file), req.body[key]);
      }
    }

    res.json({ message: 'Configuración guardada correctamente', seed });
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

  // Resolve the chosen GAML model from description.txt against the allowlist and
  // hand it to the bash scripts via GAMA_MODEL_NAME.
  const { model: modelKey, seed } = parseDescription(path.join(DATA_DIR, id));
  if (!seed) {
    return res.status(400).json({ error: 'La simulación no tiene semilla. Guarda la configuración antes de lanzarla.' });
  }

  // Point .last_simulation at this simulation so run_simulation.sh picks it up
  const lastSimFile = path.join(bashScriptsDir, '.last_simulation');
  fs.writeFileSync(lastSimFile, `../data/logs/${id}\n`);

  const modelFile = engineFor(modelKey).model || '';

  const proc = spawn('bash', [scriptPath], {
    cwd: bashScriptsDir,
    detached: true,
    stdio: 'ignore',
    env: { ...process.env, GAMA_MODEL_NAME: modelFile },
  });
  proc.unref();

  //Emit an alert via websockets to call for every index instance to rebuil.d the page in order to show the new sim info bar
  io.emit('new_sim_launched', { id, title: req.body?.title || id });

  res.json({ message: 'Simulación lanzada', simId: id });
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
        fs.readFileSync(path.join(inputsPath, 'final_input.json'), 'utf8')
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
        const chartsPath = path.join(simPath, 'PLOTS');
        const engineType = engineFor(parseDescription(simPath).model).type;
        const { runCount, percentage } = replicaProgress(simPath, engineType);

        let status = '';
        if (runCount >= 1000){
          const hasCharts = fs.existsSync(chartsPath) && fs.readdirSync(chartsPath).some(f => f.endsWith('.json'));
          if (hasCharts){
            status = 'Completada';
          }
          else{
            status = 'Esperando Gr\u00e1ficas';
          }
        }
        else{
          status = 'En progreso';
        }
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

// Tracks sim IDs that were in-progress on the previous tick
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
      const simPath = path.join(DATA_DIR, id);
      if (!fs.existsSync(simPath)) continue;  // deleted, not completed
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
