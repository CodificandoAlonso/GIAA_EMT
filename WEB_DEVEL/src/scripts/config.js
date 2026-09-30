// ============================================================
// config.js — Simulation parameter configuration
// ============================================================

// ---- Utilities ----

function toast(msg, type = 'info') {
  const container = document.getElementById('toast-container');
  const el = document.createElement('div');
  el.className = `toast ${type}`;
  el.textContent = msg;
  container.appendChild(el);
  setTimeout(() => el.remove(), 4000);
}

function escHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;')
    .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function getSimId() {
  const parts = window.location.pathname.split('/');
  return parts[parts.length - 1];
}

// ---- State ----

let simId = null;
let inputData = {
  buses: {}, stopsToA: [], stopsToB: [], alightToA: [], alightToB: [], timesStopsToA: [], timesStopsToB: [],
};
let currentView = 'buses';

// Route view state
let _routeFilter = 'general';   // 'general' | 'timeslot'
let _selectedTs  = 8;           // selected timeslot hour
let _currentInfoSel  = null;    // { type:'stop'|'section', stopId, sectionKey, dirKey, stopProps }
let _activeClearSel  = null;    // function to clear current SVG selection

// Bus view state
let _busViewFilter = 'physical'; // 'physical' | 'timeslot'
let _busViewTs     = 8;          // selected bus timeslot hour

// Geodata URLs (E01 experiment from known_data)
const GEODATA_E01 = {
  toA: {
    route: '/data/known_data/geodata/E01/to_A/ROUTE/E01route_toA.geojson',
    stops: '/data/known_data/geodata/E01/to_A/STOPS/E01stops_toA.geojson',
  },
  toB: {
    route: '/data/known_data/geodata/E01/to_B/ROUTE/E01route_toB.geojson',
    stops: '/data/known_data/geodata/E01/to_B/STOPS/E01stops_toB.geojson',
  },
};

// Direction labels (populated from known_data general_info)
let DIR_LABEL = { toA: 'Sentido A', toB: 'Sentido B' };

// Bus terminal stops
const STOP_TOA = '2646';  // departure stop for toA trips
const STOP_TOB = '5727';  // departure stop for toB trips

// Line → experiment mapping
const LINE_TO_EXPERIMENT = { '401': 'E01' };

// ---- Direction name helpers ----

function parseDirectionName(str) {
  // "Sentido Parada: 5727 Cibeles" → "Cibeles"
  const colonIdx = str.indexOf(': ');
  if (colonIdx === -1) return str;
  const tokens = str.slice(colonIdx + 2).split(' ');
  return tokens.slice(1).join(' ') || str; // skip stop id, keep rest
}

async function loadLineInfo(lineValue) {
  const expId = LINE_TO_EXPERIMENT[lineValue];
  if (!expId) return;
  try {
    const res = await fetch(`/data/known_data/general_info/${expId}.json`);
    if (!res.ok) return;
    const info = await res.json();
    if (info.toA?.[0]) DIR_LABEL.toA = parseDirectionName(info.toA[0]);
    if (info.toB?.[0]) DIR_LABEL.toB = parseDirectionName(info.toB[0]);
  } catch (_) {}
}

// ---- Data loading ----

async function loadInputs() {
  const res = await fetch(`/api/simulations/${simId}/inputs`);
  if (!res.ok) {
    const d = await res.json().catch(() => ({}));
    throw new Error(d.error || `HTTP ${res.status}`);
  }
  const data = await res.json();
  inputData.buses        = data.buses        || {};
  inputData.stopsToA     = data.stopsToA     || [];
  inputData.stopsToB     = data.stopsToB     || [];
  inputData.alightToA    = data.alightToA    || [];
  inputData.alightToB    = data.alightToB    || [];
  inputData.timesStopsToA = data.timesStopsToA || [];
  inputData.timesStopsToB = data.timesStopsToB || [];

  // Pre-fill meta fields
  if (data.description) {
    if (data.description.title)       document.getElementById('input-title').value       = data.description.title;
    if (data.description.description) document.getElementById('input-description').value = data.description.description;
    if (data.description.line)        document.getElementById('input-line').value         = data.description.line;
    if (data.description.model)       document.getElementById('input-model').value = data.description.model || 'without_agents';
    if (data.description.seed)        document.getElementById('input-seed').value = data.description.seed;
    document.getElementById('input-exclusive').value = data.description.exclusive ? 'yes' : 'no';
  }

  // Load direction names from general_info for the selected line
  const lineVal = data.description?.line || document.getElementById('input-line').value;
  await loadLineInfo(lineVal);
}

// ---- Save ----

async function saveInputs() {
  const description = {
    title:       document.getElementById('input-title').value.trim(),
    description: document.getElementById('input-description').value.trim(),
    line:        document.getElementById('input-line').value,
    model:       document.getElementById('input-model').value,
    seed:        document.getElementById('input-seed').value.trim(),
    exclusive:   document.getElementById('input-exclusive').value === 'yes',
  };

  if (description.seed && !/^\d{1,20}$/.test(description.seed)) {
    throw new Error('La semilla debe ser un número entero positivo (máx. 20 cifras)');
  }

  const body = {
    description,
    buses:        inputData.buses,
    stopsToA:     inputData.stopsToA,
    stopsToB:     inputData.stopsToB,
    alightToA:    inputData.alightToA,
    alightToB:    inputData.alightToB,
    timesStopsToA: inputData.timesStopsToA,
    timesStopsToB: inputData.timesStopsToB,
  };

  const res = await fetch(`/api/simulations/${simId}/inputs`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || `HTTP ${res.status}`);
  // Empty seed -> the server generates one; show it so the run can be reproduced
  if (data.seed) document.getElementById('input-seed').value = data.seed;
  return data;
}

async function handleSave() {
  try {
    await saveInputs();
    toast('Configuración guardada correctamente', 'success');
  } catch (err) {
    toast('Error al guardar: ' + err.message, 'error');
  }
}

async function handleRun() {
  try {
    await saveInputs();
    toast('Guardado. Lanzando simulación...', 'info');
    const res = await fetch(`/api/simulations/${simId}/run`, { method: 'POST' });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      toast(data.error || 'Error al lanzar la simulación', 'error');
      return;
    }
    toast(data.queued
      ? `Simulación en cola (posición ${data.position}): arrancará cuando haya hueco`
      : 'Simulación lanzada en segundo plano', 'success');
    setTimeout(() => { window.location.href = '/'; }, 2000);
  } catch (err) {
    toast('Error: ' + err.message, 'error');
  }
}

// ---- View switching ----

function switchView(view) {
  currentView = view;
  document.querySelectorAll('.config-nav-btn').forEach(b => {
    b.classList.toggle('active', b.dataset.view === view);
  });
  const content = document.getElementById('config-content');
  content.innerHTML = '';
  _currentInfoSel = null;
  _activeClearSel = null;
  if (view === 'buses') renderBusesView(content);
  else                  renderRouteView(content);
}

// ============================================================
// BUSES VIEW
// ============================================================

function renderBusesView(container) {
  const wrap = document.createElement('div');
  wrap.className = 'buses-editor';

  // Filter bar
  const filterBar = document.createElement('div');
  filterBar.className = 'buses-editor-filter-bar';
  filterBar.innerHTML = `
    <span class="analysis-filter-label">Ver por:</span>
    <button class="filter-btn ${_busViewFilter === 'physical' ? 'active' : ''}" id="bus-filter-physical">&#128652; Autobús físico</button>
    <button class="filter-btn ${_busViewFilter === 'timeslot' ? 'active' : ''}" id="bus-filter-ts">&#128336; Franja horaria</button>
    <div id="bus-ts-selector" style="display:${_busViewFilter === 'timeslot' ? 'flex' : 'none'};align-items:center;gap:0.35rem;flex-wrap:wrap;margin-left:0.75rem;"></div>
  `;
  wrap.appendChild(filterBar);

  // Content area
  const contentArea = document.createElement('div');
  contentArea.id = 'buses-view-content';
  wrap.appendChild(contentArea);

  container.appendChild(wrap);

  if (_busViewFilter === 'timeslot') {
    renderBusTsSelector(document.getElementById('bus-ts-selector'));
  }
  renderBusViewContent();

  document.getElementById('bus-filter-physical').addEventListener('click', () => {
    _busViewFilter = 'physical';
    document.getElementById('bus-filter-physical').classList.add('active');
    document.getElementById('bus-filter-ts').classList.remove('active');
    document.getElementById('bus-ts-selector').style.display = 'none';
    renderBusViewContent();
  });
  document.getElementById('bus-filter-ts').addEventListener('click', () => {
    _busViewFilter = 'timeslot';
    document.getElementById('bus-filter-ts').classList.add('active');
    document.getElementById('bus-filter-physical').classList.remove('active');
    const sel = document.getElementById('bus-ts-selector');
    sel.style.display = 'flex';
    renderBusTsSelector(sel);
    renderBusViewContent();
  });
}

function renderBusTsSelector(container) {
  container.innerHTML = '';
  const label = document.createElement('span');
  label.className = 'timeslot-selector-label';
  label.textContent = 'Hora:';
  container.appendChild(label);
  for (let h = 5; h <= 23; h++) {
    const btn = document.createElement('button');
    btn.className = 'ts-btn' + (h === _busViewTs ? ' active' : '');
    btn.dataset.hour = h;
    btn.textContent = h;
    btn.addEventListener('click', () => {
      _busViewTs = h;
      container.querySelectorAll('.ts-btn').forEach(b => b.classList.toggle('active', Number(b.dataset.hour) === h));
      renderBusViewContent();
    });
    container.appendChild(btn);
  }
}

function renderBusViewContent() {
  const content = document.getElementById('buses-view-content');
  if (!content) return;
  content.innerHTML = '';
  if (_busViewFilter === 'physical') {
    renderPhysicalBusView(content);
  } else {
    renderTimeslotBusView(content, _busViewTs);
  }
}

function renderPhysicalBusView(container) {
  // Header row
  const header = document.createElement('div');
  header.className = 'buses-editor-header';
  header.innerHTML = `
    <div>
      <h3>Autobuses Físicos</h3>
      <p class="buses-editor-subtitle">Cada autobús físico tiene una lista de salidas desde los terminales de la línea.</p>
    </div>
    <button class="btn btn-primary btn-sm" id="btn-add-bus">+ Nuevo autobús</button>
  `;
  container.appendChild(header);

  // Add-bus form (hidden by default)
  const addBusForm = document.createElement('div');
  addBusForm.className = 'add-bus-form';
  addBusForm.id = 'add-bus-form';
  addBusForm.style.display = 'none';
  addBusForm.innerHTML = `
    <div class="add-bus-form-inner">
      <label>ID del autobús (número):</label>
      <input type="text" id="new-bus-id" placeholder="ej. 3599" maxlength="6" />
      <button class="btn btn-primary btn-sm" id="btn-confirm-add-bus">Crear</button>
      <button class="btn btn-outline btn-sm" id="btn-cancel-add-bus">Cancelar</button>
    </div>
    <p class="add-bus-form-hint">El ID es el identificador del autobús físico (matrícula/número de unidad).</p>
  `;
  container.appendChild(addBusForm);

  // Bus list
  const list = document.createElement('div');
  list.className = 'bus-list';
  list.id = 'bus-list';
  container.appendChild(list);

  renderBusList();

  document.getElementById('btn-add-bus').addEventListener('click', () => {
    addBusForm.style.display = 'block';
    document.getElementById('new-bus-id').focus();
  });
  document.getElementById('btn-cancel-add-bus').addEventListener('click', () => {
    addBusForm.style.display = 'none';
    document.getElementById('new-bus-id').value = '';
  });
  document.getElementById('btn-confirm-add-bus').addEventListener('click', () => {
    const newId = document.getElementById('new-bus-id').value.trim();
    if (!newId) { toast('Introduce un ID de autobús', 'error'); return; }
    if (inputData.buses[newId]) { toast('Ya existe un autobús con ese ID', 'error'); return; }
    inputData.buses[newId] = [];
    addBusForm.style.display = 'none';
    document.getElementById('new-bus-id').value = '';
    renderBusList();
    toast(`Autobús ${newId} creado`, 'success');
  });
}

function renderTimeslotBusView(container, ts) {
  // Collect all departures in this hour
  const departures = [];
  for (const [busId, trips] of Object.entries(inputData.buses)) {
    trips.forEach(([stopId, time]) => {
      const hour = parseInt(time.split(':')[0], 10);
      if (hour === ts) departures.push({ busId, stopId, time });
    });
  }
  departures.sort((a, b) => a.time.localeCompare(b.time));

  const header = document.createElement('div');
  header.className = 'buses-editor-header';
  header.innerHTML = `
    <div>
      <h3>Franja ${ts}:00 – ${ts + 1}:00</h3>
      <p class="buses-editor-subtitle">${departures.length} salida${departures.length !== 1 ? 's' : ''} programada${departures.length !== 1 ? 's' : ''} en esta franja.</p>
    </div>
  `;
  container.appendChild(header);

  if (departures.length === 0) {
    const empty = document.createElement('div');
    empty.className = 'empty-state';
    empty.style.padding = '2rem';
    empty.innerHTML = `<p>No hay salidas programadas en la franja ${ts}:00 – ${ts + 1}:00.</p>`;
    container.appendChild(empty);
    return;
  }

  const tableWrap = document.createElement('div');
  tableWrap.style.padding = '0 0 1rem';
  const table = document.createElement('table');
  table.className = 'trips-table';
  table.innerHTML = `
    <thead>
      <tr>
        <th>Autobús</th>
        <th>Dirección</th>
        <th>Hora de salida</th>
        <th></th>
      </tr>
    </thead>
  `;
  const tbody = document.createElement('tbody');

  departures.forEach(dep => {
    const isToA = dep.stopId === STOP_TOA;
    const dir = isToA
      ? `<span class="dir-badge dir-badge-a">&#8594; ${DIR_LABEL.toA}</span>`
      : `<span class="dir-badge dir-badge-b">&#8592; ${DIR_LABEL.toB}</span>`;
    const tr = document.createElement('tr');
    tr.className = 'trip-row';
    tr.innerHTML = `
      <td class="trip-idx"><span class="bus-id-badge">${escHtml(dep.busId)}</span></td>
      <td>${dir}</td>
      <td style="font-family:monospace;">${escHtml(dep.time)}</td>
      <td><button class="btn btn-sm btn-danger-soft" title="Eliminar salida">&#10005;</button></td>
    `;
    tr.querySelector('button').addEventListener('click', () => {
      const trips = inputData.buses[dep.busId];
      if (!trips) return;
      const idx = trips.findIndex(([sid, t]) => sid === dep.stopId && t === dep.time);
      if (idx !== -1) {
        trips.splice(idx, 1);
        renderBusViewContent();
        toast('Salida eliminada', 'info');
      }
    });
    tbody.appendChild(tr);
  });

  table.appendChild(tbody);
  tableWrap.appendChild(table);
  container.appendChild(tableWrap);
}

function renderBusList() {
  const list = document.getElementById('bus-list');
  if (!list) return;
  list.innerHTML = '';

  const busIds = Object.keys(inputData.buses).sort((a, b) => Number(a) - Number(b));

  if (busIds.length === 0) {
    list.innerHTML = `<div class="empty-state" style="padding:2rem;"><p>No hay autobuses configurados. Añade uno con el botón de arriba.</p></div>`;
    return;
  }

  busIds.forEach(busId => {
    list.appendChild(buildBusCard(busId));
  });
}

function buildBusCard(busId) {
  const trips = inputData.buses[busId] || [];
  const card = document.createElement('div');
  card.className = 'bus-card';
  card.id = `bus-card-${busId}`;

  // Header
  const cardHeader = document.createElement('div');
  cardHeader.className = 'bus-card-header';
  cardHeader.innerHTML = `
    <div class="bus-card-title">
      <span class="bus-card-icon">&#128652;</span>
      <span class="bus-card-id">Autobús ${escHtml(busId)}</span>
      <span class="bus-card-count">${trips.length} salida${trips.length !== 1 ? 's' : ''}</span>
    </div>
    <div class="bus-card-actions">
      <button class="btn btn-sm btn-outline btn-collapse" data-bus="${escHtml(busId)}">
        <span class="collapse-icon">&#9660;</span> Ver salidas
      </button>
      <button class="btn btn-sm btn-danger" data-delete-bus="${escHtml(busId)}">&#128465; Eliminar</button>
    </div>
  `;
  card.appendChild(cardHeader);

  // Trips section (collapsible)
  const tripsSection = document.createElement('div');
  tripsSection.className = 'bus-trips-section';
  tripsSection.id = `bus-trips-${busId}`;
  tripsSection.style.display = 'none';

  tripsSection.appendChild(buildTripsTable(busId));
  card.appendChild(tripsSection);

  // Wire up collapse button
  cardHeader.querySelector('.btn-collapse').addEventListener('click', (e) => {
    const btn = e.currentTarget;
    const open = tripsSection.style.display !== 'none';
    tripsSection.style.display = open ? 'none' : 'block';
    btn.querySelector('.collapse-icon').textContent = open ? '▼' : '▲';
    btn.querySelector('.collapse-icon').nextSibling.textContent = open ? ' Ver salidas' : ' Ocultar';
  });

  // Wire up delete bus
  cardHeader.querySelector('[data-delete-bus]').addEventListener('click', () => {
    if (!confirm(`¿Eliminar el autobús ${busId} y todas sus salidas?`)) return;
    delete inputData.buses[busId];
    renderBusList();
    toast(`Autobús ${busId} eliminado`, 'info');
  });

  return card;
}

function buildTripsTable(busId) {
  const trips = inputData.buses[busId] || [];
  const wrap = document.createElement('div');

  if (trips.length === 0) {
    wrap.innerHTML = `<p class="bus-trips-empty">Sin salidas. Añade una con el botón de abajo.</p>`;
  } else {
    const table = document.createElement('table');
    table.className = 'trips-table';
    table.innerHTML = `
      <thead>
        <tr>
          <th>#</th>
          <th>Dirección</th>
          <th>Hora de salida</th>
          <th></th>
        </tr>
      </thead>
    `;
    const tbody = document.createElement('tbody');
    trips.forEach(([stopId, time], idx) => {
      const isToA = stopId === STOP_TOA;
      const dir = isToA ? `<span class="dir-badge dir-badge-a">&#8594; ${DIR_LABEL.toA}</span>` : `<span class="dir-badge dir-badge-b">&#8592; ${DIR_LABEL.toB}</span>`;
      const tr = document.createElement('tr');
      tr.className = 'trip-row';
      tr.innerHTML = `
        <td class="trip-idx">${idx + 1}</td>
        <td>${dir}</td>
        <td>
          <input type="text" class="trip-time-input" value="${escHtml(time)}" data-bus="${escHtml(busId)}" data-idx="${idx}" pattern="\\d{1,2}:\\d{2}" title="Formato HH:MM" />
        </td>
        <td>
          <button class="btn btn-sm btn-danger-soft" data-delete-trip="${idx}" title="Eliminar salida">&#10005;</button>
        </td>
      `;
      // Time change handler
      tr.querySelector('.trip-time-input').addEventListener('change', (e) => {
        inputData.buses[busId][idx][1] = e.target.value.trim();
      });
      // Delete trip handler
      tr.querySelector('[data-delete-trip]').addEventListener('click', () => {
        inputData.buses[busId].splice(idx, 1);
        refreshBusCard(busId);
        toast('Salida eliminada', 'info');
      });
      tbody.appendChild(tr);
    });
    table.appendChild(tbody);
    wrap.appendChild(table);
  }

  // Add trip form
  const addForm = document.createElement('div');
  addForm.className = 'add-trip-form';
  addForm.innerHTML = `
    <span class="add-trip-label">Nueva salida:</span>
    <select class="add-trip-dir">
      <option value="${STOP_TOA}">&#8594; ${DIR_LABEL.toA} (desde ${STOP_TOA})</option>
      <option value="${STOP_TOB}">&#8592; ${DIR_LABEL.toB} (desde ${STOP_TOB})</option>
    </select>
    <input type="text" class="add-trip-time" placeholder="HH:MM" />
    <button class="btn btn-sm btn-primary btn-add-trip">+ Añadir</button>
  `;
  addForm.querySelector('.btn-add-trip').addEventListener('click', () => {
    const stopId = addForm.querySelector('.add-trip-dir').value;
    const time   = addForm.querySelector('.add-trip-time').value.trim();
    if (!time.match(/^\d{1,2}:\d{2}$/)) { toast('Hora inválida (usa formato H:MM o HH:MM)', 'error'); return; }
    if (!inputData.buses[busId]) inputData.buses[busId] = [];
    inputData.buses[busId].push([stopId, time]);
    refreshBusCard(busId);
    toast('Salida añadida', 'success');
  });
  wrap.appendChild(addForm);

  return wrap;
}

function refreshBusCard(busId) {
  const section = document.getElementById(`bus-trips-${busId}`);
  const card    = document.getElementById(`bus-card-${busId}`);
  if (!section || !card) { renderBusList(); return; }

  // Update count in header
  const trips = inputData.buses[busId] || [];
  const countEl = card.querySelector('.bus-card-count');
  if (countEl) countEl.textContent = `${trips.length} salida${trips.length !== 1 ? 's' : ''}`;

  // Rebuild trips table keeping section visible
  const wasVisible = section.style.display !== 'none';
  section.innerHTML = '';
  section.appendChild(buildTripsTable(busId));
  section.style.display = wasVisible ? 'block' : 'none';
}

// ============================================================
// ROUTE VIEW
// ============================================================

function renderRouteView(container) {
  const wrap = document.createElement('div');
  wrap.className = 'route-config-wrap';

  // Filter bar
  const filterBar = document.createElement('div');
  filterBar.className = 'route-config-filter-bar';
  filterBar.id = 'route-config-filter-bar';
  filterBar.innerHTML = `
    <span class="analysis-filter-label">Mostrar por:</span>
    <button class="filter-btn ${_routeFilter === 'general' ? 'active' : ''}" id="rcfg-general-btn">&#128202; General</button>
    <button class="filter-btn ${_routeFilter === 'timeslot' ? 'active' : ''}" id="rcfg-ts-btn">&#128336; Franja horaria</button>
    <div class="rcfg-ts-selector" id="rcfg-ts-selector" style="display:${_routeFilter === 'timeslot' ? 'flex' : 'none'};"></div>
  `;
  wrap.appendChild(filterBar);

  // Direction maps
  const mapsRow = document.createElement('div');
  mapsRow.className = 'route-config-maps';
  mapsRow.innerHTML = `
    <div class="direction-map-panel">
      <div class="direction-map-label dir-label-a">&#8594; ${DIR_LABEL.toA}</div>
      <svg id="rcfg-svg-toA" class="route-svg"></svg>
    </div>
    <div class="direction-map-panel">
      <div class="direction-map-label dir-label-b">&#8592; ${DIR_LABEL.toB}</div>
      <svg id="rcfg-svg-toB" class="route-svg"></svg>
    </div>
  `;
  wrap.appendChild(mapsRow);

  // Info panel
  const infoPanel = document.createElement('div');
  infoPanel.className = 'route-config-info-panel';
  infoPanel.id = 'rcfg-info-panel';
  infoPanel.style.display = 'none';
  wrap.appendChild(infoPanel);

  container.appendChild(wrap);

  // Filter bar events
  document.getElementById('rcfg-general-btn').addEventListener('click', () => {
    _routeFilter = 'general';
    document.getElementById('rcfg-general-btn').classList.add('active');
    document.getElementById('rcfg-ts-btn').classList.remove('active');
    document.getElementById('rcfg-ts-selector').style.display = 'none';
    refreshConfigInfoPanel();
  });
  document.getElementById('rcfg-ts-btn').addEventListener('click', () => {
    _routeFilter = 'timeslot';
    document.getElementById('rcfg-ts-btn').classList.add('active');
    document.getElementById('rcfg-general-btn').classList.remove('active');
    const sel = document.getElementById('rcfg-ts-selector');
    sel.style.display = 'flex';
    renderTsSelector(sel);
    refreshConfigInfoPanel();
  });

  // Build both SVG maps
  buildSvgMapConfig(document.getElementById('rcfg-svg-toA'), GEODATA_E01.toA, 'toA');
  buildSvgMapConfig(document.getElementById('rcfg-svg-toB'), GEODATA_E01.toB, 'toB');
}

function renderTsSelector(container) {
  container.innerHTML = '';
  const label = document.createElement('span');
  label.className = 'timeslot-selector-label';
  label.textContent = 'Hora:';
  container.appendChild(label);
  for (let h = 5; h <= 23; h++) {
    const btn = document.createElement('button');
    btn.className = 'ts-btn' + (h === _selectedTs ? ' active' : '');
    btn.dataset.hour = h;
    btn.textContent = h;
    btn.addEventListener('click', () => {
      _selectedTs = h;
      container.querySelectorAll('.ts-btn').forEach(b => b.classList.toggle('active', Number(b.dataset.hour) === h));
      refreshConfigInfoPanel();
    });
    container.appendChild(btn);
  }
}

function refreshConfigInfoPanel() {
  if (!_currentInfoSel) return;
  if (_currentInfoSel.type === 'stop') {
    showConfigStopInfo(_currentInfoSel.stopId, _currentInfoSel.stopProps, _currentInfoSel.dirKey);
  } else {
    showConfigSectionInfo(_currentInfoSel.sectionKey, _currentInfoSel.dirKey);
  }
}

function closeConfigInfoPanel() {
  if (_activeClearSel) { _activeClearSel(); _activeClearSel = null; }
  _currentInfoSel = null;
  const panel = document.getElementById('rcfg-info-panel');
  if (panel) panel.style.display = 'none';
}

// ---- SVG map for config ----

const _configTooltip = (() => {
  const el = document.createElement('div');
  el.className = 'route-tooltip';
  document.body.appendChild(el);
  return el;
})();

function showCfgTooltip(e, html) {
  _configTooltip.innerHTML = html;
  _configTooltip.style.display = 'block';
  _configTooltip.style.left = (e.clientX + 14) + 'px';
  _configTooltip.style.top  = (e.clientY - 10) + 'px';
}
function moveCfgTooltip(e) {
  _configTooltip.style.left = (e.clientX + 14) + 'px';
  _configTooltip.style.top  = (e.clientY - 10) + 'px';
}
function hideCfgTooltip() {
  _configTooltip.style.display = 'none';
}

async function buildSvgMapConfig(svgEl, dirData, dirKey) {
  const ns = 'http://www.w3.org/2000/svg';

  const loading = document.createElementNS(ns, 'text');
  loading.setAttribute('x', '50%'); loading.setAttribute('y', '50%');
  loading.setAttribute('text-anchor', 'middle'); loading.setAttribute('dominant-baseline', 'middle');
  loading.setAttribute('fill', '#aaa'); loading.setAttribute('font-size', '13');
  loading.setAttribute('font-family', 'sans-serif');
  loading.textContent = 'Cargando...';
  svgEl.appendChild(loading);

  try {
    const [routeGeo, stopsGeo] = await Promise.all([
      fetch(dirData.route).then(r => r.json()),
      fetch(dirData.stops).then(r => r.json()),
    ]);

    svgEl.innerHTML = '';

    const sortedStops = stopsGeo.features
      .filter(f => f.geometry.type === 'Point')
      .map(f => ({ props: f.properties, coords: f.geometry.coordinates }))
      .sort((a, b) => a.props.distance - b.props.distance);

    const sections = sortedStops.slice(0, -1).map((from, i) => ({
      from, to: sortedStops[i + 1],
      visPaths: [], hitPaths: [],
      fromCircle: null, toCircle: null,
    }));

    function assignSection(dist) {
      for (let i = 0; i < sections.length; i++) {
        if (dist < sections[i].to.props.distance) return i;
      }
      return sections.length - 1;
    }

    const allCoords = [];
    for (const f of routeGeo.features) {
      const rings = f.geometry.type === 'MultiLineString' ? f.geometry.coordinates : [f.geometry.coordinates];
      for (const ring of rings) allCoords.push(...ring);
    }
    for (const s of sortedStops) allCoords.push(s.coords);

    if (allCoords.length === 0) {
      svgEl.innerHTML = `<text x="50%" y="50%" text-anchor="middle" fill="#aaa" font-size="13" font-family="sans-serif">Sin datos</text>`;
      return;
    }

    const minLng = Math.min(...allCoords.map(c => c[0]));
    const maxLng = Math.max(...allCoords.map(c => c[0]));
    const minLat = Math.min(...allCoords.map(c => c[1]));
    const maxLat = Math.max(...allCoords.map(c => c[1]));

    const rect = svgEl.getBoundingClientRect();
    const W = rect.width || 500; const H = rect.height || 380; const PAD = 32;
    const rangeX = maxLng - minLng || 0.001; const rangeY = maxLat - minLat || 0.001;
    const scaleX = (W - 2 * PAD) / rangeX; const scaleY = (H - 2 * PAD) / rangeY;
    const scale  = Math.min(scaleX, scaleY);
    const drawW  = rangeX * scale; const drawH = rangeY * scale;
    const offX   = PAD + (W - 2 * PAD - drawW) / 2;
    const offY   = PAD + (H - 2 * PAD - drawH) / 2;

    const project = ([lng, lat]) => [
      offX + (lng - minLng) * scale,
      offY + drawH - (lat - minLat) * scale,
    ];

    const C_DEFAULT  = '#0865d6';
    const C_HOVER    = '#0c97e8';
    const C_SELECTED = '#f59e0b';
    const C_STOP_DEF = '#ffffff';
    const C_STOP_SEL = '#f59e0b';

    let selectedIdx     = -1;
    let selectedStopIdx = -1;
    const stopCircles   = [];

    function styleSection(idx, color, weight) {
      sections[idx].visPaths.forEach(p => { p.setAttribute('stroke', color); p.setAttribute('stroke-width', weight); });
    }
    function styleStops(idx, fill, stroke) {
      [sections[idx].fromCircle, sections[idx].toCircle].forEach(c => {
        if (c) { c.setAttribute('fill', fill); c.setAttribute('stroke', stroke); c.setAttribute('r', fill === C_STOP_DEF ? '6' : '8'); }
      });
    }
    function styleStopCircle(i, fill, stroke, r) {
      const c = stopCircles[i];
      if (c) { c.setAttribute('fill', fill); c.setAttribute('stroke', stroke); c.setAttribute('r', r); }
    }
    function clearSel() {
      if (selectedIdx >= 0)     { styleSection(selectedIdx, C_DEFAULT, '3'); styleStops(selectedIdx, C_STOP_DEF, C_DEFAULT); selectedIdx = -1; }
      if (selectedStopIdx >= 0) { styleStopCircle(selectedStopIdx, C_STOP_DEF, C_DEFAULT, '6'); selectedStopIdx = -1; }
    }

    // Draw route segments
    for (const f of routeGeo.features) {
      const sIdx = assignSection(f.properties.distance);
      const rings = f.geometry.type === 'MultiLineString' ? f.geometry.coordinates : [f.geometry.coordinates];
      for (const ring of rings) {
        const pts = ring.map(project);
        const d   = 'M ' + pts.map(([x, y]) => `${x.toFixed(1)},${y.toFixed(1)}`).join(' L ');
        const vis = document.createElementNS(ns, 'path');
        vis.setAttribute('d', d); vis.setAttribute('stroke', C_DEFAULT); vis.setAttribute('stroke-width', '3');
        vis.setAttribute('fill', 'none'); vis.setAttribute('stroke-linecap', 'round'); vis.setAttribute('stroke-linejoin', 'round');
        const hit = document.createElementNS(ns, 'path');
        hit.setAttribute('d', d); hit.setAttribute('stroke', 'transparent'); hit.setAttribute('stroke-width', '14');
        hit.setAttribute('fill', 'none'); hit.style.cursor = 'pointer';
        sections[sIdx].visPaths.push(vis); sections[sIdx].hitPaths.push(hit);
        svgEl.appendChild(vis); svgEl.appendChild(hit);
      }
    }

    // Section hover/click
    sections.forEach((sec, sIdx) => {
      const ttHtml = () =>
        `<strong>${sec.from.props.stopNum}</strong> ${escHtml(sec.from.props.stopName)}`
        + ` &#8594; <strong>${sec.to.props.stopNum}</strong> ${escHtml(sec.to.props.stopName)}`;
      sec.hitPaths.forEach(hit => {
        hit.addEventListener('mouseenter', e => { if (selectedIdx !== sIdx) styleSection(sIdx, C_HOVER, '5'); showCfgTooltip(e, ttHtml()); });
        hit.addEventListener('mousemove',  moveCfgTooltip);
        hit.addEventListener('mouseleave', () => { if (selectedIdx !== sIdx) styleSection(sIdx, C_DEFAULT, '3'); hideCfgTooltip(); });
        hit.addEventListener('click', () => {
          const wasSel = selectedIdx === sIdx;
          if (_activeClearSel && _activeClearSel !== clearSel) { _activeClearSel(); _activeClearSel = null; }
          clearSel();
          if (!wasSel) {
            styleSection(sIdx, C_SELECTED, '5');
            styleStops(sIdx, C_STOP_SEL, C_SELECTED);
            selectedIdx = sIdx;
            _activeClearSel = clearSel;
            const sectionKey = `${sec.from.props.stopNum}-${sec.to.props.stopNum}`;
            _currentInfoSel = { type: 'section', sectionKey, dirKey };
            showConfigSectionInfo(sectionKey, dirKey);
          } else {
            _activeClearSel = null;
            _currentInfoSel = null;
            const panel = document.getElementById('rcfg-info-panel');
            if (panel) panel.style.display = 'none';
          }
          hideCfgTooltip();
        });
      });
    });

    // Draw stops
    sortedStops.forEach((stop, i) => {
      const [x, y] = project(stop.coords);
      const p = stop.props;
      const circle = document.createElementNS(ns, 'circle');
      circle.setAttribute('cx', x.toFixed(1)); circle.setAttribute('cy', y.toFixed(1));
      circle.setAttribute('r', '6'); circle.setAttribute('fill', C_STOP_DEF);
      circle.setAttribute('stroke', C_DEFAULT); circle.setAttribute('stroke-width', '2.5');
      circle.style.cursor = 'pointer';
      stopCircles.push(circle);
      if (i < sections.length) sections[i].fromCircle = circle;
      if (i > 0)               sections[i - 1].toCircle = circle;

      circle.addEventListener('mouseenter', e => { circle.setAttribute('r', '9'); circle.setAttribute('fill', C_DEFAULT); showCfgTooltip(e, `<strong>${p.stopNum}</strong> &middot; ${escHtml(p.stopName)}`); });
      circle.addEventListener('mousemove',  moveCfgTooltip);
      circle.addEventListener('mouseleave', () => {
        const isBoundary = (i < sections.length && selectedIdx === i) || (i > 0 && selectedIdx === i - 1);
        const isSel = selectedStopIdx === i;
        circle.setAttribute('r',      (isBoundary || isSel) ? '8' : '6');
        circle.setAttribute('fill',   (isBoundary || isSel) ? C_STOP_SEL : C_STOP_DEF);
        circle.setAttribute('stroke', (isBoundary || isSel) ? C_SELECTED : C_DEFAULT);
        hideCfgTooltip();
      });
      circle.addEventListener('click', () => {
        const wasSel = selectedStopIdx === i;
        if (_activeClearSel && _activeClearSel !== clearSel) { _activeClearSel(); _activeClearSel = null; }
        clearSel();
        if (!wasSel) {
          styleStopCircle(i, C_STOP_SEL, C_SELECTED, '8');
          selectedStopIdx = i;
          _activeClearSel = clearSel;
          _currentInfoSel = { type: 'stop', stopId: String(p.stopNum), stopProps: p, dirKey };
          showConfigStopInfo(String(p.stopNum), p, dirKey);
        } else {
          _activeClearSel = null;
          _currentInfoSel = null;
          const panel = document.getElementById('rcfg-info-panel');
          if (panel) panel.style.display = 'none';
        }
        hideCfgTooltip();
      });
      svgEl.appendChild(circle);
    });

  } catch (err) {
    svgEl.innerHTML = '';
    const errText = document.createElementNS(ns, 'text');
    errText.setAttribute('x', '50%'); errText.setAttribute('y', '50%');
    errText.setAttribute('text-anchor', 'middle'); errText.setAttribute('fill', '#e3000f');
    errText.setAttribute('font-size', '13'); errText.setAttribute('font-family', 'sans-serif');
    errText.textContent = `Error: ${err.message}`;
    svgEl.appendChild(errText);
  }
}

// ---- Distribution helpers ----
//
// The user only sees means; the family of each row is kept and its parameters
// are rescaled here. Family names must be written back verbatim (the C parser
// identifies them by string length).
//
// Boardings (input_data_E01_*.csv), passengers arriving at the stop per hour:
//   NORMAL             Param1 = μ, Param2 = σ   mean = μ
//   NEGATIVE BINOMIAL  Param1 = r, Param2 = p   mean = r(1-p)/p
//   GEOMETRICAL        Param1 = p               mean = (1-p)/p
// Alightings (alighting_params_*.csv), fraction of the bus occupancy getting off:
//   binomial           P                        mean = P
//   betabinom          alpha, beta              mean = α/(α+β)
//   TERMINAL*          first/last stop, not sampled

function boardingMean(row) {
  const n1 = parseFloat(row.Param1), n2 = parseFloat(row.Param2);
  switch (String(row.DistributionType).trim()) {
    case 'NORMAL':
      return isNaN(n1) ? 0 : Math.max(n1, 0);
    case 'NEGATIVE BINOMIAL':
      return (isNaN(n1) || isNaN(n2) || n2 <= 0) ? 0 : n1 * (1 - n2) / n2;
    case 'GEOMETRICAL':
      return (isNaN(n1) || n1 <= 0) ? 0 : (1 - n1) / n1;
  }
  return 0;
}

// Success probability p' that multiplies the mean (1-p)/p by k: p' = 1 / (1 + k(1-p)/p)
function scaledSuccessProb(p, k) {
  return 1 / (1 + k * (1 - p) / p);
}

// Multiply the mean number of boardings of a row by k
function scaleBoarding(row, k) {
  switch (String(row.DistributionType).trim()) {
    case 'NORMAL':
      row.Param1 = String(parseFloat(row.Param1) * k);
      break;
    case 'NEGATIVE BINOMIAL': {
      const p = parseFloat(row.Param2);
      if (p > 0 && p < 1) row.Param2 = String(scaledSuccessProb(p, k));
      break;
    }
    case 'GEOMETRICAL': {
      const p = parseFloat(row.Param1);
      if (p > 0 && p < 1) row.Param1 = String(scaledSuccessProb(p, k));
      break;
    }
  }
}

const MAX_ALIGHT_FRACTION = 0.999;
const MIN_BETABIN_FRACTION = 1e-6; // α must stay > 0 for the beta sampler

function isTerminalAlight(row) {
  return String(row.family).trim().startsWith('TERMINAL');
}

function alightFraction(row) {
  switch (String(row.family).trim()) {
    case 'binomial': {
      const p = parseFloat(row.P);
      return isNaN(p) ? 0 : p;
    }
    case 'betabinom': {
      const a = parseFloat(row.alpha), b = parseFloat(row.beta);
      return (a + b > 0) ? a / (a + b) : 0;
    }
  }
  return 0;
}

// Set the mean alighting fraction of a row. Beta-binomial keeps α+β, so the
// over-dispersion of the fitted distribution is preserved.
function setAlightFraction(row, fraction) {
  const f = Math.min(Math.max(fraction, 0), MAX_ALIGHT_FRACTION);
  switch (String(row.family).trim()) {
    case 'binomial':
      row.P = String(f);
      break;
    case 'betabinom': {
      const c = parseFloat(row.alpha) + parseFloat(row.beta);
      if (!(c > 0)) return;
      const m = Math.max(f, MIN_BETABIN_FRACTION);
      row.alpha = String(m * c);
      row.beta  = String((1 - m) * c);
      break;
    }
  }
}

function avg(values) {
  return values.length ? values.reduce((s, v) => s + v, 0) / values.length : 0;
}

// Convert seconds (float) → "MM:SS" string
function secondsToMMSS(secs) {
  const total = Math.round(Math.max(0, secs));
  const m = Math.floor(total / 60);
  const s = total % 60;
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
}

// Parse "MM:SS" (or plain seconds) → seconds (number). Returns NaN on bad input.
function mmssToSeconds(str) {
  if (!str) return NaN;
  const t = str.trim();
  if (t.includes(':')) {
    const [mStr, sStr] = t.split(':');
    const m = parseInt(mStr, 10), s = parseInt(sStr, 10);
    if (isNaN(m) || isNaN(s) || s >= 60) return NaN;
    return m * 60 + s;
  }
  const n = parseFloat(t);
  return isNaN(n) ? NaN : n;
}

// ---- Stop info panel ----

function rowTimeslot(row) {
  return Number(row.Timeslot ?? row.TimeSlot);
}

function getBoardRows(stopId, dirKey) {
  const rows = dirKey === 'toA' ? inputData.stopsToA : inputData.stopsToB;
  return rows.filter(r => String(r.Stop) === String(stopId));
}

function getAlightRows(stopId, dirKey) {
  const rows = dirKey === 'toA' ? inputData.alightToA : inputData.alightToB;
  return rows.filter(r => String(r.Stop) === String(stopId));
}

// Value of an editable input only if the user changed it (avoids drift from
// re-applying the rounded value that was displayed)
function changedNumber(panel, id) {
  const el = panel.querySelector(`#${id}`);
  if (!el || el.disabled || el.value.trim() === el.defaultValue.trim()) return null;
  return parseFloat(el.value.replace(',', '.'));
}

// Scale boardings so their average mean goes from `orig` to `target`
function applyBoardingTarget(rows, target, orig) {
  if (!(orig > 0)) return false;
  const k = Math.max(target / orig, 1e-6);
  rows.forEach(r => scaleBoarding(r, k));
  return true;
}

// Move the average alighting fraction of `rows` from `orig` to `target`,
// keeping the relative profile across timeslots
function applyAlightingTarget(rows, target, orig) {
  const active = rows.filter(r => !isTerminalAlight(r));
  if (orig > 0) active.forEach(r => setAlightFraction(r, alightFraction(r) * target / orig));
  else          active.forEach(r => setAlightFraction(r, target));
  return active.length > 0;
}

function showConfigStopInfo(stopId, stopProps, dirKey) {
  const panel = document.getElementById('rcfg-info-panel');
  if (!panel) return;
  panel.style.display = 'block';

  const boardRows  = getBoardRows(stopId, dirKey);
  const alightRows = getAlightRows(stopId, dirKey);
  const dirLabel = dirKey === 'toA' ? `&#8594; ${DIR_LABEL.toA}` : `&#8592; ${DIR_LABEL.toB}`;
  const dirClass = dirKey === 'toA' ? 'dir-label-a' : 'dir-label-b';

  let content = `
    <div class="rcfg-panel-header">
      <div class="rcfg-panel-title">
        <span class="section-stop-badge ${dirClass}">${dirLabel}</span>
        <strong>Parada ${escHtml(stopId)}</strong>
        ${stopProps?.stopName ? `<span class="rcfg-stop-name">${escHtml(stopProps.stopName)}</span>` : ''}
      </div>
      <button class="btn btn-sm btn-outline" id="rcfg-panel-close">&#10005;</button>
    </div>
  `;

  if (boardRows.length === 0 && alightRows.length === 0) {
    content += `<p class="rcfg-no-data">No hay datos de pasajeros para esta parada en la dirección seleccionada.</p>`;
  } else if (_routeFilter === 'general') {
    content += buildStopGeneralView(boardRows, alightRows);
  } else {
    content += buildStopTimeslotView(boardRows, alightRows, _selectedTs);
  }

  panel.innerHTML = content;
  panel.querySelector('#rcfg-panel-close')?.addEventListener('click', closeConfigInfoPanel);

  const general = _routeFilter === 'general';
  const scopeBoard  = general ? boardRows  : boardRows.filter(r => rowTimeslot(r) === _selectedTs);
  const scopeAlight = general ? alightRows : alightRows.filter(r => rowTimeslot(r) === _selectedTs);

  panel.querySelector('#rcfg-apply-stop')?.addEventListener('click', () => {
    const newBoard = changedNumber(panel, 'rcfg-board-mean-input');
    const newPct   = changedNumber(panel, 'rcfg-alight-pct-input');

    if (newBoard !== null && (isNaN(newBoard) || newBoard < 0)) {
      toast('Media de subidas inválida: introduce un número ≥ 0', 'error'); return;
    }
    if (newPct !== null && (isNaN(newPct) || newPct < 0 || newPct > MAX_ALIGHT_FRACTION * 100)) {
      toast(`Porcentaje de bajadas inválido: introduce un valor entre 0 y ${MAX_ALIGHT_FRACTION * 100}`, 'error'); return;
    }
    if (newBoard === null && newPct === null) {
      toast('No hay cambios que aplicar', 'info'); return;
    }

    if (newBoard !== null) {
      const orig = avg(scopeBoard.map(boardingMean));
      if (!applyBoardingTarget(scopeBoard, newBoard, orig)) {
        toast('La media de subidas actual es 0: no se puede escalar', 'error');
      }
    }
    if (newPct !== null) {
      const orig = avg(scopeAlight.filter(r => !isTerminalAlight(r)).map(alightFraction));
      applyAlightingTarget(scopeAlight, newPct / 100, orig);
    }

    toast(general
      ? `Parada ${stopId}: valores actualizados en todas las franjas`
      : `Parada ${stopId} franja ${_selectedTs}h: valores actualizados`, 'success');
    showConfigStopInfo(stopId, stopProps, dirKey);
  });
}

function stopStatInput(id, label, value, disabledMsg) {
  return `
    <div class="rcfg-stat rcfg-stat-editable">
      <span class="rcfg-stat-label">${label}</span>
      <input type="text" inputmode="decimal" class="rcfg-mean-input" id="${id}"
             value="${value}" ${disabledMsg ? 'disabled' : ''} />
      ${disabledMsg ? `<span class="rcfg-modify-hint">${disabledMsg}</span>` : ''}
    </div>
  `;
}

// Alighting % input: disabled for terminal stops or when there is no data
function alightStat(rows, label) {
  const active = rows.filter(r => !isTerminalAlight(r));
  let msg = null;
  if (rows.length === 0)        msg = 'Sin datos de bajadas';
  else if (active.length === 0) msg = 'Parada de cabecera/final: no se modelan bajadas parciales';
  const pct = avg(active.map(alightFraction)) * 100;
  return stopStatInput('rcfg-alight-pct-input', label, msg ? '—' : pct.toFixed(2), msg);
}

function boardStat(rows, label) {
  const mean = avg(rows.map(boardingMean));
  return stopStatInput('rcfg-board-mean-input', label,
    rows.length ? mean.toFixed(2) : '—', rows.length ? null : 'Sin datos de subidas');
}

// ---- General view: mean passenger inputs ----

function buildStopGeneralView(boardRows, alightRows) {
  const timeslots = [...new Set([...boardRows, ...alightRows].map(rowTimeslot))].sort((a, b) => a - b);

  return `
    <div class="rcfg-panel-section">
      <h4>Pasajeros en esta parada</h4>
      <p class="rcfg-modify-hint" style="margin-bottom:0.75rem;">
        Valores medios de todas las franjas. Cambia un valor y pulsa <strong>Aplicar</strong>
        para escalar <em>todas las franjas horarias</em> proporcionalmente.
      </p>
      <div class="rcfg-stats-grid">
        ${boardStat(boardRows, '&#8679; Media de pasajeros que llegan a la parada por hora')}
        ${alightStat(alightRows, '&#8681; % medio de la ocupación del autobús que se baja en la parada')}
        <div class="rcfg-stat">
          <span class="rcfg-stat-label">Franjas con datos</span>
          <span class="rcfg-stat-value">${timeslots.length}</span>
          <span class="rcfg-stat-dist">${timeslots[0] ?? '—'}h – ${timeslots[timeslots.length - 1] ?? '—'}h</span>
        </div>
      </div>
      <div class="rcfg-apply-row">
        <button class="btn btn-primary btn-sm" id="rcfg-apply-stop">Aplicar a todas las franjas</button>
      </div>
    </div>
  `;
}

// ---- Timeslot view: mean passenger inputs for selected hour ----

function buildStopTimeslotView(boardRows, alightRows, ts) {
  const tsBoard  = boardRows.filter(r => rowTimeslot(r) === ts);
  const tsAlight = alightRows.filter(r => rowTimeslot(r) === ts);

  return `
    <div class="rcfg-panel-section">
      <h4>Franja horaria: ${ts}:00 – ${ts + 1}:00</h4>
      <p class="rcfg-modify-hint" style="margin-bottom:0.75rem;">
        Cambia un valor y pulsa <strong>Aplicar</strong> para modificar <em>solo esta franja</em>.
      </p>
      <div class="rcfg-stats-grid">
        ${boardStat(tsBoard, '&#8679; Número de pasajeros que llegan a la parada en esta franja')}
        ${alightStat(tsAlight, '&#8681; % de la ocupación del autobús que se baja en la parada')}
      </div>
      <div class="rcfg-apply-row">
        <button class="btn btn-primary btn-sm" id="rcfg-apply-stop">Aplicar a esta franja</button>
      </div>
    </div>
  `;
}

// ---- Section (travel time) info panel ----

function getSectionRow(sectionKey, dirKey) {
  const rows = dirKey === 'toA' ? inputData.timesStopsToA : inputData.timesStopsToB;
  return rows.find(r => r.StopsCodes === sectionKey) || null;
}

function showConfigSectionInfo(sectionKey, dirKey) {
  const panel = document.getElementById('rcfg-info-panel');
  if (!panel) return;
  panel.style.display = 'block';

  const row = getSectionRow(sectionKey, dirKey);
  const dirLabel = dirKey === 'toA' ? `&#8594; ${DIR_LABEL.toA}` : `&#8592; ${DIR_LABEL.toB}`;
  const dirClass = dirKey === 'toA' ? 'dir-label-a' : 'dir-label-b';
  const [fromStop, toStop] = sectionKey.split('-');

  let content = `
    <div class="rcfg-panel-header">
      <div class="rcfg-panel-title">
        <span class="section-stop-badge ${dirClass}">${dirLabel}</span>
        <strong>Tramo ${escHtml(fromStop)} &#8594; ${escHtml(toStop)}</strong>
      </div>
      <button class="btn btn-sm btn-outline" id="rcfg-panel-close">&#10005;</button>
    </div>
  `;

  if (!row) {
    content += `<p class="rcfg-no-data">No hay datos de tiempos para este tramo en la dirección seleccionada.</p>`;
  } else if (_routeFilter === 'general') {
    content += buildSectionGeneralView(row);
  } else {
    content += buildSectionTimeslotView(row, _selectedTs);
  }

  panel.innerHTML = content;
  panel.querySelector('#rcfg-panel-close')?.addEventListener('click', closeConfigInfoPanel);

  if (_routeFilter === 'general') {
    panel.querySelector('#rcfg-sec-apply-general')?.addEventListener('click', () => {
      const origSecs = parseFloat(panel.querySelector('#rcfg-sec-mean-original').value);
      const newSecs  = mmssToSeconds(panel.querySelector('#rcfg-sec-mean-input').value);
      if (isNaN(newSecs) || newSecs < 0) { toast('Formato inválido — usa MM:SS (ej: 02:35)', 'error'); return; }
      if (origSecs > 0) {
        const pct = (newSecs / origSecs - 1) * 100;
        applySectionChange(sectionKey, dirKey, pct, null);
      }
      toast(`Tramo ${sectionKey}: tiempos actualizados en todas las franjas`, 'success');
      showConfigSectionInfo(sectionKey, dirKey);
    });
  } else {
    panel.querySelector('#rcfg-sec-apply-ts')?.addEventListener('click', () => {
      const origSecs = parseFloat(panel.querySelector('#rcfg-sec-ts-original').value);
      const newSecs  = mmssToSeconds(panel.querySelector('#rcfg-sec-ts-input').value);
      if (isNaN(newSecs) || newSecs < 0) { toast('Formato inválido — usa MM:SS (ej: 02:35)', 'error'); return; }
      if (origSecs > 0) {
        const pct = (newSecs / origSecs - 1) * 100;
        applySectionChange(sectionKey, dirKey, pct, _selectedTs);
      }
      toast(`Tramo ${sectionKey} franja ${_selectedTs}h: tiempo actualizado`, 'success');
      showConfigSectionInfo(sectionKey, dirKey);
    });
  }
}

function buildSectionGeneralView(row) {
  let sum = 0; let count = 0;
  for (let h = 5; h <= 23; h++) {
    const v = parseFloat(row[`Mean_${h}`]);
    if (!isNaN(v)) { sum += v; count++; }
  }
  const avgMeanSecs = count ? sum / count : 0;

  return `
    <div class="rcfg-panel-section">
      <h4>Tiempo de tránsito (general)</h4>
      <p class="rcfg-modify-hint" style="margin-bottom:0.75rem;">
        Tiempo medio de tránsito en este tramo. Cambia el valor y pulsa <strong>Aplicar</strong>
        para escalar <em>todas las franjas horarias</em> proporcionalmente.
      </p>
      <div class="rcfg-stats-grid">
        <div class="rcfg-stat rcfg-stat-editable">
          <span class="rcfg-stat-label">&#128337; Tiempo medio (todas las franjas)</span>
          <input type="text" class="rcfg-mean-input" id="rcfg-sec-mean-input"
                 value="${secondsToMMSS(avgMeanSecs)}" placeholder="MM:SS" />
          <span class="rcfg-modify-hint">formato MM:SS</span>
        </div>
        <div class="rcfg-stat">
          <span class="rcfg-stat-label">Tramo</span>
          <span class="rcfg-stat-value" style="font-size:0.85rem;">${escHtml(row.StopsCodes)}</span>
        </div>
      </div>
      <div class="rcfg-apply-row">
        <button class="btn btn-primary btn-sm" id="rcfg-sec-apply-general">Aplicar a todas las franjas</button>
      </div>
    </div>
    <input type="hidden" id="rcfg-sec-mean-original" value="${avgMeanSecs}" />
  `;
}

function buildSectionTimeslotView(row, ts) {
  const meanSecs = row[`Mean_${ts}`] ? parseFloat(row[`Mean_${ts}`]) : 0;
  const hasData  = !!row[`Mean_${ts}`];

  return `
    <div class="rcfg-panel-section">
      <h4>Franja horaria: ${ts}:00 – ${ts + 1}:00</h4>
      <p class="rcfg-modify-hint" style="margin-bottom:0.75rem;">
        Cambia el valor y pulsa <strong>Aplicar</strong> para modificar <em>solo esta franja</em>.
      </p>
      <div class="rcfg-stats-grid">
        <div class="rcfg-stat rcfg-stat-editable">
          <span class="rcfg-stat-label">&#128337; Tiempo medio en esta franja</span>
          <input type="text" class="rcfg-mean-input" id="rcfg-sec-ts-input"
                 value="${secondsToMMSS(meanSecs)}" placeholder="MM:SS"
                 ${!hasData ? 'disabled' : ''} />
          <span class="rcfg-modify-hint">${hasData ? 'formato MM:SS' : 'Sin datos para esta franja'}</span>
        </div>
      </div>
      <div class="rcfg-apply-row">
        <span class="rcfg-modify-hint">Solo afecta a la franja <strong>${ts}:00 – ${ts + 1}:00</strong>.</span>
        <button class="btn btn-primary btn-sm" id="rcfg-sec-apply-ts"
                ${!hasData ? 'disabled' : ''}>Aplicar a esta franja</button>
      </div>
    </div>
    <input type="hidden" id="rcfg-sec-ts-original" value="${meanSecs}" />
  `;
}

// ---- Data modification helpers ----

function applySectionChange(sectionKey, dirKey, pct, timeslot) {
  const rows = dirKey === 'toA' ? inputData.timesStopsToA : inputData.timesStopsToB;
  const factor = Math.max(1 + pct / 100, 1e-6); // Avoid negative or zero scaling
  for (const row of rows) {
    if (row.StopsCodes !== sectionKey) continue;
    if (timeslot !== null) {
      const mk = `Mean_${timeslot}`
      if (row[mk] !== undefined) row[mk] = String(parseFloat(row[mk]) * factor);
    } else {
      for (let h = 5; h <= 23; h++) {
        const mk = `Mean_${h}`; 
        if (row[mk] !== undefined) row[mk] = String(parseFloat(row[mk]) * factor);
      }
    }
    break;
  }
}

// ============================================================
// INIT
// ============================================================

document.addEventListener('DOMContentLoaded', async () => {
  simId = getSimId();

  if (!simId.match(/^SIMULATION_\d{8}_\d{6}$/)) {
    document.getElementById('config-loading').innerHTML = `
      <div class="empty-icon">&#9888;</div>
      <p>ID de simulación inválido.</p>
      <a href="/" class="btn btn-outline" style="margin-top:1rem;">&#8592; Volver al dashboard</a>
    `;
    return;
  }

  document.getElementById('config-sim-id-label').textContent = simId;
  document.title = `Configurar ${simId} — EMT`;

  try {
    await loadInputs();
  } catch (err) {
    document.getElementById('config-loading').innerHTML = `
      <div class="empty-icon">&#9888;</div>
      <p>Error al cargar los parámetros.</p>
      <p style="color:var(--emt-red);font-size:0.85rem;margin-top:0.5rem;">${escHtml(err.message)}</p>
      <a href="/" class="btn btn-outline" style="margin-top:1rem;">&#8592; Volver al dashboard</a>
    `;
    return;
  }

  document.getElementById('config-loading').style.display = 'none';
  document.getElementById('config-body').style.display = 'flex';

  // Start with buses view
  const content = document.getElementById('config-content');
  renderBusesView(content);

  // Sidebar navigation
  document.querySelectorAll('.config-nav-btn').forEach(btn => {
    btn.addEventListener('click', () => switchView(btn.dataset.view));
  });

  document.getElementById('btn-save').addEventListener('click', handleSave);
  document.getElementById('btn-run').addEventListener('click', handleRun);

  const socket = io();
  socket.on('sim_completed', ({ id, title }) => {
    toast(`Simulaci\u00f3n completada: ${title || id}`, 'success');
  });
});
