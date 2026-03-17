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

function getSimId() {
  // URL is /simulation/SIMULATION_YYYYMMDD_HHMMSS
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
    const [detailRes, statsRes] = await Promise.all([
      fetch(`/api/simulations/${simId}`),
      fetch(`/api/simulations/${simId}/stats`)
    ]);

    if (!detailRes.ok) throw new Error(`Simulación no encontrada (HTTP ${detailRes.status})`);
    const detail = await detailRes.json();
    const stats = statsRes.ok ? await statsRes.json() : null;

    // Hero
    document.getElementById('hero-id').textContent = detail.id;
    document.getElementById('hero-date').textContent = detail.title || detail.datetime || detail.id;
    document.getElementById('hero-subtitle').textContent = detail.description
      ? `${detail.description} · ${formatNum(detail.runCount)} réplicas`
      : `${detail.datetime || ''} · ${formatNum(detail.runCount)} réplicas`;
    document.title = `${detail.title || detail.id} — EMT Dashboard`;

    // Stats bar
    document.getElementById('ds-runs').textContent = formatNum(detail.runCount);
    if (stats) {
      document.getElementById('ds-boards').textContent = formatNum(Math.round(stats.totalBoards));
      document.getElementById('ds-dropoffs').textContent = formatNum(Math.round(stats.totalDropoffs));
      document.getElementById('ds-occ').textContent = formatNum(stats.avgPassengers);

    }

    // Route map
    loadGeodata(simId);

    // Plots info (occupation stats, stop/bus plots) — non-blocking
    loadPlotsInfo(simId);

    // Log
    const logEl = document.getElementById('log-viewer');
    if (detail.logContent) {
      logEl.innerHTML = colorizeLog(detail.logContent);
    } else {
      logEl.textContent = 'No se encontró archivo de log.';
    }

    // Show content
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
  document.getElementById('occ-general').textContent = fmt(s.Occupation);
  document.getElementById('occ-toA').textContent     = fmt(s.Occupation_toA);
  document.getElementById('occ-toB').textContent     = fmt(s.Occupation_toB);
}

// ---- View toggle (Route / Bus) ----

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

let _busViewRendered = false;

function renderBusView() {
  if (_busViewRendered) return;
  _busViewRendered = true;

  const container = document.getElementById('bus-view-container');

  if (!_plotsInfo?.busSchedule || Object.keys(_plotsInfo.busSchedule).length === 0) {
    container.innerHTML = '<div class="empty-state"><p>No hay datos de autobuses disponibles.</p></div>';
    return;
  }

  const { busSchedule, busMetrics, busPlots } = _plotsInfo;
  const busIds = Object.keys(busSchedule).sort((a, b) => Number(a) - Number(b));

  const pillsHtml = busIds.map(id =>
    `<button class="bus-pill" data-bus="${id}">${id}</button>`
  ).join('');

  container.innerHTML = `
    <div class="bus-selector-section">
      <div class="bus-selector-label">Selecciona un autobús:</div>
      <div class="bus-pills" id="bus-pills">${pillsHtml}</div>
    </div>
    <div id="bus-detail-panel" style="display:none;"></div>
  `;

  container.querySelectorAll('.bus-pill').forEach(btn => {
    btn.addEventListener('click', () => {
      container.querySelectorAll('.bus-pill').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      renderBusDetail(btn.dataset.bus, busSchedule, busMetrics, busPlots);
    });
  });
}

function normalizeDir(dir) {
  if (!dir) return 'toA';
  return (dir === 'to_A' || dir === 'toA') ? 'toA' : 'toB';
}

function renderBusDetail(busId, busSchedule, busMetrics, busPlots) {
  const panel  = document.getElementById('bus-detail-panel');
  panel.style.display = '';

  const schedule = busSchedule[busId] || [];
  const metrics  = busMetrics?.[busId]  || {};
  const plots    = busPlots?.[busId]    || { toA: [], toB: [] };

  // Build trip objects, tracking per-direction index for PNG matching
  const dirCount = { toA: 0, toB: 0 };
  const trips = schedule.map(([stopId, time], globalIdx) => {
    const key = `${stopId}-${time}`;
    const m   = metrics[key];
    const dir = normalizeDir(m?.Direction);
    return { stopId, time, key, metrics: m, direction: dir, dirIndex: dirCount[dir]++, globalIdx };
  });

  const rows = trips.map((t, i) => {
    const m        = t.metrics;
    const dirLabel = t.direction === 'toA' ? '&#8594; Dir A' : '&#8592; Dir B';
    const dirClass = t.direction === 'toA' ? 'dir-badge-a' : 'dir-badge-b';
    const occ      = m?.Mean_Occupation_Percentage != null ? m.Mean_Occupation_Percentage.toFixed(1) + '%' : '—';
    const tTime    = m?.Mean_time_of_trip != null ? m.Mean_time_of_trip.toFixed(1) + ' min' : '—';
    return `
      <tr class="trip-row" data-idx="${i}">
        <td class="trip-num">${i}</td>
        <td><span class="trip-stop">${t.stopId}</span></td>
        <td class="trip-time-val">${t.time}</td>
        <td><span class="dir-badge ${dirClass}">${dirLabel}</span></td>
        <td class="trip-occ">${occ}</td>
        <td>${tTime}</td>
      </tr>`;
  }).join('');

  panel.innerHTML = `
    <div class="bus-detail-grid">
      <div class="bus-trips-section">
        <div class="bus-section-title">Autobús ${busId} &mdash; ${trips.length} viaje${trips.length !== 1 ? 's' : ''}</div>
        <table class="trip-table">
          <thead>
            <tr>
              <th>#</th><th>Parada inicio</th><th>Hora</th>
              <th>Dirección</th><th>Ocupación media</th><th>T. viaje</th>
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
      renderTripDetail(trips[Number(row.dataset.idx)], plots);
    });
  });
}

function renderTripDetail(trip, plots) {
  const panel = document.getElementById('trip-detail-panel');
  const m     = trip.metrics;
  const fmt   = (v, suf = '') => (v != null && !isNaN(v)) ? Number(v).toFixed(2) + suf : '—';

  const dirLabel = trip.direction === 'toA' ? '&#8594; Dirección A' : '&#8592; Dirección B';
  const dirClass = trip.direction === 'toA' ? 'dir-badge-a' : 'dir-badge-b';

  const imgUrl = (plots[trip.direction] || [])[trip.dirIndex] || null;

  panel.innerHTML = `
    <div class="trip-detail-header">
      <span class="dir-badge ${dirClass}">${dirLabel}</span>
      <span class="trip-detail-id">Viaje ${trip.globalIdx} &middot; ${trip.stopId} · ${trip.time}</span>
    </div>
    <div class="trip-metrics-grid">
      <div class="trip-metric-card">
        <div class="trip-metric-label">Ocupación media</div>
        <div class="trip-metric-value">${fmt(m?.Mean_Occupation_Percentage, '%')}</div>
      </div>
      <div class="trip-metric-card">
        <div class="trip-metric-label">Tiempo de viaje</div>
        <div class="trip-metric-value">${fmt(m?.Mean_time_of_trip, ' min')}</div>
      </div>
      <div class="trip-metric-card">
        <div class="trip-metric-label">% simulaciones con retraso</div>
        <div class="trip-metric-value">${fmt(m?.Percentage_sims_delay_departure, '%')}</div>
      </div>
      <div class="trip-metric-card">
        <div class="trip-metric-label">Retraso medio</div>
        <div class="trip-metric-value">${fmt(m?.Mean_Minutes_departure_delay, ' min')}</div>
      </div>
    </div>
    ${imgUrl
      ? `<div class="trip-plot-wrap">
           <div class="trip-plot-label">Ocupación media por parada</div>
           <img src="${imgUrl}" alt="Ocupación por parada" class="trip-plot-img" loading="lazy" />
         </div>`
      : `<div class="route-info-hint" style="padding:0.5rem 0;">Sin gráfica disponible para este viaje.</div>`
    }
  `;
}

// Reference to the active map's clearSelection — set whenever a selection is made
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
  _svgTooltip.style.top = (e.clientY - 10) + 'px';
}

function hideTooltip() {
  _svgTooltip.style.display = 'none';
}

async function loadGeodata(simId) {
  const container = document.getElementById('map-container');
  try {
    const res = await fetch(`/api/simulations/${simId}/geodata`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    if (!data.experiments || data.experiments.length === 0) {
      container.innerHTML = '<p style="padding:1.5rem;color:var(--emt-gray-600);">No se encontraron datos geoespaciales para esta simulación.</p>';
      return;
    }

    const expTabsEl = document.getElementById('exp-tabs');
    if (data.experiments.length > 1) {
      data.experiments.forEach((exp, i) => {
        const btn = document.createElement('button');
        btn.className = `btn btn-sm ${i === 0 ? 'btn-primary' : 'btn-outline'}`;
        btn.textContent = exp.expId;
        btn.addEventListener('click', () => {
          expTabsEl.querySelectorAll('button').forEach(b => b.className = 'btn btn-sm btn-outline');
          btn.className = 'btn btn-sm btn-primary';
          renderDirectionMaps(exp);
        });
        expTabsEl.appendChild(btn);
      });
    }

    renderDirectionMaps(data.experiments[0]);

  } catch (err) {
    container.innerHTML = `<p style="padding:1.5rem;color:var(--emt-red);">Error al cargar geodata: ${escHtml(err.message)}</p>`;
  }
}

function renderDirectionMaps(exp) {
  const container = document.getElementById('map-container');
  container.innerHTML = `
    <div class="direction-maps">
      <div class="direction-map-panel">
        <div class="direction-map-label dir-label-a">&#8594; Dirección A</div>
        <svg id="svg-toA" class="route-svg"></svg>
      </div>
      <div class="direction-map-panel">
        <div class="direction-map-label dir-label-b">&#8592; Dirección B</div>
        <svg id="svg-toB" class="route-svg"></svg>
      </div>
    </div>
    <div id="route-info-panel" class="route-info-panel" style="display:none;"></div>
  `;
  buildSvgMap(document.getElementById('svg-toA'), exp.toA);
  buildSvgMap(document.getElementById('svg-toB'), exp.toB);
}

async function buildSvgMap(svgEl, dirData) {
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

    // Sort stops by cumulative distance
    const sortedStops = stopsGeo.features
      .filter(f => f.geometry.type === 'Point')
      .map(f => ({ props: f.properties, coords: f.geometry.coordinates }))
      .sort((a, b) => a.props.distance - b.props.distance);

    // Build one section per consecutive stop pair
    // Each section: { from, to, visPaths[], hitPaths[], fromCircle, toCircle }
    const sections = sortedStops.slice(0, -1).map((from, i) => ({
      from,
      to: sortedStops[i + 1],
      visPaths: [],
      hitPaths: [],
      fromCircle: null,
      toCircle: null,
    }));

    // Assign a route feature to the section whose [from.distance, to.distance) it falls into.
    // Features before the first stop go to section 0; after the last stop go to the last section.
    function assignSection(dist) {
      for (let i = 0; i < sections.length; i++) {
        if (dist < sections[i].to.props.distance) return i;
      }
      return sections.length - 1;
    }

    // Collect all coords for bounding box
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
    const scale = Math.min(scaleX, scaleY);

    const drawW = rangeX * scale;
    const drawH = rangeY * scale;
    const offX = PAD + (W - 2 * PAD - drawW) / 2;
    const offY = PAD + (H - 2 * PAD - drawH) / 2;

    const project = ([lng, lat]) => [
      offX + (lng - minLng) * scale,
      offY + drawH - (lat - minLat) * scale,
    ];

    const C_DEFAULT  = '#0865d6';
    const C_HOVER    = '#0c97e8';
    const C_SELECTED = '#f59e0b';
    const C_STOP_DEF = '#ffffff';
    const C_STOP_SEL = '#f59e0b';

    let selectedIdx     = -1;  // selected section index (-1 = none)
    let selectedStopIdx = -1;  // selected stop index (-1 = none)
    const stopCircles   = [];  // indexed parallel to sortedStops

    // Helpers to style all paths/circles in a section
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

    // --- Draw route paths grouped by section ---
    for (const f of routeGeo.features) {
      const sIdx = assignSection(f.properties.distance);
      const rings = f.geometry.type === 'MultiLineString'
        ? f.geometry.coordinates : [f.geometry.coordinates];

      for (const ring of rings) {
        const pts = ring.map(project);
        const d = 'M ' + pts.map(([x, y]) => `${x.toFixed(1)},${y.toFixed(1)}`).join(' L ');

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

    // Attach shared hover + click to all hit paths in each section
    sections.forEach((sec, sIdx) => {
      const tooltipHtml = () =>
        `<strong>${sec.from.props.stopNum}</strong> ${escHtml(sec.from.props.stopName)}`
        + `&nbsp;&#8594;&nbsp;`
        + `<strong>${sec.to.props.stopNum}</strong> ${escHtml(sec.to.props.stopName)}`;

      sec.hitPaths.forEach(hit => {
        hit.addEventListener('mouseenter', e => {
          if (selectedIdx !== sIdx) {
            styleSection(sIdx, C_HOVER, '5');
          }
          showTooltip(e, tooltipHtml());
        });
        hit.addEventListener('mousemove', positionTooltip);
        hit.addEventListener('mouseleave', () => {
          if (selectedIdx !== sIdx) {
            styleSection(sIdx, C_DEFAULT, '3');
          }
          hideTooltip();
        });
        hit.addEventListener('click', () => {
          const wasSelected = selectedIdx === sIdx;
          // Clear selection from the other map if it's active
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
            showSectionInfo(sec);
          } else {
            _activeClearSelection = null;
            const panel = document.getElementById('route-info-panel');
            if (panel) panel.style.display = 'none';
          }
          hideTooltip();
        });
      });
    });

    // --- Draw stops on top (so they sit above route lines) ---
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

      // Register circle as boundary of adjacent sections
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
        // Clear selection from the other map if it's active
        if (_activeClearSelection && _activeClearSelection !== clearSelection) {
          _activeClearSelection();
          _activeClearSelection = null;
        }
        clearSelection();
        if (!wasSelected) {
          styleStopCircle(i, C_STOP_SEL, C_SELECTED, '8');
          selectedStopIdx = i;
          _activeClearSelection = clearSelection;
          showStopInfo(p);
        } else {
          _activeClearSelection = null;
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

function showStopInfo(p) {
  const panel = document.getElementById('route-info-panel');
  panel.style.display = 'block';

  const stopId = String(p.stopNum);
  const toAUrl = _plotsInfo?.stopPlots?.toA?.[stopId];
  const toBUrl = _plotsInfo?.stopPlots?.toB?.[stopId];

  const plotHtml = (toAUrl || toBUrl) ? `
    <div class="stop-plots-wrap">
      ${toAUrl ? `<div class="stop-plot-item">
        <div class="stop-plot-dir-label dir-label-a">&#8594; Dirección A</div>
        <img src="${toAUrl}" alt="Ocupación Dir. A" loading="lazy" />
      </div>` : ''}
      ${toBUrl ? `<div class="stop-plot-item">
        <div class="stop-plot-dir-label dir-label-b">&#8592; Dirección B</div>
        <img src="${toBUrl}" alt="Ocupación Dir. B" loading="lazy" />
      </div>` : ''}
    </div>` : `<div class="route-info-hint" style="padding:0.6rem 1rem;">Sin gráfica disponible para esta parada.</div>`;

  panel.innerHTML = `
    <div class="route-info-header">
      <span>&#9679; Parada ${p.stopNum} &middot; ${escHtml(p.stopName)}</span>
      <button class="route-info-close" onclick="closeInfoPanel()">&#10005;</button>
    </div>
    <div class="route-info-body">
      <div class="route-info-row"><span>Nombre</span><strong>${escHtml(p.stopName)}</strong></div>
      <div class="route-info-row"><span>N&#250;m. parada</span><strong>${p.stopNum}</strong></div>
      <div class="route-info-row"><span>Distancia desde origen</span><strong>${p.distance ?? '—'} m</strong></div>
    </div>
    ${plotHtml}
  `;
}

function showSectionInfo(sec) {
  const panel = document.getElementById('route-info-panel');
  panel.style.display = 'block';
  const dist = (sec.to.props.distance - sec.from.props.distance).toFixed(0);
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
      <div class="route-info-row"><span>Distancia del tramo</span><strong>${dist} m</strong></div>
      <div class="route-info-hint">Tiempo de tr&#225;nsito entre paradas — pr&#243;ximamente</div>
    </div>
  `;
}

// ---- Init ----

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
});
