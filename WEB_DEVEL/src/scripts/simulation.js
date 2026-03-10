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

// ---- Render charts ----

function renderCharts(charts) {
  const area = document.getElementById('charts-area');
  const countEl = document.getElementById('charts-count');

  if (!charts || charts.length === 0) {
    area.innerHTML = `
      <div class="empty-state">
        <div class="empty-icon">&#128202;</div>
        <p>No hay gráficas generadas aún.</p>
        <p style="margin-top:0.5rem;font-size:0.85rem;">
          Pulsa <strong>"Generar gráficas"</strong> para ejecutar el script Python de análisis.
        </p>
      </div>`;
    countEl.textContent = '';
    return;
  }

  countEl.textContent = `${charts.length} imagen${charts.length !== 1 ? 'es' : ''}`;
  const grid = document.createElement('div');
  grid.className = 'charts-grid';

  charts.forEach(src => {
    const name = src.split('/').pop().replace(/\.[^/.]+$/, '').replace(/_/g, ' ');
    const wrap = document.createElement('div');
    wrap.className = 'chart-img-wrap';
    wrap.innerHTML = `
      <img src="${src}" alt="${name}" loading="lazy" />
      <div class="chart-name">${name}</div>
    `;
    grid.appendChild(wrap);
  });

  area.innerHTML = '';
  area.appendChild(grid);
}

// ---- Render time slot table ----

function renderTimeSlots(byTimeSlot) {
  const container = document.getElementById('timeslot-table');
  const slots = Object.entries(byTimeSlot).sort((a, b) => Number(a[0]) - Number(b[0]));

  if (slots.length === 0) {
    container.innerHTML = '<p style="color:var(--emt-gray-600);font-size:0.85rem;">Sin datos de franjas horarias.</p>';
    return;
  }

  const maxBoards = Math.max(...slots.map(([, v]) => v.boards), 1);

  const table = document.createElement('table');
  table.style.cssText = 'width:100%;border-collapse:collapse;';

  table.innerHTML = `
    <thead>
      <tr style="text-align:left;border-bottom:2px solid var(--emt-red);">
        <th style="padding:0.4rem 0.5rem;font-size:0.75rem;color:var(--emt-gray-600);">Franja</th>
        <th style="padding:0.4rem 0.5rem;font-size:0.75rem;color:var(--emt-gray-600);">Boards</th>
        <th style="padding:0.4rem 0.5rem;font-size:0.75rem;color:var(--emt-gray-600);">Dropoffs</th>
        <th style="padding:0.4rem 0.5rem;font-size:0.75rem;color:var(--emt-gray-600);min-width:80px;">Actividad</th>
      </tr>
    </thead>
    <tbody>
      ${slots.map(([slot, v]) => {
        const pct = Math.round((v.boards / maxBoards) * 100);
        return `
          <tr style="border-bottom:1px solid var(--emt-gray-200);">
            <td style="padding:0.4rem 0.5rem;font-weight:600;">${slot}</td>
            <td style="padding:0.4rem 0.5rem;">${formatNum(Math.round(v.boards))}</td>
            <td style="padding:0.4rem 0.5rem;">${formatNum(Math.round(v.dropoffs))}</td>
            <td style="padding:0.4rem 0.5rem;">
              <div style="background:var(--emt-gray-200);border-radius:3px;height:8px;overflow:hidden;">
                <div style="background:var(--emt-red);height:100%;width:${pct}%;border-radius:3px;"></div>
              </div>
            </td>
          </tr>`;
      }).join('')}
    </tbody>
  `;

  container.innerHTML = '';
  container.appendChild(table);
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
    document.getElementById('hero-date').textContent = detail.datetime || detail.id;
    document.getElementById('hero-subtitle').textContent =
      `${formatNum(detail.runCount)} réplicas · ${detail.charts?.length || 0} gráficas`;
    document.title = `${detail.id} — EMT Dashboard`;

    // Stats bar
    document.getElementById('ds-runs').textContent = formatNum(detail.runCount);
    if (stats) {
      document.getElementById('ds-boards').textContent = formatNum(Math.round(stats.totalBoards));
      document.getElementById('ds-dropoffs').textContent = formatNum(Math.round(stats.totalDropoffs));
      document.getElementById('ds-occ').textContent = formatNum(stats.avgPassengers);

      // Direction
      document.getElementById('dir-a-boards').textContent = formatNum(Math.round(stats.byDirection?.toA?.boards || 0));
      document.getElementById('dir-b-boards').textContent = formatNum(Math.round(stats.byDirection?.toB?.boards || 0));
      document.getElementById('dir-a-dropoffs').textContent = formatNum(Math.round(stats.byDirection?.toA?.dropoffs || 0));
      document.getElementById('dir-b-dropoffs').textContent = formatNum(Math.round(stats.byDirection?.toB?.dropoffs || 0));

      // Time slots
      renderTimeSlots(stats.byTimeSlot || {});
    }

    // Charts
    renderCharts(detail.charts || []);

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

// ---- Generate charts ----

async function generateCharts(simId) {
  const btn = document.getElementById('btn-gen-charts');
  btn.disabled = true;
  btn.textContent = '⏳ Generando...';
  toast('Generando gráficas con Python...', 'info');

  try {
    const res = await fetch(`/api/simulations/${simId}/generate-charts`, { method: 'POST' });
    const data = await res.json();
    toast(data.message || 'Gráficas generadas', res.ok ? 'success' : 'error');
    if (res.ok) {
      // Reload detail to show new charts
      const detailRes = await fetch(`/api/simulations/${simId}`);
      const detail = await detailRes.json();
      renderCharts(detail.charts || []);
    }
  } catch (err) {
    toast('Error al generar gráficas: ' + err.message, 'error');
  } finally {
    btn.disabled = false;
    btn.innerHTML = '&#128202; Generar gráficas';
  }
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

  document.getElementById('btn-gen-charts').addEventListener('click', () => generateCharts(simId));

  document.getElementById('btn-download-log').addEventListener('click', () => {
    window.open(`/data/logs/${simId}/log_result_${simId.replace('SIMULATION_', '')}.log`, '_blank');
  });
});
