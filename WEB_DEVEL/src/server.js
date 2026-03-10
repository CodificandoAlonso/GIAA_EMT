const express = require('express');
const path = require('path');
const fs = require('fs');
const { execFile } = require('child_process');

const app = express();
const PORT = 3000;

const DATA_DIR = path.join(__dirname, '..', 'data', 'logs');
const PAGES_DIR = path.join(__dirname, 'pages');

app.use(express.json());
app.use('/styles', express.static(path.join(__dirname, 'styles')));
app.use('/scripts', express.static(path.join(__dirname, 'scripts')));
app.use('/data', express.static(path.join(__dirname, '..', 'data')));

// ---- Pages ----

app.get('/', (req, res) => {
  res.sendFile(path.join(PAGES_DIR, 'index.html'));
});

app.get('/simulation/:id', (req, res) => {
  res.sendFile(path.join(PAGES_DIR, 'simulation.html'));
});




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
        const chartsPath = path.join(simPath, 'charts');

        let runCount = 0;
        try {
          runCount = fs.readdirSync(resultsPath).filter(f => f.endsWith('.csv')).length;
        } catch (_) {}

        const hasCharts = fs.existsSync(chartsPath) &&
          fs.readdirSync(chartsPath).some(f => f.endsWith('.png') || f.endsWith('.jpg'));

        // Parse datetime from folder name: SIMULATION_YYYYMMDD_HHMMSS
        const match = id.match(/SIMULATION_(\d{8})_(\d{6})/);
        let datetime = null;
        if (match) {
          const d = match[1];
          const t = match[2];
          datetime = `${d.slice(0, 4)}-${d.slice(4, 6)}-${d.slice(6, 8)} ${t.slice(0, 2)}:${t.slice(2, 4)}:${t.slice(4, 6)}`;
        }

        return { id, datetime, runCount, hasCharts };
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
  const chartsPath = path.join(simPath, 'charts');

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
      .map(f => `/data/logs/${id}/charts/${f}`);
  }

  // Read log file
  let logContent = null;
  try {
    const logFiles = fs.readdirSync(simPath).filter(f => f.endsWith('.log'));
    if (logFiles.length > 0) {
      const raw = fs.readFileSync(path.join(simPath, logFiles[0]), 'utf8');
      logContent = raw.split('\n').slice(0, 50).join('\n');
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

  res.json({ id, datetime, runCount, charts, logContent });
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

// Trigger new simulation (placeholder - adapt path to your script)
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

app.listen(PORT, () => {
  console.log(`EMT GAMA Dashboard running at http://localhost:${PORT}`);
});
