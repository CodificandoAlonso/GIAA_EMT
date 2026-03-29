// ---- Utilities ----

function toast(msg, type = 'info') {
  const container = document.getElementById('toast-container');
  const el = document.createElement('div');
  el.className = `toast ${type}`;
  el.textContent = msg;
  container.appendChild(el);
  setTimeout(() => el.remove(), 4000);
}

function formatNum(n) {
  if (n === null || n === undefined || isNaN(n)) return '—';
  return Number(n).toLocaleString('es-ES');
}

// ---- Render simulation cards ----

function renderCard(sim) {
  const card = document.createElement('div');
  card.className = 'sim-card';
  card.setAttribute('role', 'button');
  card.setAttribute('tabindex', '0');

  const [datePart, timePart] = (sim.datetime || '—  —').split(' ');
  const chartsHtml = sim.hasCharts
    ? '<span class="charts-badge ready">&#10003; Gráficas listas</span>'
    : '<span class="charts-badge pending">&#9711; Sin gráficas</span>';

  const titleHtml = sim.title
    ? `<div class="sim-title">${sim.title}</div>`
    : '';
  const descHtml = sim.description
    ? `<div class="sim-description">${sim.description}</div>`
    : '';

  card.innerHTML = `
    <div class="sim-card-header">
      <div>
        ${titleHtml}
        <div class="sim-id">${sim.id}</div>
        <div class="sim-date">${datePart || '—'} ${timePart || ''}</div>
      </div>
      <span class="sim-card-badge">GAMA</span>
    </div>
    <div class="sim-card-body">
      ${descHtml}
      <div class="sim-meta-row">
        <span class="meta-label">Numero de Repeticiones por experimento</span>
        <span class="meta-value">${formatNum(sim.runCount)}</span>
      </div>
      <div class="sim-meta-row">
        <span class="meta-label">Estado</span>
        <span class="meta-value">Completada</span>
      </div>
    </div>
    <div class="sim-card-footer">
      ${chartsHtml}
      <button class="btn btn-primary btn-sm">Ver detalle &#8594;</button>
    </div>
  `;

  card.addEventListener('click', () => {
    window.location.href = `/simulation/${sim.id}`;
  });
  card.addEventListener('keydown', e => {
    if (e.key === 'Enter' || e.key === ' ') window.location.href = `/simulation/${sim.id}`;
  });

  return card;
}

// ---- Load simulations ----

async function loadSimulations() {
  const container = document.getElementById('sim-container');
  try {
    const res = await fetch('/api/simulations');
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const sims = await res.json();

    // Update stats bar
    document.getElementById('stat-total').textContent = formatNum(sims.length);
    document.getElementById('stat-charts').textContent = formatNum(sims.filter(s => s.hasCharts).length);
    document.getElementById('stat-latest').textContent = sims[0]?.datetime?.split(' ')[0] ?? '—';
    document.getElementById('sim-count-badge').textContent = `${sims.length} simulación${sims.length !== 1 ? 'es' : ''} encontrada${sims.length !== 1 ? 's' : ''}`;

    // Render cards
    if (sims.length === 0) {
      container.innerHTML = `
        <div class="empty-state">
          <div class="empty-icon">&#128650;</div>
          <p>No se han encontrado simulaciones.</p>
          <p style="margin-top:0.5rem;font-size:0.85rem;">Lanza una nueva simulación con el botón de arriba.</p>
        </div>`;
      return;
    }

    const grid = document.createElement('div');
    grid.className = 'sim-grid';
    sims.forEach(sim => grid.appendChild(renderCard(sim)));
    container.innerHTML = '';
    container.appendChild(grid);

  } catch (err) {
    container.innerHTML = `
      <div class="empty-state">
        <div class="empty-icon">&#9888;</div>
        <p>Error al cargar las simulaciones.</p>
        <p style="margin-top:0.5rem;font-size:0.83rem;color:var(--emt-red);">${err.message}</p>
      </div>`;
    toast('Error al conectar con el servidor', 'error');
  }
}

// ---- Generate simulation modal ----

function openModal() {
  document.getElementById('modal-generate').classList.add('open');
}

function closeModal() {
  document.getElementById('modal-generate').classList.remove('open');
}

async function triggerGenerate() {
  closeModal();
  toast('Lanzando simulación...', 'info');
  try {
    const res = await fetch('/api/simulations/generate', { method: 'POST' });
    const data = await res.json();
    toast(data.message || 'Simulación iniciada', res.ok ? 'success' : 'error');
    if (res.ok) setTimeout(loadSimulations, 3000);
  } catch (err) {
    toast('Error al lanzar la simulación: ' + err.message, 'error');
  }
}

// ---- Init ----

document.addEventListener('DOMContentLoaded', () => {
  loadSimulations();

  document.getElementById('btn-generate').addEventListener('click', openModal);
  document.getElementById('btn-modal-cancel').addEventListener('click', closeModal);
  document.getElementById('btn-modal-confirm').addEventListener('click', triggerGenerate);

  // Close modal on overlay click
  document.getElementById('modal-generate').addEventListener('click', e => {
    if (e.target === e.currentTarget) closeModal();
  });
});
