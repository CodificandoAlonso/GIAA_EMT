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
let inputData = { buses: {}, stopsToA: [], stopsToB: [], timesStopsToA: [], timesStopsToB: [] };
let currentView = 'buses';

// Route view state
let _routeFilter = 'general';   // 'general' | 'timeslot'
let _selectedTs  = 8;           // selected timeslot hour
let _currentInfoSel  = null;    // { type:'stop'|'section', stopId, sectionKey, dirKey, stopProps }
let _activeClearSel  = null;    // function to clear current SVG selection

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
  inputData.timesStopsToA = data.timesStopsToA || [];
  inputData.timesStopsToB = data.timesStopsToB || [];

  // Pre-fill meta fields
  if (data.description) {
    if (data.description.title)       document.getElementById('input-title').value       = data.description.title;
    if (data.description.description) document.getElementById('input-description').value = data.description.description;
    if (data.description.line)        document.getElementById('input-line').value         = data.description.line;
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
  };

  const body = {
    description,
    buses:        inputData.buses,
    stopsToA:     inputData.stopsToA,
    stopsToB:     inputData.stopsToB,
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
    toast('Simulación lanzada en segundo plano', 'success');
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

  // Header row
  const header = document.createElement('div');
  header.className = 'buses-editor-header';
  header.innerHTML = `
    <div>
      <h3>Autobuses lógicos</h3>
      <p class="buses-editor-subtitle">Cada autobús lógico tiene una lista de salidas desde los terminales de la línea.</p>
    </div>
    <button class="btn btn-primary btn-sm" id="btn-add-bus">+ Nuevo autobús</button>
  `;
  wrap.appendChild(header);

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
    <p class="add-bus-form-hint">El ID es el identificador del autobús lógico (matrícula/número de unidad).</p>
  `;
  wrap.appendChild(addBusForm);

  // Bus list
  const list = document.createElement('div');
  list.className = 'bus-list';
  list.id = 'bus-list';
  wrap.appendChild(list);

  container.appendChild(wrap);

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

// ---- Distribution metadata ----

const DISTRIBUTIONS = {
  'NORMAL': {
    label: 'Distribución Normal',
    csvValue: 'NORMAL',
    p1: { name: 'μ — media', hint: 'Valor central esperado de pasajeros' },
    p2: { name: 'σ — desv. típica', hint: 'Dispersión alrededor de la media (σ > 0)' },
    cheatsheet: 'Simétrica. Útil cuando los datos se concentran en torno a un valor central con variabilidad constante.',
  },
  'NEGATIVE BINOMIAL': {
    label: 'Distribución Binomial Negativa',
    csvValue: 'NEGATIVE BINOMIAL',
    p1: { name: 'p — prob. de éxito', hint: 'Probabilidad de éxito por ensayo (0 < p ≤ 1)' },
    p2: { name: 'r — nº de éxitos', hint: 'Número de éxitos objetivo (r > 0). Controla la dispersión.' },
    cheatsheet: 'Modela conteos con sobredispersión (varianza > media).',
  },
  'GEOMETRICAL': {
    label: 'Distribución Geométrica',
    csvValue: 'GEOMETRICAL',
    p1: { name: 'p — prob. de éxito', hint: 'Probabilidad de éxito por ensayo (0 < p ≤ 1)' },
    p2: { name: '— (no utilizado)', hint: 'Este parámetro no aplica a la distribución geométrica' },
    cheatsheet: 'Caso especial de la Binomial Negativa con r = 1',
  },
};

const DIST_OPTIONS = Object.keys(DISTRIBUTIONS).map(k =>
  `<option value="${k}">${DISTRIBUTIONS[k].label}</option>`
).join('');

function distLabel(csvVal) {
  return DISTRIBUTIONS[csvVal]?.label ?? csvVal;
}

// ---- Stop info panel ----

function getStopRows(stopId, dirKey) {
  const rows = dirKey === 'toA' ? inputData.stopsToA : inputData.stopsToB;
  return rows.filter(r => String(r.Stop) === String(stopId));
}

function showConfigStopInfo(stopId, stopProps, dirKey) {
  const panel = document.getElementById('rcfg-info-panel');
  if (!panel) return;
  panel.style.display = 'block';

  const rows = getStopRows(stopId, dirKey);
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

  if (rows.length === 0) {
    content += `<p class="rcfg-no-data">No hay datos de pasajeros para esta parada en la dirección seleccionada.</p>`;
  } else if (_routeFilter === 'general') {
    content += buildStopGeneralView(rows);
  } else {
    content += buildStopTimeslotView(rows, _selectedTs);
  }

  panel.innerHTML = content;
  panel.querySelector('#rcfg-panel-close')?.addEventListener('click', closeConfigInfoPanel);

  // Cheatsheet toggle (timeslot view only)
  panel.querySelector('#rcfg-cheatsheet-toggle')?.addEventListener('click', (e) => {
    const cs = panel.querySelector('#rcfg-cheatsheet');
    const open = cs.style.display !== 'none';
    cs.style.display = open ? 'none' : 'block';
    e.currentTarget.textContent = open
      ? '📖 Ver guía rápida de distribuciones'
      : '📖 Ocultar guía rápida';
  });

  if (_routeFilter === 'general') {
    const slider = wireSlider(panel, 'rcfg-global-slider', 'rcfg-global-pct-display');
    panel.querySelector('#rcfg-apply-global')?.addEventListener('click', () => {
      const pct = parseFloat(slider.value);
      applyStopChange(stopId, dirKey, pct, null);
      toast(`Parada ${stopId}: parámetros escalados ${pct > 0 ? '+' : ''}${pct}%`, 'success');
      showConfigStopInfo(stopId, stopProps, dirKey);
    });
  } else {
    // Timeslot: per-datatype edit handlers
    ['board', 'drop'].forEach(tag => {
      const dataType = tag === 'board' ? 'Board' : 'DropOff';

      // Distribution type change → swap param labels
      const distSel = panel.querySelector(`#rcfg-dist-${tag}`);
      distSel?.addEventListener('change', () => {
        const d = DISTRIBUTIONS[distSel.value];
        if (!d) return;
        panel.querySelector(`#rcfg-p1-label-${tag}`).textContent = d.p1.name;
        panel.querySelector(`#rcfg-p1-hint-${tag}`).textContent  = d.p1.hint;
        panel.querySelector(`#rcfg-p2-label-${tag}`).textContent = d.p2.name;
        panel.querySelector(`#rcfg-p2-hint-${tag}`).textContent  = d.p2.hint;
      });

      const sliderTs  = wireSlider(panel, `rcfg-slider-ts-${tag}`,  `rcfg-disp-ts-${tag}`);
      const sliderAll = wireSlider(panel, `rcfg-slider-all-${tag}`, `rcfg-disp-all-${tag}`);

      // Scale by % for this timeslot
      panel.querySelector(`#rcfg-scale-ts-${tag}`)?.addEventListener('click', () => {
        const pct = parseFloat(sliderTs?.value ?? 0);
        applyStopChangeByType(stopId, dirKey, dataType, pct, _selectedTs);
        toast(`Parada ${stopId} ${dataType} franja ${_selectedTs}h: escalado ${pct > 0 ? '+' : ''}${pct}%`, 'success');
        showConfigStopInfo(stopId, stopProps, dirKey);
      });

      // Scale by % for ALL timeslots
      panel.querySelector(`#rcfg-scale-all-${tag}`)?.addEventListener('click', () => {
        const pct = parseFloat(sliderAll?.value ?? 0);
        applyStopChangeByType(stopId, dirKey, dataType, pct, null);
        toast(`Parada ${stopId} ${dataType}: todas las franjas escaladas ${pct > 0 ? '+' : ''}${pct}%`, 'success');
        showConfigStopInfo(stopId, stopProps, dirKey);
      });

      // Save distribution + exact params for this timeslot
      panel.querySelector(`#rcfg-save-ts-${tag}`)?.addEventListener('click', () => {
        const newDist = panel.querySelector(`#rcfg-dist-${tag}`).value;
        const p1 = parseFloat(panel.querySelector(`#rcfg-p1-${tag}`).value);
        const p2 = parseFloat(panel.querySelector(`#rcfg-p2-${tag}`).value);
        if (isNaN(p1) || isNaN(p2)) { toast('Los parámetros deben ser numéricos', 'error'); return; }
        setStopParams(stopId, dirKey, dataType, _selectedTs, newDist, p1, p2);
        toast(`Parada ${stopId} ${dataType} franja ${_selectedTs}h guardada`, 'success');
        showConfigStopInfo(stopId, stopProps, dirKey);
      });
    });
  }
}

// ---- General view: slider potentiometer ----

function buildStopGeneralView(rows) {
  const timeslots = [...new Set(rows.map(r => Number(r.Timeslot)))].sort((a, b) => a - b);
  const boardRows = rows.filter(r => r.DataType === 'Board');
  const dropRows  = rows.filter(r => r.DataType === 'DropOff');

  const avgP1 = (arr) => arr.length
    ? (arr.reduce((s, r) => s + parseFloat(r.Param1 || 0), 0) / arr.length).toFixed(3) : '—';

  const distBoard = boardRows[0]?.DistributionType ?? '—';
  const distDrop  = dropRows[0]?.DistributionType  ?? '—';

  return `
    <div class="rcfg-panel-section">
      <h4>Resumen de la parada</h4>
      <div class="rcfg-stats-grid">
        <div class="rcfg-stat">
          <span class="rcfg-stat-label">&#8679; Subidas (Param1 medio)</span>
          <span class="rcfg-stat-value">${avgP1(boardRows)}</span>
          <span class="rcfg-stat-dist">${distLabel(distBoard)}</span>
        </div>
        <div class="rcfg-stat">
          <span class="rcfg-stat-label">&#8681; Bajadas (Param1 medio)</span>
          <span class="rcfg-stat-value">${avgP1(dropRows)}</span>
          <span class="rcfg-stat-dist">${distLabel(distDrop)}</span>
        </div>
        <div class="rcfg-stat">
          <span class="rcfg-stat-label">Franjas con datos</span>
          <span class="rcfg-stat-value">${timeslots.length}</span>
          <span class="rcfg-stat-dist">${timeslots[0]}h – ${timeslots[timeslots.length-1]}h</span>
        </div>
      </div>
    </div>
    <div class="rcfg-panel-section">
      <h4>Escalar todos los parámetros</h4>
      <p class="rcfg-modify-hint" style="margin-bottom:0.75rem;">
        Multiplica Param1 y Param2 de <strong>subidas y bajadas</strong> en <strong>todas las franjas horarias</strong>.
      </p>
      <div class="rcfg-slider-wrap">
        <div class="rcfg-slider-labels">
          <span>−100%</span><span>0%</span><span>+200%</span>
        </div>
        <input type="range" id="rcfg-global-slider" class="rcfg-slider"
               min="-100" max="200" value="0" step="1" />
        <div class="rcfg-slider-value-row">
          <span class="rcfg-slider-value-label">Ajuste:</span>
          <span id="rcfg-global-pct-display" class="rcfg-slider-display">0%</span>
          <button class="btn btn-primary btn-sm" id="rcfg-apply-global">Aplicar</button>
        </div>
      </div>
    </div>
  `;
}

// ---- Timeslot view: full edit per data type ----

function buildStopTimeslotView(rows, ts) {
  const boardRow = rows.find(r => r.DataType === 'Board'   && Number(r.Timeslot) === ts);
  const dropRow  = rows.find(r => r.DataType === 'DropOff' && Number(r.Timeslot) === ts);

  return `
    <div class="rcfg-panel-section">
      <h4>Franja horaria: ${ts}:00 – ${ts + 1}:00</h4>
      ${buildDistTypeEditor('board', '&#8679; Subidas', boardRow)}
      ${buildDistTypeEditor('drop',  '&#8681; Bajadas', dropRow)}
    </div>
    <div class="rcfg-panel-section rcfg-cheatsheet-section">
      <button class="rcfg-cheatsheet-toggle" id="rcfg-cheatsheet-toggle">
        &#128218; Ver guía rápida de distribuciones
      </button>
      <div class="rcfg-cheatsheet" id="rcfg-cheatsheet" style="display:none;">
        ${Object.values(DISTRIBUTIONS).map(d => `
          <div class="rcfg-cs-item">
            <strong>${d.label}</strong>
            <span class="rcfg-cs-params">${d.p1.name} · ${d.p2.name !== '— (no utilizado)' ? d.p2.name : 'sin Param2'}</span>
            <span class="rcfg-cs-note">${d.cheatsheet}</span>
          </div>
        `).join('')}
      </div>
    </div>
  `;
}

// ---- Slider widget helper ----

function sliderHtml(sliderId, displayId, btnId, btnLabel) {
  return `
    <div class="rcfg-slider-wrap">
      <div class="rcfg-slider-labels">
        <span>−100%</span><span>0%</span><span>+200%</span>
      </div>
      <input type="range" id="${sliderId}" class="rcfg-slider" min="-100" max="200" value="0" step="1" />
      <div class="rcfg-slider-value-row">
        <span class="rcfg-slider-value-label">Ajuste:</span>
        <span id="${displayId}" class="rcfg-slider-display">0%</span>
        <button class="btn btn-primary btn-sm" id="${btnId}">${btnLabel}</button>
      </div>
    </div>
  `;
}

function wireSlider(panel, sliderId, displayId) {
  const slider  = panel.querySelector(`#${sliderId}`);
  const display = panel.querySelector(`#${displayId}`);
  if (slider && display) {
    slider.addEventListener('input', () => {
      display.textContent = (Number(slider.value) > 0 ? '+' : '') + slider.value + '%';
    });
  }
  return slider;
}

function buildDistTypeEditor(tag, labelHtml, row) {
  const distVal  = row?.DistributionType ?? 'NORMAL';
  const d        = DISTRIBUTIONS[distVal] ?? DISTRIBUTIONS['NORMAL'];
  const p1val    = row ? Number(row.Param1).toFixed(6) : '0';
  const p2val    = row ? Number(row.Param2).toFixed(6) : '0';

  // Build select with current value selected
  const distOpts = Object.keys(DISTRIBUTIONS).map(k =>
    `<option value="${k}" ${k === distVal ? 'selected' : ''}>${DISTRIBUTIONS[k].label}</option>`
  ).join('');

  return `
    <div class="rcfg-dtype-card">
      <div class="rcfg-dtype-header">
        <span class="rcfg-dtype-title">${labelHtml}</span>
        <select class="rcfg-dist-select" id="rcfg-dist-${tag}">${distOpts}</select>
      </div>

      <div class="rcfg-params-grid">
        <div class="rcfg-param-field">
          <label class="rcfg-param-label" id="rcfg-p1-label-${tag}">${d.p1.name}</label>
          <input type="number" class="rcfg-param-input" id="rcfg-p1-${tag}" value="${p1val}" step="any" />
          <span class="rcfg-param-hint" id="rcfg-p1-hint-${tag}">${d.p1.hint}</span>
        </div>
        <div class="rcfg-param-field">
          <label class="rcfg-param-label" id="rcfg-p2-label-${tag}">${d.p2.name}</label>
          <input type="number" class="rcfg-param-input" id="rcfg-p2-${tag}" value="${p2val}" step="any" />
          <span class="rcfg-param-hint" id="rcfg-p2-hint-${tag}">${d.p2.hint}</span>
        </div>
      </div>

      <div class="rcfg-dtype-actions">
        <span class="rcfg-scale-label" style="display:block;margin-bottom:0.35rem;">Escalar esta franja:</span>
        ${sliderHtml(`rcfg-slider-ts-${tag}`, `rcfg-disp-ts-${tag}`, `rcfg-scale-ts-${tag}`, 'Aplicar aquí')}
        <span class="rcfg-scale-label" style="display:block;margin:0.65rem 0 0.35rem;">Escalar todas las franjas:</span>
        ${sliderHtml(`rcfg-slider-all-${tag}`, `rcfg-disp-all-${tag}`, `rcfg-scale-all-${tag}`, 'Aplicar a todas')}
        <button class="btn btn-sm btn-primary rcfg-save-ts-btn" id="rcfg-save-ts-${tag}" style="margin-top:0.75rem;">
          &#10003; Guardar distribución y parámetros en franja ${_selectedTs}h
        </button>
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

  const sliderGlobal = wireSlider(panel, 'rcfg-sec-slider-global', 'rcfg-sec-disp-global');
  const sliderTs     = wireSlider(panel, 'rcfg-sec-slider-ts',     'rcfg-sec-disp-ts');
  const sliderTsAll  = wireSlider(panel, 'rcfg-sec-slider-ts-all', 'rcfg-sec-disp-ts-all');

  panel.querySelector('#rcfg-sec-apply-global')?.addEventListener('click', () => {
    const pct = parseFloat(sliderGlobal?.value ?? 0);
    applySectionChange(sectionKey, dirKey, pct, null);
    toast(`Tramo ${sectionKey}: tiempos ajustados ${pct > 0 ? '+' : ''}${pct}%`, 'success');
    showConfigSectionInfo(sectionKey, dirKey);
  });

  panel.querySelector('#rcfg-sec-apply-ts')?.addEventListener('click', () => {
    const pct = parseFloat(sliderTs?.value ?? 0);
    applySectionChange(sectionKey, dirKey, pct, _selectedTs);
    toast(`Tramo ${sectionKey} franja ${_selectedTs}h: ajustado ${pct > 0 ? '+' : ''}${pct}%`, 'success');
    showConfigSectionInfo(sectionKey, dirKey);
  });

  panel.querySelector('#rcfg-sec-apply-ts-all')?.addEventListener('click', () => {
    const pct = parseFloat(sliderTsAll?.value ?? 0);
    applySectionChange(sectionKey, dirKey, pct, null);
    toast(`Tramo ${sectionKey}: todos los tiempos ajustados ${pct > 0 ? '+' : ''}${pct}%`, 'success');
    showConfigSectionInfo(sectionKey, dirKey);
  });
}

function buildSectionGeneralView(row) {
  // Compute average mean across all timeslots
  let sum = 0; let count = 0;
  for (let h = 5; h <= 23; h++) {
    const v = parseFloat(row[`Mean_${h}`]);
    if (!isNaN(v)) { sum += v; count++; }
  }
  const avgMean = count ? (sum / count).toFixed(1) : '—';

  return `
    <div class="rcfg-panel-section">
      <h4>Tiempos de tránsito (general)</h4>
      <div class="rcfg-stats-grid">
        <div class="rcfg-stat"><span class="rcfg-stat-label">Tiempo medio (todas las franjas)</span><span class="rcfg-stat-value">${avgMean} s</span></div>
        <div class="rcfg-stat"><span class="rcfg-stat-label">Tramo</span><span class="rcfg-stat-value">${escHtml(row.StopsCodes)}</span></div>
      </div>
      <div class="rcfg-times-table-wrap">
        <table class="rcfg-times-table">
          <thead><tr><th>Hora</th><th>Media (s)</th><th>Desv. típ. (s)</th></tr></thead>
          <tbody>
            ${Array.from({length: 19}, (_, i) => i + 5).map(h => {
              const mean = row[`Mean_${h}`] ? Number(row[`Mean_${h}`]).toFixed(1) : '—';
              const std  = row[`Std_${h}`]  ? Number(row[`Std_${h}`]).toFixed(1)  : '—';
              return `<tr><td>${h}:00</td><td>${mean}</td><td>${std}</td></tr>`;
            }).join('')}
          </tbody>
        </table>
      </div>
    </div>
    <div class="rcfg-panel-section">
      <h4>Modificar todos los tiempos</h4>
      <p class="rcfg-modify-hint" style="margin-bottom:0.75rem;">Multiplica Media y Desviación en todas las franjas horarias.</p>
      ${sliderHtml('rcfg-sec-slider-global', 'rcfg-sec-disp-global', 'rcfg-sec-apply-global', 'Aplicar a todas las franjas')}
    </div>
  `;
}

function buildSectionTimeslotView(row, ts) {
  const mean = row[`Mean_${ts}`] ? Number(row[`Mean_${ts}`]).toFixed(2) : '—';
  const std  = row[`Std_${ts}`]  ? Number(row[`Std_${ts}`]).toFixed(2)  : '—';

  return `
    <div class="rcfg-panel-section">
      <h4>Franja horaria: ${ts}:00 – ${ts + 1}:00</h4>
      <div class="rcfg-stats-grid">
        <div class="rcfg-stat"><span class="rcfg-stat-label">Tiempo medio</span><span class="rcfg-stat-value">${mean} s</span></div>
        <div class="rcfg-stat"><span class="rcfg-stat-label">Desviación típica</span><span class="rcfg-stat-value">${std} s</span></div>
      </div>
    </div>
    <div class="rcfg-panel-section">
      <h4>Modificar esta franja (${ts}h)</h4>
      <span class="rcfg-modify-label" style="display:block;margin-bottom:0.4rem;">Sólo franja ${ts}h</span>
      ${sliderHtml('rcfg-sec-slider-ts', 'rcfg-sec-disp-ts', 'rcfg-sec-apply-ts', 'Aplicar a esta franja')}
      <span class="rcfg-modify-label" style="display:block;margin:0.75rem 0 0.4rem;">Todas las franjas</span>
      ${sliderHtml('rcfg-sec-slider-ts-all', 'rcfg-sec-disp-ts-all', 'rcfg-sec-apply-ts-all', 'Aplicar a todas las franjas')}
    </div>
  `;
}

// ---- Data modification helpers ----

// Scale Param1+Param2 for ALL dataTypes of a stop (used by general slider)
function applyStopChange(stopId, dirKey, pct, timeslot) {
  const rows = dirKey === 'toA' ? inputData.stopsToA : inputData.stopsToB;
  const factor = Math.max(1 + pct / 100, 1e-6); // Avoid negative or zero scaling

  for (const row of rows) {
    if (String(row.Stop) !== String(stopId)) continue;
    if (timeslot !== null && Number(row.Timeslot) !== timeslot) continue;

    if (row.DistributionType === 'NORMAL') {
    row.Param1 = String(parseFloat(row.Param1) * factor);
    }
    else if (row.DistributionType === 'NEGATIVE BINOMIAL') {
    row.Param1 = String(1 / (1 + factor * (1 - row.Param1) /row.Param1)); // p' = 1 / (1 + k*(1-p)/p) 
  }
    else if (row.DistributionType === 'GEOMETRICAL') {
    row.Param1 = String(row.Param1 / factor);    
  }
  }
}



//todo: REVIEW FORMULA FOR REFACTORING
// Scale Param1+Param2 for a specific dataType ('Board' | 'DropOff') of a stop
function applyStopChangeByType(stopId, dirKey, dataType, pct, timeslot) {
  const rows = dirKey === 'toA' ? inputData.stopsToA : inputData.stopsToB;
  const factor = Math.max(1 + pct / 100, 1e-6); // Avoid negative or zero scaling
  for (const row of rows) {
    if (String(row.Stop) !== String(stopId)) continue;
    if (row.DataType !== dataType) continue;
    if (timeslot !== null && Number(row.Timeslot) !== timeslot) continue;

    if (row.DistributionType === 'NORMAL') {
    row.Param1 = String(parseFloat(row.Param1) * factor);
    }
    else if (row.DistributionType === 'NEGATIVE BINOMIAL') {
    row.Param1 = String(1 / (1 + factor * (1 - parseFloat(row.Param1)) /parseFloat(row.Param1))); // p' = 1 / (1 + k*(1-p)/p) 
  }
    else if (row.DistributionType === 'GEOMETRICAL') {
    row.Param1 = String(parseFloat(row.Param1) / factor);    
  }

  }
}
// Set exact distribution type + params for a specific dataType + timeslot
function setStopParams(stopId, dirKey, dataType, timeslot, distType, p1, p2) {
  const rows = dirKey === 'toA' ? inputData.stopsToA : inputData.stopsToB;
  const csvDist = DISTRIBUTIONS[distType]?.csvValue ?? distType;
  for (const row of rows) {
    if (String(row.Stop) !== String(stopId)) continue;
    if (row.DataType !== dataType) continue;
    if (Number(row.Timeslot) !== timeslot) continue;
    row.DistributionType = csvDist;
    row.Param1 = String(p1);
    row.Param2 = String(p2);
    return;
  }
  // Row doesn't exist yet — create it
  const arr = dirKey === 'toA' ? inputData.stopsToA : inputData.stopsToB;
  arr.push({
    Stop: String(stopId),
    Timeslot: String(timeslot),
    DataType: dataType,
    DistributionType: csvDist,
    Param1: String(p1),
    Param2: String(p2),
  });
}

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
});
