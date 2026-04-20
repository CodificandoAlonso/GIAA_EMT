// ---- Utilities ----

function toast(msg, type = 'info') {
  const container = document.getElementById('toast-container');
  const el = document.createElement('div');
  el.className = `toast ${type}`;
  el.textContent = msg;
  container.appendChild(el);
  setTimeout(() => el.remove(), 5000);
}

function formatNum(n) {
  if (n === null || n === undefined || isNaN(n)) return '—';
  return Number(n).toLocaleString('es-ES');
}

function formatDuration(secs) {
  if (secs == null || isNaN(secs)) return '—';
  const s = Math.round(secs);
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  const sec = s % 60;
  if (h > 0) {
    return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(sec).padStart(2, '0')}`;
  }
  return `${String(m).padStart(2, '0')}:${String(sec).padStart(2, '0')}`;
}

// Parse scheduled time like "6:25" or "14:30" into total minutes from midnight
function parseScheduledMinutes(timeStr) {
  if (!timeStr) return null;
  const [h, m] = timeStr.split(':').map(Number);
  if (isNaN(h) || isNaN(m)) return null;
  return h * 60 + m;
}

// Format total minutes (possibly past 1440 = 24:00) as HH:MM
// Past midnight shows as 00:MM, 01:MM, etc.
function formatClockTime(totalMinutes) {
  if (totalMinutes == null || isNaN(totalMinutes)) return '—';
  const wrapped = ((totalMinutes % 1440) + 1440) % 1440;
  const h = Math.floor(wrapped / 60);
  const m = Math.floor(wrapped % 60);
  return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}`;
}

// Compute mean real departure time given scheduled time string, pct delay, mean delay seconds
// Returns formatted string like "06:25" or "01:03 (+1d)"
function computeMeanDeparture(scheduledTimeStr, pctDelay, meanDelaySeconds) {
  const scheduledMins = parseScheduledMinutes(scheduledTimeStr);
  if (scheduledMins === null) return '—';
  if (!pctDelay || pctDelay === 0) return formatClockTime(scheduledMins);

  const fracDelay = pctDelay / 100;
  const delayMins = meanDelaySeconds != null ? meanDelaySeconds / 60 : 0;
  // Mean departure = (1 - fracDelay) * scheduled + fracDelay * (scheduled + delayMins)
  //                = scheduled + fracDelay * delayMins
  const meanMins = scheduledMins + fracDelay * delayMins;
  const formatted = formatClockTime(meanMins);

  // If it crossed midnight
  const crossed = meanMins >= 1440 ? ' (+1d)' : '';
  return formatted + crossed;
}

function getSimId() {
  const parts = window.location.pathname.split('/');
  return parts[parts.length - 1];
}

// ---- Colorize log output ----

function colorizeLog(text) {
  return text
    .split('\n')
    .map(line => {
      if (line.includes('[SUCCESS]') || line.includes('SUCCESS')) return `<span class="log-success">${escHtml(line)}</span>`;
      if (line.includes('[INFO]') || line.includes('INFO')) return `<span class="log-info">${escHtml(line)}</span>`;
      if (line.includes('[WARN]') || line.includes('WARNING')) return `<span class="log-warn">${escHtml(line)}</span>`;
      if (line.includes('[ERROR]') || line.includes('ERROR')) return `<span class="log-error">${escHtml(line)}</span>`;
      return escHtml(line);
    })
    .join('\n');
}

function escHtml(str) {
  return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

// ---- Load simulation detail ----

async function loadDetail(simId) {
  try {
    const detailRes = await fetch(`/api/simulations/${simId}`);
    if (!detailRes.ok) throw new Error(`Simulación no encontrada (HTTP ${detailRes.status})`);
    const detail = await detailRes.json();

    document.getElementById('hero-id').textContent = detail.id;
    document.getElementById('hero-date').textContent = detail.title || detail.datetime || detail.id;
    document.getElementById('hero-subtitle').textContent = detail.description
      ? detail.description
      : (detail.datetime || '');
    document.title = `${detail.title || detail.id} — EMT Dashboard`;

    document.getElementById('ds-runs').textContent = formatNum(detail.runCount);

    if (detail.logContent) {
      const match = detail.logContent.match(/TOTAL PIPELINE TIME:\s*(.+)/);
      if (match) {
        document.getElementById('ds-total-time').textContent = match[1].trim();
      }
    }

    loadGeodata(simId);
    loadPlotsInfo(simId);

    const logEl = document.getElementById('log-viewer');
    if (detail.logContent) {
      logEl.innerHTML = colorizeLog(detail.logContent);
    } else {
      logEl.textContent = 'No se encontró archivo de log.';
    }

    document.getElementById('loading-state').style.display = 'none';
    document.getElementById('sim-content').style.display = 'block';

  } catch (err) {
    document.getElementById('loading-state').innerHTML = `
      <div class="empty-icon">&#9888;</div>
      <p>Error al cargar la simulación.</p>
      <p style="margin-top:0.5rem;font-size:0.83rem;color:var(--emt-red);">${err.message}</p>
      <a href="/" class="btn btn-outline" style="margin-top:1rem;">&#8592; Volver al dashboard</a>
    `;
    toast('Error al cargar la simulación: ' + err.message, 'error');
  }
}

// ---- Route map (SVG renderer) ----

let _dirNames = { toA: 'A', toB: 'B' };

async function loadDirNames(expId) {
  try {
    const res = await fetch(`/data/known_data/general_info/${expId}.json`);
    if (!res.ok) return;
    const data = await res.json();
    const parseName = arr => {
      const s = arr?.[0] || '';
      const m = s.match(/\d+\s+(.+)/);
      return m ? m[1] : s;
    };
    _dirNames.toA = parseName(data.toA);
    _dirNames.toB = parseName(data.toB);
    const lA = document.getElementById('occ-toA-label');
    const lB = document.getElementById('occ-toB-label');
    if (lA) lA.innerHTML = `&#8594; Ocupacion media Sentido ${_dirNames.toA}`;
    if (lB) lB.innerHTML = `&#8592; Ocupación media Sentido ${_dirNames.toB}`;
  } catch (_) {}
}

// ---- Plots info cache ----
let _plotsInfo = null;

async function loadPlotsInfo(simId) {
  try {
    const res = await fetch(`/api/simulations/${simId}/plots-info`);
    if (!res.ok) return;
    _plotsInfo = await res.json();
    if (_plotsInfo.generalStats) renderOccupationStats(_plotsInfo.generalStats);
  } catch (_) {}
}

function renderOccupationStats(s) {
  const card = document.getElementById('occ-plots-card');
  if (card) card.style.display = '';
  const fmt = v => (v != null && !isNaN(v)) ? v.toFixed(1) + '%' : '—';
  document.getElementById('occ-general').textContent        = fmt(s.Occupation);
  document.getElementById('occ-toA').textContent            = fmt(s.Occupation_toA);
  document.getElementById('occ-toB').textContent            = fmt(s.Occupation_toB);
  document.getElementById('occ-logical-buses').textContent  = s.Logical_Buses != null ? String(s.Logical_Buses) : '—';
  document.getElementById('occ-total-trips').textContent    = s.Total_Trips   != null ? String(s.Total_Trips)   : '—';
  document.getElementById('occ-mean-await').textContent     = s.Mean_await_passengers != null ? formatDuration(s.Mean_await_passengers) : '—';
  document.getElementById('occ-reg-value').textContent      = +s.Regularity_value.toFixed(2);
}

// ---- View toggle (Route / Bus) ----

// Route filter state: 'general' | 'timeslot'
let _routeFilter = 'general';

function initViewToggle() {
  const routeBtn  = document.getElementById('view-route-btn');
  const busBtn    = document.getElementById('view-bus-btn');
  const routeSec  = document.getElementById('view-route-section');
  const busSec    = document.getElementById('view-bus-section');
  const expTabs   = document.getElementById('exp-tabs');

  routeBtn.addEventListener('click', () => {
    routeBtn.className = 'btn btn-sm btn-primary';
    busBtn.className   = 'btn btn-sm btn-outline';
    routeSec.style.display = '';
    busSec.style.display   = 'none';
    expTabs.style.display  = 'flex';
  });

  busBtn.addEventListener('click', () => {
    busBtn.className   = 'btn btn-sm btn-primary';
    routeBtn.className = 'btn btn-sm btn-outline';
    busSec.style.display   = '';
    routeSec.style.display = 'none';
    expTabs.style.display  = 'none';
    renderBusView();
  });
}

// ---- Bus view ----

// Bus filter state: 'bus' | 'timeslot'
let _busFilter = 'bus';
let _busViewRendered = false;

function renderBusView() {
  if (_busViewRendered) return;
  _busViewRendered = true;

  const container = document.getElementById('bus-view-container');

  if (!_plotsInfo?.busSchedule || Object.keys(_plotsInfo.busSchedule).length === 0) {
    container.innerHTML = '<div class="empty-state"><p>No hay datos de autobuses disponibles.</p></div>';
    return;
  }

  container.innerHTML = `
    <div class="bus-filter-bar">
      <span class="analysis-filter-label">Ver por:</span>
      <button class="filter-btn active" id="bus-filter-bus-btn">&#128652; Autobús Físico</button>
      <button class="filter-btn" id="bus-filter-ts-btn">&#128336; Franja horaria</button>
    </div>
    <div id="bus-filter-content"></div>
  `;

  document.getElementById('bus-filter-bus-btn').addEventListener('click', () => {
    _busFilter = 'bus';
    document.getElementById('bus-filter-bus-btn').classList.add('active');
    document.getElementById('bus-filter-ts-btn').classList.remove('active');
    renderBusByBusView();
  });
  document.getElementById('bus-filter-ts-btn').addEventListener('click', () => {
    _busFilter = 'timeslot';
    document.getElementById('bus-filter-ts-btn').classList.add('active');
    document.getElementById('bus-filter-bus-btn').classList.remove('active');
    renderBusByTimeslotView();
  });

  renderBusByBusView();
}

function renderBusByBusView() {
  const content = document.getElementById('bus-filter-content');
  const { busSchedule, busMetrics } = _plotsInfo;
  const busIds = Object.keys(busSchedule).sort((a, b) => Number(a) - Number(b));

  const pillsHtml = busIds.map(id =>
    `<button class="bus-pill" data-bus="${id}">${id}</button>`
  ).join('');

  content.innerHTML = `
    <div class="bus-selector-section">
      <div class="bus-selector-label">Selecciona un autobús físico:</div>
      <div class="bus-pills" id="bus-pills">${pillsHtml}</div>
    </div>
    <div id="bus-detail-panel" style="display:none;"></div>
  `;

  content.querySelectorAll('.bus-pill').forEach(btn => {
    btn.addEventListener('click', () => {
      content.querySelectorAll('.bus-pill').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      renderBusDetail(btn.dataset.bus, busSchedule, busMetrics, /* showBusId */ false);
    });
  });
}

function renderBusByTimeslotView() {
  const content = document.getElementById('bus-filter-content');
  const { busSchedule, busMetrics } = _plotsInfo;

  // Group all trips by timeslot (hour of departure)
  // trip hour = parseInt(time.split(':')[0])
  const byTimeslot = {}; // { hour: [ { busId, stopId, time, metrics, direction, dirIndex } ] }
  const dirCount = {}; // { busId: { toA: N, toB: N } }

  for (const busId of Object.keys(busSchedule)) {
    dirCount[busId] = { toA: 0, toB: 0 };
  }

  for (const busId of Object.keys(busSchedule)) {
    const schedule = busSchedule[busId] || [];
    const metrics  = busMetrics?.[busId] || {};
    const localDirCount = { toA: 0, toB: 0 };

    schedule.forEach(([stopId, time]) => {
      const hour = parseInt(time.split(':')[0]);
      const key  = `${stopId}-${time}`;
      const m    = metrics[key];
      const dir  = normalizeDir(m?.Direction);
      const di   = localDirCount[dir]++;
      if (!byTimeslot[hour]) byTimeslot[hour] = [];
      byTimeslot[hour].push({ busId, stopId, time, metrics: m, direction: dir, dirIndex: di });
    });
  }

  const hours = Object.keys(byTimeslot).map(Number).sort((a, b) => a - b);

  const pillsHtml = hours.map(h =>
    `<button class="bus-ts-pill" data-hour="${h}">${h}:00</button>`
  ).join('');

  content.innerHTML = `
    <div class="bus-ts-header">
      <span class="analysis-filter-label">Franja horaria:</span>
      ${pillsHtml}
    </div>
    <div id="bus-ts-detail-panel"></div>
  `;

  content.querySelectorAll('.bus-ts-pill').forEach(btn => {
    btn.addEventListener('click', () => {
      content.querySelectorAll('.bus-ts-pill').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      renderBusTimeslotDetail(byTimeslot[Number(btn.dataset.hour)]);
    });
  });
}

function renderBusTimeslotDetail(trips) {
  const panel = document.getElementById('bus-ts-detail-panel');
  if (!panel) return;

  const rows = trips.map((t, i) => {
    const m        = t.metrics;
    const dirLabel = t.direction === 'toA' ? `&#8594; ${_dirNames.toA}` : `&#8592; ${_dirNames.toB}`;
    const dirClass = t.direction === 'toA' ? 'dir-badge-a' : 'dir-badge-b';
    const occ      = m?.Mean_Occupation_Percentage != null ? m.Mean_Occupation_Percentage.toFixed(1) + '%' : '—';
    const tTime    = formatDuration(m?.Mean_time_of_trip);
    const meanDep  = computeMeanDeparture(t.time, m?.Percentage_sims_delay_departure, m?.Mean_Minutes_departure_delay);
    return `
      <tr class="trip-row" data-idx="${i}">
        <td class="trip-num">${i}</td>
        <td><span class="trip-stop">${t.stopId}</span></td>
        <td class="trip-time-val">${t.time}</td>
        <td><span class="dir-badge ${dirClass}">${dirLabel}</span> <span class="bus-id-badge">${t.busId}</span></td>
        <td class="trip-occ">${occ}</td>
        <td>${tTime}</td>
        <td style="font-family:monospace;">${meanDep}</td>
      </tr>`;
  }).join('');

  panel.innerHTML = `
    <div class="bus-detail-grid">
      <div class="bus-trips-section">
        <div class="bus-section-title">Viajes en esta franja &mdash; ${trips.length} viaje${trips.length !== 1 ? 's' : ''}</div>
        <table class="trip-table">
          <thead>
            <tr>
              <th>#</th><th>Parada</th><th>Prog.</th>
              <th>Sentido / Bus</th><th>Ocup.</th><th>T. viaje</th><th>Salida</th>
            </tr>
          </thead>
          <tbody>${rows}</tbody>
        </table>
      </div>
      <div id="bus-ts-trip-detail" class="trip-detail-panel">
        <div class="empty-state" style="padding:2.5rem;">
          <div class="empty-icon" style="font-size:2rem;">&#128652;</div>
          <p style="font-size:0.85rem;">Selecciona un viaje para ver detalles</p>
        </div>
      </div>
    </div>
  `;

  panel.querySelectorAll('.trip-row').forEach(row => {
    row.addEventListener('click', () => {
      panel.querySelectorAll('.trip-row').forEach(r => r.classList.remove('selected'));
      row.classList.add('selected');
      const t = trips[Number(row.dataset.idx)];
      renderTripDetail(t, document.getElementById('bus-ts-trip-detail'));
    });
  });
}

function normalizeDir(dir) {
  if (!dir) return 'toA';
  return (dir === 'to_A' || dir === 'toA') ? 'toA' : 'toB';
}

function renderBusDetail(busId, busSchedule, busMetrics, showBusId = false) {
  const panel = document.getElementById('bus-detail-panel');
  panel.style.display = '';

  const schedule = busSchedule[busId] || [];
  const metrics  = busMetrics?.[busId]  || {};

  const dirCount = { toA: 0, toB: 0 };
  const trips = schedule.map(([stopId, time], globalIdx) => {
    const key = `${stopId}-${time}`;
    const m   = metrics[key];
    const dir = normalizeDir(m?.Direction);
    return { busId, stopId, time, key, metrics: m, direction: dir, dirIndex: dirCount[dir]++, globalIdx };
  });

  const rows = trips.map((t, i) => {
    const m        = t.metrics;
    const dirLabel = t.direction === 'toA' ? `&#8594; ${_dirNames.toA}` : `&#8592; ${_dirNames.toB}`;
    const dirClass = t.direction === 'toA' ? 'dir-badge-a' : 'dir-badge-b';
    const occ      = m?.Mean_Occupation_Percentage != null ? m.Mean_Occupation_Percentage.toFixed(1) + '%' : '—';
    const tTime    = formatDuration(m?.Mean_time_of_trip);
    const meanDep  = computeMeanDeparture(t.time, m?.Percentage_sims_delay_departure, m?.Mean_Minutes_departure_delay);
    const busCell  = showBusId ? `<span class="bus-id-badge">${t.busId}</span>` : '';
    return `
      <tr class="trip-row" data-idx="${i}">
        <td class="trip-num">${i}</td>
        <td><span class="trip-stop">${t.stopId}</span></td>
        <td class="trip-time-val">${t.time}</td>
        <td><span class="dir-badge ${dirClass}">${dirLabel}</span>${busCell}</td>
        <td class="trip-occ">${occ}</td>
        <td>${tTime}</td>
        <td style="font-family:monospace;">${meanDep}</td>
      </tr>`;
  }).join('');

  panel.innerHTML = `
    <div class="bus-detail-grid">
      <div class="bus-trips-section">
        <div class="bus-section-title">Autobús ${busId} &mdash; ${trips.length} viaje${trips.length !== 1 ? 's' : ''}</div>
        <table class="trip-table">
          <thead>
            <tr>
              <th>#</th><th>Parada</th><th>Prog.</th>
              <th>Sentido</th><th>Ocup.</th><th>T. viaje</th><th>Salida</th>
            </tr>
          </thead>
          <tbody>${rows}</tbody>
        </table>
      </div>
      <div id="trip-detail-panel" class="trip-detail-panel">
        <div class="empty-state" style="padding:2.5rem;">
          <div class="empty-icon" style="font-size:2rem;">&#128652;</div>
          <p style="font-size:0.85rem;">Selecciona un viaje para ver detalles</p>
        </div>
      </div>
    </div>
  `;

  panel.querySelectorAll('.trip-row').forEach(row => {
    row.addEventListener('click', () => {
      panel.querySelectorAll('.trip-row').forEach(r => r.classList.remove('selected'));
      row.classList.add('selected');
      renderTripDetail(trips[Number(row.dataset.idx)], document.getElementById('trip-detail-panel'));
    });
  });
}

function renderTripDetail(trip, panel) {
  if (!panel) return;
  const m     = trip.metrics;
  const fmt   = (v, suf = '') => (v != null && !isNaN(v)) ? Number(v).toFixed(2) + suf : '—';

  const dirLabel = trip.direction === 'toA' ? `&#8594; Sentido ${_dirNames.toA}` : `&#8592; Sentido ${_dirNames.toB}`;
  const dirClass = trip.direction === 'toA' ? 'dir-badge-a' : 'dir-badge-b';
  const meanDep  = computeMeanDeparture(trip.time, m?.Percentage_sims_delay_departure, m?.Mean_Minutes_departure_delay);

  // Bus plots for this trip
  const busPlotUrls = _plotsInfo?.busPlots?.[trip.busId]?.[trip.direction] || [];
  const plotUrl = busPlotUrls[trip.dirIndex];
  const plotHtml = plotUrl ? `
    <div class="trip-plots-wrap">
      <div class="trip-plot-label">Ocupación media por parada</div>
      <div class="trip-plot-item plot-expandable" onclick="openImgModal('${plotUrl}')">
        <img class="trip-plot-img" src="${plotUrl}" alt="Gráfica de ocupación" loading="lazy" />
        <div class="plot-expand-hint">&#128269; Clic para ampliar</div>
      </div>
    </div>` : '';

  panel.innerHTML = `
    <div class="trip-detail-header">
      <span class="dir-badge ${dirClass}">${dirLabel}</span>
      <span class="trip-detail-id">Bus ${trip.busId} &middot; Viaje ${trip.globalIdx ?? trip.dirIndex} &middot; ${trip.stopId} · ${trip.time}</span>
    </div>
    <div class="trip-metrics-grid">
      <div class="trip-metric-card">
        <div class="trip-metric-label">Ocupación media</div>
        <div class="trip-metric-value">${fmt(m?.Mean_Occupation_Percentage, '%')}</div>
      </div>
      <div class="trip-metric-card">
        <div class="trip-metric-label">Tiempo de viaje</div>
        <div class="trip-metric-value">${formatDuration(m?.Mean_time_of_trip)}</div>
      </div>
      <div class="trip-metric-card">
        <div class="trip-metric-label">% Simulaciones con retraso</div>
        <div class="trip-metric-value">${fmt(m?.Percentage_sims_delay_departure, '%')}</div>
      </div>
      <div class="trip-metric-card">
        <div class="trip-metric-label">Retraso medio de salida</div>
        <div class="trip-metric-value">${formatDuration(m?.Mean_Minutes_departure_delay)}</div>
      </div>
      <div class="trip-metric-card">
        <div class="trip-metric-label">Hora programada</div>
        <div class="trip-metric-value" style="font-size:1rem;">${trip.time}</div>
      </div>
      <div class="trip-metric-card">
        <div class="trip-metric-label">Salida media real</div>
        <div class="trip-metric-value" style="font-size:1rem;">${meanDep}</div>
      </div>
    </div>
    ${plotHtml}
  `;
}

// ---- Route info panel: filter state ----
// 'general' | 'timeslot'
let _routeInfoFilter = 'general';
let _routeInfoSelectedTs = 5;  // default timeslot

// Reference to the active map's clearSelection
let _activeClearSelection = null;

function closeInfoPanel() {
  if (_activeClearSelection) {
    _activeClearSelection();
    _activeClearSelection = null;
  }
  const panel = document.getElementById('route-info-panel');
  if (panel) panel.style.display = 'none';
}

const _svgTooltip = (() => {
  const el = document.createElement('div');
  el.className = 'route-tooltip';
  document.body.appendChild(el);
  return el;
})();

function showTooltip(e, html) {
  _svgTooltip.innerHTML = html;
  _svgTooltip.style.display = 'block';
  positionTooltip(e);
}

function positionTooltip(e) {
  _svgTooltip.style.left = (e.clientX + 14) + 'px';
  _svgTooltip.style.top  = (e.clientY - 10) + 'px';
}

function hideTooltip() {
  _svgTooltip.style.display = 'none';
}

async function loadGeodata(simId) {
  const container = document.getElementById('map-container');
  try {
    const [, data] = await Promise.all([
      loadDirNames('E01'),
      fetch(`/api/simulations/${simId}/geodata`).then(r => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      }),
    ]);

    if (!data.experiments || data.experiments.length === 0) {
      container.innerHTML = '<p style="padding:1.5rem;color:var(--emt-gray-600);">No se encontraron datos geoespaciales para esta simulación.</p>';
      return;
    }

    const e01 = data.experiments.find(e => e.expId === 'E01') ?? data.experiments[0];
    renderDirectionMaps(e01);

  } catch (err) {
    container.innerHTML = `<p style="padding:1.5rem;color:var(--emt-red);">Error al cargar geodata: ${escHtml(err.message)}</p>`;
  }
}

function renderDirectionMaps(exp) {
  const container = document.getElementById('map-container');
  container.innerHTML = `
    <div class="analysis-filter-bar">
      <span class="analysis-filter-label">Mostrar info por:</span>
      <button class="filter-btn active" id="route-filter-general-btn">&#128202; General</button>
      <button class="filter-btn" id="route-filter-ts-btn">&#128336; Franja horaria</button>
    </div>
    <div class="direction-maps">
      <div class="direction-map-panel">
        <div class="direction-map-label dir-label-a">&#8594; Sentido ${_dirNames.toA}</div>
        <svg id="svg-toA" class="route-svg"></svg>
      </div>
      <div class="direction-map-panel">
        <div class="direction-map-label dir-label-b">&#8592; Sentido ${_dirNames.toB}</div>
        <svg id="svg-toB" class="route-svg"></svg>
      </div>
    </div>
    <div id="route-info-panel" class="route-info-panel" style="display:none;"></div>
  `;

  document.getElementById('route-filter-general-btn').addEventListener('click', () => {
    _routeInfoFilter = 'general';
    document.getElementById('route-filter-general-btn').classList.add('active');
    document.getElementById('route-filter-ts-btn').classList.remove('active');
    // Refresh panel if something is selected
    refreshInfoPanel();
  });

  document.getElementById('route-filter-ts-btn').addEventListener('click', () => {
    _routeInfoFilter = 'timeslot';
    document.getElementById('route-filter-ts-btn').classList.add('active');
    document.getElementById('route-filter-general-btn').classList.remove('active');
    refreshInfoPanel();
  });

  buildSvgMap(document.getElementById('svg-toA'), exp.toA, 'toA');
  buildSvgMap(document.getElementById('svg-toB'), exp.toB, 'toB');
}

// Track what is currently selected in the info panel
let _currentInfoSelection = null; // { type: 'stop'|'section', data, dirKey }

function refreshInfoPanel() {
  if (!_currentInfoSelection) return;
  if (_currentInfoSelection.type === 'stop') {
    showStopInfo(_currentInfoSelection.data, _currentInfoSelection.dirKey);
  } else {
    showSectionInfo(_currentInfoSelection.data, _currentInfoSelection.dirKey);
  }
}

async function buildSvgMap(svgEl, dirData, dirKey) {
  const ns = 'http://www.w3.org/2000/svg';

  const loading = document.createElementNS(ns, 'text');
  loading.setAttribute('x', '50%');
  loading.setAttribute('y', '50%');
  loading.setAttribute('text-anchor', 'middle');
  loading.setAttribute('dominant-baseline', 'middle');
  loading.setAttribute('fill', '#aaa');
  loading.setAttribute('font-size', '13');
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
      from,
      to: sortedStops[i + 1],
      visPaths: [],
      hitPaths: [],
      fromCircle: null,
      toCircle: null,
    }));

    function assignSection(dist) {
      for (let i = 0; i < sections.length; i++) {
        if (dist < sections[i].to.props.distance) return i;
      }
      return sections.length - 1;
    }

    const allCoords = [];
    for (const f of routeGeo.features) {
      const rings = f.geometry.type === 'MultiLineString'
        ? f.geometry.coordinates : [f.geometry.coordinates];
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
    const W = rect.width || 600;
    const H = rect.height || 380;
    const PAD = 32;

    const rangeX = maxLng - minLng || 0.001;
    const rangeY = maxLat - minLat || 0.001;
    const scaleX = (W - 2 * PAD) / rangeX;
    const scaleY = (H - 2 * PAD) / rangeY;
    const scale  = Math.min(scaleX, scaleY);

    const drawW = rangeX * scale;
    const drawH = rangeY * scale;
    const offX  = PAD + (W - 2 * PAD - drawW) / 2;
    const offY  = PAD + (H - 2 * PAD - drawH) / 2;

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
      sections[idx].visPaths.forEach(p => {
        p.setAttribute('stroke', color);
        p.setAttribute('stroke-width', weight);
      });
    }

    function styleStops(idx, fill, stroke) {
      const s = sections[idx];
      [s.fromCircle, s.toCircle].forEach(c => {
        if (c) {
          c.setAttribute('fill', fill);
          c.setAttribute('stroke', stroke);
          c.setAttribute('r', fill === C_STOP_DEF ? '6' : '8');
        }
      });
    }

    function styleStopCircle(i, fill, stroke, r) {
      const c = stopCircles[i];
      if (c) {
        c.setAttribute('fill', fill);
        c.setAttribute('stroke', stroke);
        c.setAttribute('r', r);
      }
    }

    function clearSelection() {
      if (selectedIdx >= 0) {
        styleSection(selectedIdx, C_DEFAULT, '3');
        styleStops(selectedIdx, C_STOP_DEF, C_DEFAULT);
        selectedIdx = -1;
      }
      if (selectedStopIdx >= 0) {
        styleStopCircle(selectedStopIdx, C_STOP_DEF, C_DEFAULT, '6');
        selectedStopIdx = -1;
      }
    }

    // Draw route paths grouped by section
    for (const f of routeGeo.features) {
      const sIdx = assignSection(f.properties.distance);
      const rings = f.geometry.type === 'MultiLineString'
        ? f.geometry.coordinates : [f.geometry.coordinates];

      for (const ring of rings) {
        const pts = ring.map(project);
        const d   = 'M ' + pts.map(([x, y]) => `${x.toFixed(1)},${y.toFixed(1)}`).join(' L ');

        const vis = document.createElementNS(ns, 'path');
        vis.setAttribute('d', d);
        vis.setAttribute('stroke', C_DEFAULT);
        vis.setAttribute('stroke-width', '3');
        vis.setAttribute('fill', 'none');
        vis.setAttribute('stroke-linecap', 'round');
        vis.setAttribute('stroke-linejoin', 'round');

        const hit = document.createElementNS(ns, 'path');
        hit.setAttribute('d', d);
        hit.setAttribute('stroke', 'transparent');
        hit.setAttribute('stroke-width', '14');
        hit.setAttribute('fill', 'none');
        hit.style.cursor = 'pointer';

        sections[sIdx].visPaths.push(vis);
        sections[sIdx].hitPaths.push(hit);

        svgEl.appendChild(vis);
        svgEl.appendChild(hit);
      }
    }

    sections.forEach((sec, sIdx) => {
      const tooltipHtml = () =>
        `<strong>${sec.from.props.stopNum}</strong> ${escHtml(sec.from.props.stopName)}`
        + `&nbsp;&#8594;&nbsp;`
        + `<strong>${sec.to.props.stopNum}</strong> ${escHtml(sec.to.props.stopName)}`;

      sec.hitPaths.forEach(hit => {
        hit.addEventListener('mouseenter', e => {
          if (selectedIdx !== sIdx) styleSection(sIdx, C_HOVER, '5');
          showTooltip(e, tooltipHtml());
        });
        hit.addEventListener('mousemove', positionTooltip);
        hit.addEventListener('mouseleave', () => {
          if (selectedIdx !== sIdx) styleSection(sIdx, C_DEFAULT, '3');
          hideTooltip();
        });
        hit.addEventListener('click', () => {
          const wasSelected = selectedIdx === sIdx;
          if (_activeClearSelection && _activeClearSelection !== clearSelection) {
            _activeClearSelection();
            _activeClearSelection = null;
          }
          clearSelection();
          if (!wasSelected) {
            styleSection(sIdx, C_SELECTED, '5');
            styleStops(sIdx, C_STOP_SEL, C_SELECTED);
            selectedIdx = sIdx;
            _activeClearSelection = clearSelection;
            _currentInfoSelection = { type: 'section', data: sec, dirKey };
            showSectionInfo(sec, dirKey);
          } else {
            _activeClearSelection = null;
            _currentInfoSelection = null;
            const panel = document.getElementById('route-info-panel');
            if (panel) panel.style.display = 'none';
          }
          hideTooltip();
        });
      });
    });

    // Draw stops on top
    sortedStops.forEach((stop, i) => {
      const [x, y] = project(stop.coords);
      const p = stop.props;

      const circle = document.createElementNS(ns, 'circle');
      circle.setAttribute('cx', x.toFixed(1));
      circle.setAttribute('cy', y.toFixed(1));
      circle.setAttribute('r', '6');
      circle.setAttribute('fill', C_STOP_DEF);
      circle.setAttribute('stroke', C_DEFAULT);
      circle.setAttribute('stroke-width', '2.5');
      circle.style.cursor = 'pointer';

      stopCircles.push(circle);

      if (i < sections.length) sections[i].fromCircle = circle;
      if (i > 0)               sections[i - 1].toCircle = circle;

      circle.addEventListener('mouseenter', e => {
        circle.setAttribute('r', '9');
        circle.setAttribute('fill', C_DEFAULT);
        showTooltip(e, `<strong>${p.stopNum}</strong> &middot; ${escHtml(p.stopName)}`);
      });
      circle.addEventListener('mousemove', positionTooltip);
      circle.addEventListener('mouseleave', () => {
        const isSectionBoundary =
          (i < sections.length && selectedIdx === i) ||
          (i > 0 && selectedIdx === i - 1);
        const isStopSelected = selectedStopIdx === i;
        const isAnySelected  = isSectionBoundary || isStopSelected;
        circle.setAttribute('r', isAnySelected ? '8' : '6');
        circle.setAttribute('fill', isAnySelected ? C_STOP_SEL : C_STOP_DEF);
        circle.setAttribute('stroke', isAnySelected ? C_SELECTED : C_DEFAULT);
        hideTooltip();
      });
      circle.addEventListener('click', () => {
        const wasSelected = selectedStopIdx === i;
        if (_activeClearSelection && _activeClearSelection !== clearSelection) {
          _activeClearSelection();
          _activeClearSelection = null;
        }
        clearSelection();
        if (!wasSelected) {
          styleStopCircle(i, C_STOP_SEL, C_SELECTED, '8');
          selectedStopIdx = i;
          _activeClearSelection = clearSelection;
          _currentInfoSelection = { type: 'stop', data: p, dirKey };
          showStopInfo(p, dirKey);
        } else {
          _activeClearSelection = null;
          _currentInfoSelection = null;
          const panel = document.getElementById('route-info-panel');
          if (panel) panel.style.display = 'none';
        }
        hideTooltip();
      });

      svgEl.appendChild(circle);
    });

  } catch (err) {
    svgEl.innerHTML = '';
    const errText = document.createElementNS(ns, 'text');
    errText.setAttribute('x', '50%');
    errText.setAttribute('y', '50%');
    errText.setAttribute('text-anchor', 'middle');
    errText.setAttribute('fill', '#e3000f');
    errText.setAttribute('font-size', '13');
    errText.setAttribute('font-family', 'sans-serif');
    errText.textContent = `Error: ${err.message}`;
    svgEl.appendChild(errText);
  }
}

// ---- Build timeslot selector HTML (hours 5-23) ----
function buildTimeslotSelector(availableHours, selectedHour, onSelect) {
  const hours = Array.from({ length: 19 }, (_, i) => i + 5); // 5..23
  const btns = hours.map(h => {
    const avail = availableHours.includes(h);
    const active = h === selectedHour ? 'active' : '';
    const disabled = avail ? '' : 'disabled style="opacity:0.35;cursor:not-allowed;"';
    return `<button class="ts-btn ${active}" data-hour="${h}" ${disabled}>${h}</button>`;
  }).join('');

  const wrap = document.createElement('div');
  wrap.className = 'timeslot-selector-wrap';
  wrap.innerHTML = `<span class="timeslot-selector-label">Franja horaria:</span>${btns}`;

  wrap.querySelectorAll('.ts-btn:not([disabled])').forEach(btn => {
    btn.addEventListener('click', () => {
      wrap.querySelectorAll('.ts-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      onSelect(Number(btn.dataset.hour));
    });
  });
  return wrap;
}

// ---- Show stop info panel ----
function showStopInfo(p, dirKey) {
  const panel = document.getElementById('route-info-panel');
  panel.style.display = 'block';

  const stopId   = String(p.stopNum);
  const stopInfo = _plotsInfo?.stopGeneralInfo?.[dirKey]?.[stopId];
  const stopPlotsByHour = _plotsInfo?.stopPlots?.[dirKey]?.[stopId] || {};

  // Build stats box content (will be re-rendered by filter changes)
  function renderStopPanel(filter, selectedTs) {
    let statsHtml = '';
    let plotsHtml = '';

    if (stopInfo) {
      if (filter === 'general') {
        const occPct = stopInfo.Occupation_percentage != null
          ? stopInfo.Occupation_percentage.toFixed(2) + '%' : '—';
        const awaitTime = stopInfo.Mean_await_time_general != null
          ? formatDuration(stopInfo.Mean_await_time_general) : '—';
        const boards_mean = stopInfo.mean_boards != null
          ? Number(stopInfo.mean_boards).toLocaleString('es-ES', { maximumFractionDigits: 2 })
          : '—';
        const unable_boards_mean = stopInfo.unable_boards != null
          ? Number(stopInfo.unable_boards).toLocaleString('es-ES', { maximumFractionDigits: 2 })
          : '—';
        const dropoffs_mean = stopInfo.mean_dropoffs != null
          ? Number(stopInfo.mean_dropoffs).toLocaleString('es-ES', { maximumFractionDigits: 2 })
          : '—';
        statsHtml = `
          <div class="stop-stats-box">
            <div class="ss-item">
              <span class="ss-label">Ocupación media general</span>
              <span class="ss-value">${occPct}</span>
            </div>
            <div class="ss-item">
              <span class="ss-label">Espera media general</span>
              <span class="ss-value">${awaitTime}</span>
            </div>
            <div class="ss-item">
              <span class="ss-label">Media de subida de pasajeros </span>
              <span class="ss-value">${boards_mean}</span>
            </div>
            <div class="ss-item">
              <span class="ss-label">Media de pasajeros que no pudieron subir </span>
              <span class="ss-value">${unable_boards_mean}</span>
            </div>
            <div class="ss-item">
              <span class="ss-label">Media de bajada de pasajeros </span>
              <span class="ss-value">${dropoffs_mean}</span>
            </div>
          </div>`;

        // General filter: show single occupation_per_timeslot_STOPID.png
        const generalPlotUrl = _plotsInfo?.stopPlotsGeneral?.[dirKey]?.[stopId];
        if (generalPlotUrl) {
          plotsHtml = `
            <div class="stop-plots-wrap">
              <div class="stop-plot-dir-label ${dirKey === 'toA' ? 'dir-label-a' : 'dir-label-b'}">
                Ocupación por franja horaria (${dirKey === 'toA' ? '&#8594; ' + _dirNames.toA : '&#8592; ' + _dirNames.toB})
              </div>
              <div class="stop-plot-item plot-expandable" onclick="openImgModal('${generalPlotUrl}')">
                <img src="${generalPlotUrl}" alt="Ocupación por franja" loading="lazy" />
                <div class="plot-expand-hint">&#128269; Clic para ampliar</div>
              </div>
            </div>`;
        }

      } else {
        // Timeslot filter
        const ts = selectedTs;
        const occPct = stopInfo.Occupation_percentage_per_timeslot?.[ts] != null
          ? stopInfo.Occupation_percentage_per_timeslot[ts].toFixed(2) + '%' : '—';
        const awaitTime = stopInfo.Mean_await_time_per_timeslot?.[ts] != null
          ? formatDuration(stopInfo.Mean_await_time_per_timeslot[ts]) : '—';
        const boards_mean = stopInfo.Board_dropoff_per_timeslot?.[ts]?.boards != null
          ? Number(stopInfo.Board_dropoff_per_timeslot[ts].boards).toLocaleString('es-ES', { maximumFractionDigits: 2 })
          : '—';
        const unable_boards_mean = stopInfo.Board_dropoff_per_timeslot?.[ts]?.unable_boards != null
          ? Number(stopInfo.Board_dropoff_per_timeslot[ts].unable_boards).toLocaleString('es-ES', { maximumFractionDigits: 2 })
          : '—';
        const dropoffs_mean = stopInfo.Board_dropoff_per_timeslot?.[ts]?.dropoffs != null
          ? Number(stopInfo.Board_dropoff_per_timeslot[ts].dropoffs).toLocaleString('es-ES', { maximumFractionDigits: 2 })
          : '—';
        statsHtml = `
          <div class="stop-stats-box">
            <div class="ss-item">
              <span class="ss-label">Ocupación franja ${ts}:00</span>
              <span class="ss-value">${occPct}</span>
            </div>
            <div class="ss-item">
              <span class="ss-label">Espera media franja ${ts}:00</span>
              <span class="ss-value">${awaitTime}</span>
            </div>
            <div class="ss-item">
                <span class="ss-label">Media de subida de pasajeros </span>
                <span class="ss-value">${boards_mean}</span>
              </div>
              <div class="ss-item">
                <span class="ss-label">Media de pasajeros que no pudieron subir </span>
                <span class="ss-value">${unable_boards_mean}</span>
              </div>
              <div class="ss-item">
                <span class="ss-label">Media de bajada de pasajeros </span>
                <span class="ss-value">${dropoffs_mean}</span>
              </div>
          </div>`;

        // Show comparison plot for selected timeslot
        const plotUrl = stopPlotsByHour[String(ts)];
        if (plotUrl) {
          plotsHtml = `
            <div class="stop-plots-wrap">
              <div class="stop-plot-dir-label ${dirKey === 'toA' ? 'dir-label-a' : 'dir-label-b'}">
                Comparativa ocupación franja ${ts}:00 (${dirKey === 'toA' ? '&#8594; ' + _dirNames.toA : '&#8592; ' + _dirNames.toB})
              </div>
              <div class="stop-plot-item plot-expandable" onclick="openImgModal('${plotUrl}')">
                <img src="${plotUrl}" alt="Ocupación franja ${ts}" loading="lazy" />
                <div class="plot-expand-hint">&#128269; Clic para ampliar</div>
              </div>
            </div>`;
        }
      }
    }

    const infoBody = panel.querySelector('.stop-info-body');
    if (infoBody) {
      infoBody.innerHTML = statsHtml;
      // Re-attach timeslot selector
      const tsWrap = panel.querySelector('.ts-selector-slot');
      if (tsWrap) tsWrap.innerHTML = '';
    }

    // Full re-render approach (simpler, avoids DOM patching)
    panel.innerHTML = `
      <div class="route-info-header">
        <span>&#9679; Parada ${p.stopNum} &middot; ${escHtml(p.stopName)}</span>
        <button class="route-info-close" onclick="closeInfoPanel()">&#10005;</button>
      </div>
      <div class="route-info-body">
        <div class="route-info-row"><span>Nombre</span><strong>${escHtml(p.stopName)}</strong></div>
        <div class="route-info-row"><span>N&#250;m. parada</span><strong>${p.stopNum}</strong></div>
      </div>
      ${statsHtml}
      ${filter === 'timeslot' ? '<!-- ts-selector -->' : ''}
      ${plotsHtml}
    `;

    // Inject timeslot selector after stats box for timeslot mode
    if (filter === 'timeslot' && stopInfo) {
      const availHours = Object.keys(stopInfo.Occupation_percentage_per_timeslot || {}).map(Number);
      const selector = buildTimeslotSelector(availHours, selectedTs, (newTs) => {
        _routeInfoSelectedTs = newTs;
        renderStopPanel('timeslot', newTs);
      });
      // Insert after the statsBox (before plots)
      const statsBox = panel.querySelector('.stop-stats-box');
      if (statsBox) {
        statsBox.after(selector);
      } else {
        // Insert before plots
        panel.appendChild(selector);
      }
    }
  }

  renderStopPanel(_routeInfoFilter, _routeInfoSelectedTs);
}

// ---- Show section info panel ----
function showSectionInfo(sec, dirKey) {
  const panel = document.getElementById('route-info-panel');
  panel.style.display = 'block';

  const fromId = String(sec.from.props.stopNum);
  const toId   = String(sec.to.props.stopNum);
  const sectionKey = `${fromId}-${toId}`;

  const timesStops = _plotsInfo?.stopGeneralInfo?.[dirKey]?.times_stops || {};
  const sectionData = timesStops[sectionKey];

  const timesByHour = _plotsInfo?.timesPlots?.[dirKey]?.[sectionKey] || {};

  function renderSectionPanel(filter, selectedTs) {
    let statsHtml = '';
    let plotsHtml = '';

    if (sectionData) {
      if (filter === 'general') {
        const genTime = sectionData.general_time != null
          ? formatDuration(sectionData.general_time) : '—';
        statsHtml = `
          <div class="stop-stats-box">
            <div class="ss-item">
              <span class="ss-label">Tiempo de tránsito general</span>
              <span class="ss-value">${genTime}</span>
            </div>
          </div>`;
        // No comparison plot in general mode for sections

      } else {
        const ts = selectedTs;
        const tsTime = sectionData.time_per_timeslot?.[ts] != null
          ? formatDuration(sectionData.time_per_timeslot[ts]) : '—';
        statsHtml = `
          <div class="stop-stats-box">
            <div class="ss-item">
              <span class="ss-label">Tiempo de tránsito franja ${ts}:00</span>
              <span class="ss-value">${tsTime}</span>
            </div>
          </div>`;

        // Show comparison plot for selected timeslot
        const plotUrl = timesByHour[String(ts)];
        if (plotUrl) {
          plotsHtml = `
            <div class="stop-plots-wrap">
              <div class="stop-plot-dir-label ${dirKey === 'toA' ? 'dir-label-a' : 'dir-label-b'}">
                Comparativa tiempo de tránsito franja ${ts}:00
              </div>
              <div class="stop-plot-item plot-expandable" onclick="openImgModal('${plotUrl}')">
                <img src="${plotUrl}" alt="Tiempo tránsito franja ${ts}" loading="lazy" />
                <div class="plot-expand-hint">&#128269; Clic para ampliar</div>
              </div>
            </div>`;
        }
      }
    }

    panel.innerHTML = `
      <div class="route-info-header section-header">
        <span>
          <span class="section-stop-badge">${sec.from.props.stopNum}</span>
          ${escHtml(sec.from.props.stopName)}
          &nbsp;&#8594;&nbsp;
          <span class="section-stop-badge">${sec.to.props.stopNum}</span>
          ${escHtml(sec.to.props.stopName)}
        </span>
        <button class="route-info-close" onclick="closeInfoPanel()">&#10005;</button>
      </div>
      <div class="route-info-body">
        <div class="route-info-row"><span>Parada origen</span><strong>${sec.from.props.stopNum} &middot; ${escHtml(sec.from.props.stopName)}</strong></div>
        <div class="route-info-row"><span>Parada destino</span><strong>${sec.to.props.stopNum} &middot; ${escHtml(sec.to.props.stopName)}</strong></div>
      </div>
      ${sectionData ? statsHtml : '<div class="route-info-hint" style="padding:0.75rem 1rem;">Sin datos de tránsito para este tramo.</div>'}
      ${plotsHtml}
    `;

    if (filter === 'timeslot' && sectionData) {
      const availHours = Object.keys(sectionData.time_per_timeslot || {}).map(Number);
      const selector = buildTimeslotSelector(availHours, selectedTs, (newTs) => {
        _routeInfoSelectedTs = newTs;
        renderSectionPanel('timeslot', newTs);
      });
      const statsBox = panel.querySelector('.stop-stats-box');
      if (statsBox) statsBox.after(selector);
      else panel.appendChild(selector);
    }
  }

  renderSectionPanel(_routeInfoFilter, _routeInfoSelectedTs);
}

// ---- Init ----

// ---- Image modal ----

function openImgModal(url) {
  let overlay = document.getElementById('img-modal-overlay');
  if (!overlay) {
    overlay = document.createElement('div');
    overlay.id = 'img-modal-overlay';
    overlay.className = 'img-modal-overlay';
    overlay.innerHTML = `
      <div class="img-modal-box">
        <button class="img-modal-close" onclick="closeImgModal()">&#10005;</button>
        <img id="img-modal-img" src="" alt="Gráfica ampliada" />
      </div>`;
    overlay.addEventListener('click', e => {
      if (e.target === overlay) closeImgModal();
    });
    document.body.appendChild(overlay);
  }
  document.getElementById('img-modal-img').src = url;
  overlay.classList.add('open');
  document.body.style.overflow = 'hidden';
}

function closeImgModal() {
  const overlay = document.getElementById('img-modal-overlay');
  if (overlay) overlay.classList.remove('open');
  document.body.style.overflow = '';
}

document.addEventListener('keydown', e => {
  if (e.key === 'Escape') closeImgModal();
});

document.addEventListener('DOMContentLoaded', () => {
  const simId = getSimId();

  if (!simId || !simId.match(/^SIMULATION_\d{8}_\d{6}$/)) {
    document.getElementById('loading-state').innerHTML = `
      <div class="empty-icon">&#9888;</div>
      <p>ID de simulación inválido.</p>
      <a href="/" class="btn btn-outline" style="margin-top:1rem;">&#8592; Volver al dashboard</a>
    `;
    return;
  }

  loadDetail(simId);
  initViewToggle();

  document.getElementById('btn-download-log').addEventListener('click', () => {
    window.open(`/data/logs/${simId}/log_result_${simId.replace('SIMULATION_', '')}.log`, '_blank');
  });

  document.getElementById('btn-delete-sim').addEventListener('click', async () => {
    const label = document.getElementById('hero-date').textContent || simId;
    const confirmed = confirm(
      `ATENCIÓN: ACCIÓN IRREVERSIBLE\n\nVas a eliminar la simulación:\n"${label}"\n\nEsto borrará permanentemente TODOS los datos, resultados y logs.\n\n¿Estás seguro de que quieres continuar?`
    );
    if (!confirmed) return;
    try {
      const res = await fetch(`/api/simulations/${simId}`, { method: 'DELETE' });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) { toast(data.error || 'Error al eliminar la simulación', 'error'); return; }
      toast('Simulación eliminada. Redirigiendo...', 'info');
      setTimeout(() => { window.location.href = '/'; }, 1800);
    } catch (err) {
      toast('Error: ' + err.message, 'error');
    }
  });

  const socket = io();
  socket.on('sim_completed', ({ id, title }) => {
    toast(`Simulaci\u00f3n completada: ${title || id}`, 'success');
  });

  socket.on('new_sim_launched', ({ id, title }) => {
    toast(`Nueva simulación creada: ${title || id}`, 'info');
  });

});
