// ---- Utilities ----

function toast(msg, type = 'info') {
  const container = document.getElementById('toast-container');
  const el = document.createElement('div');
  el.className = `toast ${type}`;
  el.textContent = msg;
  container.appendChild(el);
  setTimeout(() => el.remove(), 4000);
}

const fmt = I18N.fmt;

// Internal status values (sent by the server, always in Spanish)
const STATUS_ERROR    = 'Error';
const STATUS_DONE     = 'Completada';
const STATUS_QUEUED   = 'En cola';
const STATUS_PREPARED = 'Preparada';
const STATUS_RUNNING  = 'En progreso';
const STATUS_WAITING  = 'Esperando Gr\u00e1ficas';

// Status -> filter key, label, symbol. The symbol always accompanies the colour.
const STATUS_INFO = {
  [STATUS_DONE]:     { key: 'done',     label: 'Completada',          symbol: '\u2713', tone: 'ok' },
  [STATUS_ERROR]:    { key: 'failed',   label: 'Fallida',             symbol: '\u2715', tone: 'fail' },
  [STATUS_RUNNING]:  { key: 'running',  label: 'En curso',            symbol: '\u25CF', tone: 'run' },
  [STATUS_WAITING]:  { key: 'running',  label: 'Generando gráficas',  symbol: '\u25CF', tone: 'run' },
  [STATUS_QUEUED]:   { key: 'queued',   label: 'En cola',             symbol: '\u25D4', tone: 'idle' },
  [STATUS_PREPARED]: { key: 'prepared', label: 'Preparada',           symbol: '\u25CB', tone: 'idle' },
};
const statusInfo = s => STATUS_INFO[s] || STATUS_INFO[STATUS_RUNNING];

// model key -> "model" dimension, independent of the engine
const MODEL_KIND = {
  with_agents:    'agents',
  without_agents: 'aggregate',
  // The C engine keeps passengers as arrays of creation times per stop (no
  // passenger agents), so it implements the aggregate model.
  c_engine:       'aggregate',
};
const MODEL_LABEL = { agents: 'Con agentes pasajero', aggregate: 'Agregado' };
const ENGINE_LABEL = { gama: 'GAMA', c: 'C' };

function escHtml(str) {
  return String(str ?? '')
    .replace(/&/g, '&amp;').replace(/</g, '&lt;')
    .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

// "FASE: mensaje" for the first recorded failure of a simulation
function errorSummary(error) {
  if (!error) return '';
  return `${error.phase}: ${error.message}`;
}

// ---- State ----

let SIMS = [];                                // as returned by /api/simulations
const view = { q: '', engine: '', model: '', status: '', sort: 'date', dir: 'desc' };

const modelKind = s => MODEL_KIND[s.model] || 'aggregate';   // absent key = default model
const nameOf = s => s.title || '';

const SORTERS = {
  name:     (a, b) => nameOf(a).localeCompare(nameOf(b), I18N.locale, { sensitivity: 'base' }),
  date:     (a, b) => a.id.localeCompare(b.id),
  engine:   (a, b) => a.engine.localeCompare(b.engine),
  model:    (a, b) => modelKind(a).localeCompare(modelKind(b)),
  replicas: (a, b) => (a.runCount || 0) - (b.runCount || 0),
  status:   (a, b) => statusInfo(a.status).label.localeCompare(statusInfo(b.status).label),
};

function visibleSims() {
  const q = view.q.trim().toLowerCase();
  const rows = SIMS.filter(s =>
    (!q || `${s.title || ''} ${s.description || ''}`.toLowerCase().includes(q)) &&
    (!view.engine || s.engine === view.engine) &&
    (!view.model || modelKind(s) === view.model) &&
    (!view.status || statusInfo(s.status).key === view.status));
  const sign = view.dir === 'asc' ? 1 : -1;
  return rows.sort((a, b) => sign * SORTERS[view.sort](a, b) || b.id.localeCompare(a.id));
}

// Settings that differ between runs (only keys present in each run's description.txt)
function varyingParams() {
  const defs = [
    { label: 'Ejecución', value: s => (s.exclusive ? 'Exclusiva' : 'Compartida'), present: s => s.seed != null },
    { label: 'Semilla',   value: s => s.seed,                                      present: s => s.seed != null },
  ];
  return defs.filter(d => new Set(SIMS.filter(d.present).map(d.value)).size > 1);
}

// ---- Summary line ----

function renderSummary() {
  const el = document.getElementById('list-summary');
  const n = SIMS.length;
  if (!n) { el.textContent = ''; return; }
  const withCharts = SIMS.filter(s => s.hasCharts).length;
  const failed = SIMS.filter(s => s.status === STATUS_ERROR).length;
  const running = SIMS.filter(s => statusInfo(s.status).key === 'running').length;
  const latest = SIMS.reduce((m, s) => (s.id > m.id ? s : m), SIMS[0]);

  const parts = [
    `<span>${escHtml(t(n === 1 ? '{n} ejecución' : '{n} ejecuciones', { n: fmt.int(n) }))}</span>`,
    `<span>${escHtml(t('{n} con gráficas', { n: fmt.int(withCharts) }))}</span>`,
  ];
  const link = (key, text) => `<a href="#" class="summary-link" data-filter-status="${key}">${escHtml(text)}</a>`;
  if (failed)  parts.push(link('failed',  t(failed === 1 ? '{n} fallida' : '{n} fallidas', { n: fmt.int(failed) })));
  if (running) parts.push(link('running', t('{n} en curso', { n: fmt.int(running) })));
  parts.push(`<span>${escHtml(t('última el {date}', { date: fmt.date(latest.datetime) }))}</span>`);
  el.innerHTML = parts.join('<span class="sep" aria-hidden="true">\u00b7</span>');

  el.querySelectorAll('[data-filter-status]').forEach(a => a.addEventListener('click', e => {
    e.preventDefault();
    view.status = a.dataset.filterStatus;
    document.getElementById('filter-status').value = view.status;
    renderTable();
  }));
}

// ---- Table ----

const COLUMNS = [
  { id: 'name',     label: 'Nombre',     sort: true },
  { id: 'date',     label: 'Fecha',      sort: true },
  { id: 'engine',   label: 'Motor',      sort: true },
  { id: 'model',    label: 'Modelo',     sort: true },
  { id: 'replicas', label: 'Réplicas',   sort: true, num: true },
  { id: 'params',   label: 'Parámetros', sort: false },
  { id: 'status',   label: 'Estado',     sort: true },
  { id: 'actions',  label: 'Acciones',   sort: false, hidden: true },
];

function statusCellHtml(sim) {
  const info = statusInfo(sim.status);
  let text = t(info.label);
  if (sim.status === STATUS_QUEUED && sim.position) text += ` (#${sim.position})`;
  if (sim.status === STATUS_RUNNING && sim.percentage != null) text += ` ${fmt.pct(sim.percentage, 0)}`;
  const reason = sim.status === STATUS_ERROR ? errorSummary(sim.error) : '';
  return `
    <span class="status status-${info.tone}">
      <span class="status-symbol" aria-hidden="true">${info.symbol}</span>${escHtml(text)}
    </span>
    ${reason ? `<div class="status-reason" title="${escHtml(reason)}">${escHtml(reason)}</div>` : ''}`;
}

function rowHtml(sim, params) {
  const name = sim.title ? escHtml(sim.title) : `<span class="untitled">${escHtml(sim.id)}</span>`;
  const desc = sim.description ? `<div class="row-desc" title="${escHtml(sim.description)}">${escHtml(sim.description)}</div>` : '';
  const paramsHtml = params.map(p => {
    const v = p.present(sim) ? p.value(sim) : null;
    return `<div class="param"><span class="param-label">${escHtml(t(p.label))}</span> <span class="param-value">${v == null ? '\u2014' : escHtml(t(String(v)))}</span></div>`;
  }).join('');
  const label = sim.title || sim.id;
  return `
    <tr class="sim-row" data-sim-id="${escHtml(sim.id)}">
      <td class="col-name">
        <a class="row-title" href="/simulation/${escHtml(sim.id)}">${name}</a>
        ${desc}
      </td>
      <td class="col-date">${escHtml(fmt.dateTime(sim.datetime))}</td>
      <td class="col-engine">${escHtml(ENGINE_LABEL[sim.engine] || sim.engine)}</td>
      <td class="col-model">${escHtml(t(MODEL_LABEL[modelKind(sim)]))}</td>
      <td class="col-replicas num" data-cell="replicas">${escHtml(fmt.int(sim.runCount))}</td>
      ${params.length ? `<td class="col-params">${paramsHtml}</td>` : ''}
      <td class="col-status" data-cell="status">${statusCellHtml(sim)}</td>
      <td class="col-actions">
        <button type="button" class="row-menu-btn" aria-haspopup="menu" aria-expanded="false"
                aria-label="${escHtml(t('Acciones de {name}', { name: label }))}" data-menu-for="${escHtml(sim.id)}">\u22ef</button>
      </td>
    </tr>`;
}

function renderTable() {
  const container = document.getElementById('sim-container');
  closeRowMenu();
  if (SIMS.length === 0) {
    container.innerHTML = `
      <div class="empty-state">
        <p class="empty-title">${t('No se han encontrado simulaciones.')}</p>
        <p>${t('Lanza una nueva simulación con el botón de arriba.')}</p>
      </div>`;
    return;
  }
  const params = varyingParams();
  const rows = visibleSims();
  const cols = COLUMNS.filter(c => c.id !== 'params' || params.length);

  const head = cols.map(c => {
    const label = t(c.label);
    const cls = `col-${c.id}${c.num ? ' num' : ''}`;
    if (!c.sort) return `<th scope="col" class="${cls}">${c.hidden ? `<span class="visually-hidden">${escHtml(label)}</span>` : escHtml(label)}</th>`;
    const active = view.sort === c.id;
    const aria = active ? (view.dir === 'asc' ? 'ascending' : 'descending') : 'none';
    const arrow = active ? (view.dir === 'asc' ? '\u2191' : '\u2193') : '';
    return `<th scope="col" class="${cls}" aria-sort="${aria}">
      <button type="button" class="sort-btn" data-sort="${c.id}">${escHtml(label)}<span class="sort-arrow" aria-hidden="true">${arrow}</span></button></th>`;
  }).join('');

  const body = rows.length
    ? rows.map(s => rowHtml(s, params)).join('')
    : `<tr><td class="no-match" colspan="${cols.length}">${escHtml(t('Ninguna ejecución coincide con los filtros.'))}</td></tr>`;

  container.innerHTML = `
    <div class="table-wrap">
      <table class="sim-table" id="sim-table">
        <caption class="visually-hidden">${escHtml(t('Simulaciones'))}</caption>
        <thead><tr>${head}</tr></thead>
        <tbody>${body}</tbody>
      </table>
    </div>
    <p class="result-count" aria-live="polite">${escHtml(t('Mostrando {n} de {total}', { n: fmt.int(rows.length), total: fmt.int(SIMS.length) }))}</p>`;

  container.querySelectorAll('[data-sort]').forEach(b => b.addEventListener('click', () => {
    const id = b.dataset.sort;
    if (view.sort === id) view.dir = view.dir === 'asc' ? 'desc' : 'asc';
    else { view.sort = id; view.dir = id === 'date' || id === 'replicas' ? 'desc' : 'asc'; }
    renderTable();
    container.querySelector(`[data-sort="${id}"]`)?.focus();
  }));
  container.querySelectorAll('.sim-row').forEach(tr => {
    tr.addEventListener('click', e => {
      if (e.target.closest('a, button')) return;
      window.location.href = `/simulation/${tr.dataset.simId}`;
    });
  });
  container.querySelectorAll('[data-menu-for]').forEach(b => b.addEventListener('click', e => {
    e.stopPropagation();
    toggleRowMenu(b);
  }));
}

// ---- Row menu (delete) ----

let _openMenu = null;

function closeRowMenu() {
  if (!_openMenu) return;
  _openMenu.menu.remove();
  _openMenu.btn.setAttribute('aria-expanded', 'false');
  _openMenu = null;
}

function toggleRowMenu(btn) {
  const same = _openMenu && _openMenu.btn === btn;
  closeRowMenu();
  if (same) return;
  const sim = SIMS.find(s => s.id === btn.dataset.menuFor);
  if (!sim) return;
  const menu = document.createElement('div');
  menu.className = 'row-menu';
  menu.setAttribute('role', 'menu');
  menu.innerHTML = `<button type="button" role="menuitem" class="row-menu-item danger">${escHtml(t('Eliminar simulación'))}</button>`;
  document.body.appendChild(menu);
  const r = btn.getBoundingClientRect();
  menu.style.top = `${r.bottom + window.scrollY + 4}px`;
  menu.style.left = `${Math.max(8, r.right + window.scrollX - menu.offsetWidth)}px`;
  btn.setAttribute('aria-expanded', 'true');
  _openMenu = { btn, menu };
  const item = menu.querySelector('.row-menu-item');
  item.focus();
  item.addEventListener('click', () => {
    closeRowMenu();
    handleDeleteSim(sim.id, sim.title || sim.id);
  });
}

document.addEventListener('click', e => {
  if (_openMenu && !_openMenu.menu.contains(e.target)) closeRowMenu();
});
document.addEventListener('keydown', e => {
  if (e.key === 'Escape' && _openMenu) { const b = _openMenu.btn; closeRowMenu(); b.focus(); }
});

// ---- Delete simulation ----

async function handleDeleteSim(simId, label) {
  const confirmed = confirm(
    t('ATENCIÓN: ACCIÓN IRREVERSIBLE\n\nVas a eliminar la simulación:\n"{label}"\n\nEsto borrará permanentemente TODOS los datos, resultados y logs.\n\n¿Estás seguro de que quieres continuar?', { label })
  );
  if (!confirmed) return;
  try {
    const res = await fetch(`/api/simulations/${simId}`, { method: 'DELETE' });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) { toast(data.error || t('Error al eliminar la simulación'), 'error'); return; }
    toast(t('Simulación "{label}" eliminada', { label }), 'info');
    loadSimulations();
  } catch (err) {
    toast('Error: ' + err.message, 'error');
  }
}

// ---- Load simulations ----

async function loadSimulations() {
  const container = document.getElementById('sim-container');
  try {
    const res = await fetch('/api/simulations');
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    SIMS = await res.json();
    renderSummary();
    renderTable();
  } catch (err) {
    container.innerHTML = `
      <div class="empty-state">
        <p class="empty-title">${t('Error al cargar las simulaciones.')}</p>
        <p class="error-detail">${escHtml(err.message)}</p>
      </div>`;
    toast(t('Error al conectar con el servidor'), 'error');
  }
}

// ---- Generate simulation modal ----
function openModal() {
  document.getElementById('modal-generate').classList.add('open');
  document.getElementById('btn-modal-confirm').focus();
}

function closeModal() {
  document.getElementById('modal-generate').classList.remove('open');
}

async function triggerGenerate() {
  closeModal();
  toast(t('Preparando directorio de simulación...'), 'info');
  try {
    const res = await fetch('/api/simulations/prepare', { method: 'POST' });
    const data = await res.json();
    if (!res.ok) {
      toast(data.error || t('Error al preparar la simulación'), 'error');
      return;
    }
    toast(t('Directorio creado. Abriendo configuración...'), 'success');
    setTimeout(() => {
      window.location.href = `/config/${data.simId}`;
    }, 800);
  } catch (err) {
    toast(t('Error al preparar la simulación') + ': ' + err.message, 'error');
  }
}

// ---- Simulation completion banner ----

function showCompletionBanner(id, title) {
  const label = title || id;
  const banner = document.createElement('div');
  banner.className = 'sim-complete-banner';
  banner.setAttribute('role', 'status');
  banner.innerHTML = `
    <div class="sim-complete-banner-inner">
      <span class="sim-complete-icon" aria-hidden="true">&#10003;</span>
      <div>
        <strong>${t('Simulación completada')}</strong>
        <div class="sim-complete-label">${escHtml(label)}</div>
      </div>
      <button class="sim-complete-dismiss" aria-label="${t('Cerrar')}">&times;</button>
    </div>
  `;
  document.body.appendChild(banner);

  // Trigger slide-down animation on next frame
  requestAnimationFrame(() => banner.classList.add('visible'));

  const dismiss = () => {
    banner.classList.add('hiding');
    setTimeout(() => banner.remove(), 400);
  };

  banner.querySelector('.sim-complete-dismiss').addEventListener('click', dismiss);
  setTimeout(dismiss, 8000);
}

// ---- WebSocket: live simulation progress ----
// Updates only the replicas and status cells of the affected rows, so open
// menus, focus and scroll position are not disturbed.

function applySimProgress(items) {
  items.forEach(({ id, runCount, percentage, status, position }) => {
    const sim = SIMS.find(s => s.id === id);
    if (!sim) return;
    Object.assign(sim, { runCount, percentage, status, position });
    const tr = document.querySelector(`tr[data-sim-id="${CSS.escape(id)}"]`);
    if (!tr) return;
    tr.querySelector('[data-cell="replicas"]').textContent = fmt.int(runCount);
    tr.querySelector('[data-cell="status"]').innerHTML = statusCellHtml(sim);
  });
}

// ---- Init ----

document.addEventListener('DOMContentLoaded', () => {
  loadSimulations();

  document.getElementById('btn-generate').addEventListener('click', openModal);
  document.getElementById('btn-modal-cancel').addEventListener('click', closeModal);
  document.getElementById('btn-modal-confirm').addEventListener('click', triggerGenerate);

  // Close modal on overlay click / Escape
  document.getElementById('modal-generate').addEventListener('click', e => {
    if (e.target === e.currentTarget) closeModal();
  });
  document.addEventListener('keydown', e => {
    if (e.key === 'Escape') closeModal();
  });

  // Search and filters
  const bind = (id, key, ev = 'change') => document.getElementById(id).addEventListener(ev, e => {
    view[key] = e.target.value;
    renderTable();
  });
  bind('filter-q', 'q', 'input');
  bind('filter-engine', 'engine');
  bind('filter-model', 'model');
  bind('filter-status', 'status');

  // Subscribe to live simulation progress updates and completion events
  const socket = io();
  socket.on('sim_progress', applySimProgress);
  socket.on('sim_completed', ({ id, title }) => {
    showCompletionBanner(id, title);
    toast(t('Simulación completada: {title}', { title: title || id }), 'success');
    loadSimulations();
  });

  socket.on('sim_failed', ({ id, title, error }) => {
    toast(t('Simulación con ERROR: {title} ({error})', { title: title || id, error: errorSummary(error) }), 'error');
    loadSimulations();
  });

  socket.on('new_sim_launched', ({ id, title, queued }) => {
    toast(queued ? t('Simulación en cola: {title}', { title: title || id }) : t('Simulación lanzada: {title}', { title: title || id }), 'info');
    loadSimulations();
  });
});
