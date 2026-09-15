// ---- Utilities ----

function toast(msg, type = 'info') {
  const container = document.getElementById('toast-container');
  const el = document.createElement('div');
  el.className = `toast ${type}`;
  el.textContent = msg;
  container.appendChild(el);
  setTimeout(() => el.remove(), 4000);
}


const MODEL_LABELS = {
  with_agents:    'Con agentes pasajero',
  without_agents: 'Sin agentes pasajero',
  c_engine:       'Motor en C',
};

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
  card.setAttribute('data-sim-id', sim.id);

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
        <span class="meta-label">Solución</span>
        <span class="meta-value">${MODEL_LABELS[sim.model] || MODEL_LABELS['without_agents']}</span>
      </div>
      <div class="sim-meta-row">
        <span class="meta-label">Estado</span>
        <span class="meta-value">${sim.status}</span>
      </div>
    </div>
    <div class="sim-card-footer">
      ${chartsHtml}
      <div style="display:flex;gap:0.5rem;align-items:center;">
        <button class="btn btn-sm btn-danger" data-delete-sim="${sim.id}" title="Eliminar simulación">&#128465;</button>
        <button class="btn btn-primary btn-sm">Ver detalle &#8594;</button>
      </div>
    </div>
  `;

  // Render initial progress bar for in-progress simulations
  if (sim.status !== 'Completada') {
    const bar = document.createElement('div');
    bar.className = 'sim-progress-bar';
    bar.style.width = `${Math.min(100, Math.round(sim.runCount / 10))}%`;
    card.insertBefore(bar, card.firstChild);
  }

  card.querySelector(`[data-delete-sim]`)?.addEventListener('click', (e) => {
    e.stopPropagation();
    handleDeleteSim(sim.id, sim.title || sim.id);
  });

  card.addEventListener('click', () => {
    window.location.href = `/simulation/${sim.id}`;
  });
  card.addEventListener('keydown', e => {
    if (e.key === 'Enter' || e.key === ' ') window.location.href = `/simulation/${sim.id}`;
  });

  return card;
}

// ---- Delete simulation ----

async function handleDeleteSim(simId, label) {
  const confirmed = confirm(
    `ATENCIÓN: ACCIÓN IRREVERSIBLE\n\nVas a eliminar la simulación:\n"${label}"\n\nEsto borrará permanentemente TODOS los datos, resultados y logs.\n\n¿Estás seguro de que quieres continuar?`
  );
  if (!confirmed) return;
  try {
    const res = await fetch(`/api/simulations/${simId}`, { method: 'DELETE' });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) { toast(data.error || 'Error al eliminar la simulación', 'error'); return; }
    toast(`Simulación "${label}" eliminada`, 'info');
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
  toast('Preparando directorio de simulación...', 'info');
  try {
    const res = await fetch('/api/simulations/prepare', { method: 'POST' });
    const data = await res.json();
    if (!res.ok) {
      toast(data.error || 'Error al preparar la simulación', 'error');
      return;
    }
    toast('Directorio creado. Abriendo configuración...', 'success');
    setTimeout(() => {
      window.location.href = `/config/${data.simId}`;
    }, 800);
  } catch (err) {
    toast('Error al preparar la simulación: ' + err.message, 'error');
  }
}

// ---- Simulation completion banner ----

function showCompletionBanner(id, title) {
  const label = title || id;
  const banner = document.createElement('div');
  banner.className = 'sim-complete-banner';
  banner.innerHTML = `
    <div class="sim-complete-banner-inner">
      <span class="sim-complete-icon">&#10003;</span>
      <div>
        <strong>Simulaci&oacute;n completada</strong>
        <div class="sim-complete-label">${label}</div>
      </div>
      <button class="sim-complete-dismiss" aria-label="Cerrar">&times;</button>
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

function applySimProgress(sims) {
  sims.forEach(({ id, runCount, percentage, status }) => {
    const card = document.querySelector(`[data-sim-id="${id}"]`);
    if (!card) return;

    // Create or update the progress bar element
    let bar = card.querySelector('.sim-progress-bar');
    if (!bar) {
      bar = document.createElement('div');
      bar.className = 'sim-progress-bar';
      card.insertBefore(bar, card.firstChild);
    }
    

    // Update run count and status text in the meta rows
    const metaValues = card.querySelectorAll('.meta-value');
    if (metaValues[0]) metaValues[0].textContent = formatNum(runCount);
    if (metaValues[2]) metaValues[2].textContent = status;


        // metaValues: [0] nº repeticiones, [1] Solución, [2] Estado.
    // El estado es [2]; comparar contra [1] leia la etiqueta del modelo,
    // que nunca es 'Esperando Graficas', de modo que el guardia no saltaba.
    if (metaValues[2]?.textContent != 'Esperando Gr\u00e1ficas'){
    bar.style.width = `${percentage}%`;
    }

    // When a sim reaches 100%, fade the bar out after a moment
    if (runCount >= 1000 && metaValues[2]?.textContent != 'Esperando Gr\u00e1ficas') {
      bar.style.width = '100%';
      setTimeout(() => {
        bar.style.opacity = '0';
        setTimeout(() => bar.remove(), 500);
      }, 1500);
    }
  });
}

function endsimprocess(id) {
  const card = document.querySelector(`[data-sim-id="${id}"]`);
  if (!card) return;

  let bar = card.querySelector('.sim-progress-bar');
  if (!bar) {
    bar = document.createElement('div');
    bar.className = 'sim-progress-bar';
    card.insertBefore(bar, card.firstChild);
  }
  bar.style.width = `100%`;
  const metaValues = card.querySelectorAll('.meta-value');
 
    if (metaValues[0]) metaValues[0].textContent = formatNum(1000);
  // [1] es la Solución; escribir ahi borraba el nombre del modelo.
  if (metaValues[2]) metaValues[2].textContent = "Completada";

  setTimeout(() => {
      bar.style.opacity = '0';
      setTimeout(() => bar.remove(), 500);
    }, 1500);

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

  // Subscribe to live simulation progress updates and completion events
  const socket = io();
  socket.on('sim_progress', applySimProgress);
  socket.on('sim_completed', ({ id, title }) => {

    showCompletionBanner(id, title);
    endsimprocess(id);
    toast(`Simulaci\u00f3n completada: ${title || id}`, 'success');
    loadSimulations();
  });

  socket.on('new_sim_launched', ({ id, title }) => {
    toast(`Nueva simulación creada: ${title || id}`, 'info');
    loadSimulations();
  });

});
