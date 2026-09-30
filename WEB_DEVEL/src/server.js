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
const SIM_ID_RE = /^SIMULATION_\d{8}_\d{6}$/;
const BASH_SCRIPTS_DIR = path.join(__dirname, '..', 'bash_scripts');
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
    // The C engine writes a single results.csv, moved to RESULTS/ once the
    // binary has finished; from then on only the analysis is pending.
    const simulated = fs.existsSync(path.join(simPath, '.done'))
                   || fs.existsSync(path.join(simPath, 'RESULTS', 'results.csv'));
    return { runCount: simulated ? 1000 : 0, percentage: simulated ? 100 : 0 };
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


// ---- Simulation status ----
//
// run_simulation.sh leaves two markers in the simulation directory:
//   .error  one line per failure, "time|PHASE|exitCode|message" (first = cause)
//   .done   simulation + analysis finished without errors (plots complete)
const STATUS = {
  PREPARED:      'Preparada',
  QUEUED:        'En cola',
  RUNNING:       'En progreso',
  WAITING_PLOTS: 'Esperando Gr\u00e1ficas',
  DONE:          'Completada',
  ERROR:         'Error',
};

function readErrors(simPath) {
  let raw;
  try { raw = fs.readFileSync(path.join(simPath, '.error'), 'utf8'); } catch (_) { return null; }
  const errors = raw.split('\n').filter(l => l.trim()).map(line => {
    const [time, phase, code, ...msg] = line.split('|');
    return { time, phase, code: Number(code), message: msg.join('|') };
  });
  return errors.length ? errors : null;
}

// Simulations that finished before the .done marker existed: the pipeline
// log ends with "=== Pipeline finished ===" only after the analysis step.
// Finished is a terminal state, so positive answers are cached.
const _legacyFinished = new Set();
function legacyFinished(simPath) {
  if (_legacyFinished.has(simPath)) return true;
  if (!fs.existsSync(path.join(simPath, 'PLOTS', 'json_output_general_info.json'))) return false;
  try {
    const log = fs.readdirSync(simPath).find(f => f.endsWith('.log'));
    if (!log) return false;
    const fd = fs.openSync(path.join(simPath, log), 'r');
    const size = fs.fstatSync(fd).size;
    const buf = Buffer.alloc(Math.min(size, 4096));
    fs.readSync(fd, buf, 0, buf.length, size - buf.length);
    fs.closeSync(fd);
    if (!buf.toString('utf8').includes('=== Pipeline finished ===')) return false;
  } catch (_) {
    return false;
  }
  _legacyFinished.add(simPath);
  return true;
}

function chartsReady(simPath) {
  return fs.existsSync(path.join(simPath, '.done')) || legacyFinished(simPath);
}

// { status, runCount, percentage, hasCharts, errors } for a simulation directory
function simStatus(simPath) {
  const engineType = engineFor(parseDescription(simPath).model).type;
  const { runCount, percentage } = replicaProgress(simPath, engineType);
  const errors = readErrors(simPath);
  const hasCharts = !errors && chartsReady(simPath);

  let status = STATUS.RUNNING;
  if (isQueued(simPath))       status = STATUS.QUEUED;
  else if (errors)             status = STATUS.ERROR;
  else if (hasCharts)          status = STATUS.DONE;
  else if (runCount >= 1000)   status = STATUS.WAITING_PLOTS;
  else if (!wasLaunched(simPath)) status = STATUS.PREPARED;

  return { status, runCount, percentage, hasCharts, errors };
}

// ---- Run queue ----
//
// Every simulation is identified by its own directory, passed explicitly to
// prepare_simulation.sh / run_simulation.sh (no shared .last_simulation).
// Launch requests are queued with a <sim>/.queued marker (so the queue
// survives a server restart) and started when there is room:
//   - at most MAX_RUNS runs at once, and MAX_RUNS_PER_ENGINE per engine;
//   - an "exclusive" run (energy measurements) starts only when nothing else
//     is running and blocks everything behind it until it finishes. The
//     resource monitor reads the whole container cgroup, so only exclusive
//     runs have isolated metrics.
// run_simulation.sh writes <sim>/.pid while alive; on startup, runs whose
// process is gone without .done/.error are marked as failed.
const MAX_RUNS = Number(process.env.EMT_MAX_RUNS) || 2;
const MAX_RUNS_PER_ENGINE = {
  // One GAMA batch already uses most of the heap and cores of the container.
  gama: Number(process.env.EMT_MAX_GAMA_RUNS) || 1,
  c:    Number(process.env.EMT_MAX_C_RUNS)    || 2,
};

// id -> { pid, engine, exclusive, adopted } for runs started by (or found
// alive by) this server process
const running = new Map();

function isQueued(simPath) {
  return fs.existsSync(path.join(simPath, '.queued'));
}

// Anything run_simulation.sh leaves behind once started
function wasLaunched(simPath) {
  return running.has(path.basename(simPath))
      || ['.pid', 'MONITOR', 'RESULTS', '.error', '.done'].some(f => fs.existsSync(path.join(simPath, f)));
}

function processAlive(pid) {
  try {
    process.kill(pid, 0);
  } catch (err) {
    return err.code === 'EPERM';
  }
  // Guard against PID reuse after a restart
  try {
    return fs.readFileSync(`/proc/${pid}/cmdline`, 'utf8').includes('run_simulation.sh');
  } catch (_) {
    return true; // no /proc (non-Linux): trust kill(0)
  }
}

function nowStamp() {
  return new Date().toISOString().replace('T', ' ').slice(0, 19);
}

// Records a RUNNER error unless the pipeline already finished or reported one
function recordRunnerError(id, message) {
  const simPath = path.join(DATA_DIR, id);
  if (!fs.existsSync(simPath) || readErrors(simPath) || fs.existsSync(path.join(simPath, '.done'))) return;
  try {
    fs.appendFileSync(path.join(simPath, '.error'), `${nowStamp()}|RUNNER|1|${message}\n`);
  } catch (_) {}
}

function queuedSims() {
  let entries = [];
  try { entries = fs.readdirSync(DATA_DIR); } catch (_) { return []; }
  return entries
    .filter(id => SIM_ID_RE.test(id) && !running.has(id))
    .map(id => {
      try {
        const q = JSON.parse(fs.readFileSync(path.join(DATA_DIR, id, '.queued'), 'utf8'));
        return { id, queuedAt: q.queuedAt || 0 };
      } catch (_) { return null; }
    })
    .filter(Boolean)
    .sort((a, b) => a.queuedAt - b.queuedAt || a.id.localeCompare(b.id));
}

function queuePosition(id) {
  return queuedSims().findIndex(q => q.id === id) + 1;
}

function canStart(engine, exclusive) {
  const runs = [...running.values()];
  if (runs.some(r => r.exclusive)) return false;
  if (exclusive) return runs.length === 0;
  return runs.length < MAX_RUNS
      && runs.filter(r => r.engine === engine).length < (MAX_RUNS_PER_ENGINE[engine] || 1);
}

// Highest number of simultaneous runs seen during each running simulation
function recordConcurrency() {
  const n = running.size;
  for (const [id, r] of running) {
    const file = path.join(DATA_DIR, id, '.concurrency');
    let info = { exclusive: r.exclusive, maxConcurrentRuns: 0 };
    try { info = { ...info, ...JSON.parse(fs.readFileSync(file, 'utf8')) }; } catch (_) {}
    if (n > info.maxConcurrentRuns) {
      info.maxConcurrentRuns = n;
      try { fs.writeFileSync(file, JSON.stringify(info) + '\n'); } catch (_) {}
    }
  }
}

function startRun(id) {
  const simPath = path.join(DATA_DIR, id);
  const { model: modelKey, exclusive } = parseDescription(simPath);
  const engine = engineFor(modelKey);
  fs.rmSync(path.join(simPath, '.queued'), { force: true });

  const proc = spawn('bash', [path.join(BASH_SCRIPTS_DIR, 'run_simulation.sh'), simPath], {
    cwd: BASH_SCRIPTS_DIR,
    detached: true,
    stdio: 'ignore',
    env: {
      ...process.env,
      GAMA_MODEL_NAME: engine.model || '',
      EMT_CONCURRENT_RUNS: String(running.size + 1),
      EMT_EXCLUSIVE: exclusive ? 'yes' : 'no',
    },
  });
  proc.unref();
  running.set(id, { pid: proc.pid, engine: engine.type, exclusive, adopted: false });
  recordConcurrency();

  // Safety net: if the pipeline dies without recording why (killed, bash
  // error before the markers exist...), record it so the UI shows Error.
  proc.on('exit', (code, signal) => {
    running.delete(id);
    if (code !== 0) {
      recordRunnerError(id, `run_simulation.sh terminated with ${signal ? `signal ${signal}` : `exit code ${code}`}`);
    }
    pumpQueue();
  });
  proc.on('error', (err) => {
    running.delete(id);
    recordRunnerError(id, `could not start run_simulation.sh: ${err.message}`);
    pumpQueue();
  });
}

// Start queued runs in FIFO order while limits allow. A queued exclusive run
// that cannot start yet blocks the ones behind it, so it is not starved.
function pumpQueue() {
  for (const { id } of queuedSims()) {
    const simPath = path.join(DATA_DIR, id);
    const { model, exclusive } = parseDescription(simPath);
    const engine = engineFor(model).type;
    if (canStart(engine, exclusive)) {
      try { startRun(id); } catch (err) { recordRunnerError(id, `could not start: ${err.message}`); }
    } else if (exclusive) {
      break;
    }
  }
}

// Runs inherited from a previous server process have no 'exit' event:
// poll them, and drop the ones whose process is gone.
function reapAdoptedRuns() {
  let changed = false;
  for (const [id, r] of running) {
    if (r.adopted && !processAlive(r.pid)) {
      running.delete(id);
      recordRunnerError(id, 'run_simulation.sh is no longer running (server or container restarted)');
      changed = true;
    }
  }
  if (changed) pumpQueue();
}

// On startup: adopt runs that are still alive, fail the ones that died with
// the previous server process, then resume the queue.
function recoverRuns() {
  let entries = [];
  try { entries = fs.readdirSync(DATA_DIR); } catch (_) { return; }
  for (const id of entries.filter(e => SIM_ID_RE.test(e))) {
    const pidFile = path.join(DATA_DIR, id, '.pid');
    if (!fs.existsSync(pidFile)) continue;
    const pid = Number(fs.readFileSync(pidFile, 'utf8').trim());
    if (pid && processAlive(pid)) {
      const { model, exclusive } = parseDescription(path.join(DATA_DIR, id));
      running.set(id, { pid, engine: engineFor(model).type, exclusive, adopted: true });
    } else {
      fs.rmSync(pidFile, { force: true });
      recordRunnerError(id, 'run_simulation.sh is no longer running (server or container restarted)');
    }
  }
  pumpQueue();
}

// New directory SIMULATION_<local time>; mkdir is atomic, so two requests in
// the same second get consecutive seconds instead of sharing a directory.
function reserveSimId() {
  fs.mkdirSync(DATA_DIR, { recursive: true });
  const pad = (n) => String(n).padStart(2, '0');
  let t = Date.now();
  for (let i = 0; i < 600; i++, t += 1000) {
    const d = new Date(t);
    const id = `SIMULATION_${d.getFullYear()}${pad(d.getMonth() + 1)}${pad(d.getDate())}`
             + `_${pad(d.getHours())}${pad(d.getMinutes())}${pad(d.getSeconds())}`;
    try {
      fs.mkdirSync(path.join(DATA_DIR, id));
      return id;
    } catch (err) {
      if (err.code !== 'EEXIST') throw err;
    }
  }
  throw new Error('Could not reserve a simulation id');
}

// Parse description.txt: `title "..."`, `description "..."`, `line "..."`
function parseDescription(simPath) {
  const descPath = path.join(simPath, 'description.txt');
  const empty = { title: null, description: null, line: null, model: null, seed: null, exclusive: false };
  if (!fs.existsSync(descPath)) return empty;
  try {
    const lines = fs.readFileSync(descPath, 'utf8').split('\n');
    let title = null, description = null, line = null, model = null, seed = null, exclusive = false;
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
      else if (key === 'exclusive') exclusive = val === 'yes';
    }
    return { title, description, line, model, seed, exclusive };
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
        const { status, runCount, hasCharts, errors } = simStatus(simPath);

        // Parse datetime from folder name: SIMULATION_YYYYMMDD_HHMMSS
        const match = id.match(/SIMULATION_(\d{8})_(\d{6})/);
        let datetime = null;
        if (match) {
          const d = match[1];
          const t = match[2];
          datetime = `${d.slice(0, 4)}-${d.slice(4, 6)}-${d.slice(6, 8)} ${t.slice(0, 2)}:${t.slice(2, 4)}:${t.slice(4, 6)}`;
        }
        const { title, description, model} = parseDescription(simPath);
        return { id, datetime, runCount, hasCharts, title, description, status, model,
                 error: errors ? errors[0] : null };
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

  const chartsPath = path.join(simPath, 'PLOTS');
  const { status, runCount, hasCharts, errors } = simStatus(simPath);

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
  res.json({ id, datetime, runCount, charts, logContent, title, description, model, status, hasCharts, errors });
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
  const scriptPath = path.join(BASH_SCRIPTS_DIR, 'prepare_simulation.sh');

  if (!fs.existsSync(scriptPath)) {
    return res.status(404).json({ error: 'prepare_simulation.sh not found' });
  }

  let simId;
  try {
    simId = reserveSimId();
  } catch (err) {
    return res.status(500).json({ error: err.message });
  }

  execFile('bash', [scriptPath, simId], { cwd: BASH_SCRIPTS_DIR, timeout: 120000 }, (err, stdout, stderr) => {
    if (err) {
      fs.rmSync(path.join(DATA_DIR, simId), { recursive: true, force: true });
      return res.status(500).json({ error: err.message, stderr });
    }
    res.json({ simId });
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
    descLines.push(`exclusive ${description?.exclusive ? 'yes' : 'no'}`);
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
  if (!SIM_ID_RE.test(id)) {
    return res.status(400).json({ error: 'Invalid simulation ID' });
  }

  const simPath = path.join(DATA_DIR, id);
  if (!fs.existsSync(simPath)) {
    return res.status(404).json({ error: 'Simulation not found' });
  }
  if (!fs.existsSync(path.join(BASH_SCRIPTS_DIR, 'run_simulation.sh'))) {
    return res.status(404).json({ error: 'run_simulation.sh not found' });
  }

  const { seed, exclusive } = parseDescription(simPath);
  if (!seed) {
    return res.status(400).json({ error: 'La simulación no tiene semilla. Guarda la configuración antes de lanzarla.' });
  }
  if (running.has(id) || isQueued(simPath)) {
    return res.status(409).json({ error: 'La simulación ya está en ejecución o en cola.' });
  }

  // A relaunch starts clean: results of the previous attempt no longer apply.
  for (const marker of ['.error', '.done']) fs.rmSync(path.join(simPath, marker), { force: true });
  fs.writeFileSync(path.join(simPath, '.queued'), JSON.stringify({ queuedAt: Date.now(), exclusive }) + '\n');
  pumpQueue();

  const started = running.has(id);
  const position = started ? 0 : queuePosition(id);

  //Emit an alert via websockets to call for every index instance to rebuil.d the page in order to show the new sim info bar
  io.emit('new_sim_launched', { id, title: parseDescription(simPath).title || id, queued: !started });

  res.json({
    message: started ? 'Simulación lanzada' : `Simulación en cola (posición ${position})`,
    simId: id,
    queued: !started,
    position,
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
  if (running.has(id)) {
    return res.status(409).json({ error: 'La simulación está en ejecución; espera a que termine para eliminarla.' });
  }
  try {
    // A queued simulation leaves the queue with its directory.
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

        const { status, runCount, percentage, errors } = simStatus(simPath);
        const position = status === STATUS.QUEUED ? queuePosition(id) : 0;
        return { id, runCount, percentage, status, position, error: errors ? errors[0] : null };
      })
      .filter(s => [STATUS.QUEUED, STATUS.RUNNING, STATUS.WAITING_PLOTS].includes(s.status));
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
  reapAdoptedRuns();
  const inProgress = getInProgressSimulations();
  const currentIds = new Set(inProgress.map(s => s.id));

  // Detect completions/failures: was tracked last tick, now gone from in-progress list
  for (const id of _trackedInProgress) {
    if (!currentIds.has(id)) {
      const simPath = path.join(DATA_DIR, id);
      if (!fs.existsSync(simPath)) continue;  // deleted, not completed
      const { title } = parseDescription(simPath);
      const { status, errors } = simStatus(simPath);
      if (status === STATUS.ERROR) io.emit('sim_failed', { id, title, error: errors[0] });
      else                         io.emit('sim_completed', { id, title });
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
  recoverRuns();
  console.log(`EMT GAMA Dashboard running at http://localhost:${PORT}`);
});
