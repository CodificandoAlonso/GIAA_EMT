// ============================================================
// i18n.js — idioma de la interfaz (es / en)
//
// El español es el texto de origen: t('texto en español') devuelve el
// mismo texto en español y la traducción en inglés si el idioma es «en».
// Los valores internos (estados, ids, claves de datos) NO se traducen;
// solo se traduce lo que se muestra. Los títulos y descripciones de las
// simulaciones son entrada del usuario y nunca pasan por aquí.
//
// El idioma se guarda en una cookie (`lang`) para que el servidor
// también responda en ese idioma, y se cambia recargando la página.
// ============================================================
(function () {
  const COOKIE = 'lang';
  const SUPPORTED = ['es', 'en'];

  function readLang() {
    const m = document.cookie.match(/(?:^|;\s*)lang=(es|en)\b/);
    return m ? m[1] : 'es';
  }

  const lang = readLang();

  // ---- Inglés: clave = texto en español ----
  const EN = {
    // Marca y cabeceras
    'Panel de simulaciones GAMA': 'GAMA Simulation Dashboard',
    'Panel GAMA — EMT Madrid': 'GAMA Dashboard — EMT Madrid',
    'Cátedra EMT-GIAA': 'EMT-GIAA Chair',
    'Movilidad urbana de Madrid · GIAA': 'Madrid Urban Mobility · GIAA',
    'Simulación — EMT Madrid': 'Simulation — EMT Madrid',
    'Configurar Simulación — EMT Madrid': 'Configure Simulation — EMT Madrid',
    'Configurar Simulación': 'Configure Simulation',
    'Configurar {id} — EMT': 'Configure {id} — EMT',
    '{title} — EMT Dashboard': '{title} — EMT Dashboard',
    'Cargando...': 'Loading...',
    'Idioma': 'Language',

    // Dashboard
    'Nueva simulación': 'New simulation',
    'Simulaciones GAMA': 'GAMA simulations',
    'Resultados de experimentos sobre movilidad urbana EMT Madrid': 'Results of urban mobility experiments for EMT Madrid',
    'Total Simulaciones': 'Total simulations',
    'carpetas en /data/logs': 'folders in /data/logs',
    'Con Gráficas': 'With charts',
    'listas para visualizar': 'ready to view',
    'Última Ejecución': 'Latest run',
    'más reciente': 'most recent',
    'Cargando simulaciones...': 'Loading simulations...',
    'Lanzar nueva simulación': 'Launch a new simulation',
    'Se ejecutará el pipeline GAMA batch. Esto puede tardar varios minutos dependiendo del número de réplicas configurado. ¿Deseas continuar?':
      'The GAMA batch pipeline will run. This can take several minutes depending on the configured number of replicas. Do you want to continue?',
    'Cancelar': 'Cancel',
    'Confirmar': 'Confirm',

    // Estados (el valor interno sigue en español)
    'Preparada': 'Prepared',
    'En cola': 'Queued',
    'En progreso': 'In progress',
    'Esperando Gráficas': 'Waiting for charts',
    'Completada': 'Completed',
    'Error': 'Error',

    // Modelos
    'Con agentes pasajero': 'With passenger agents',
    'Sin agentes pasajero': 'Without passenger agents',
    'Motor en C': 'C engine',
    'Motor en C ': 'C engine',

    // Tarjeta de simulación
    'Gráficas listas': 'Charts ready',
    'Sin gráficas': 'No charts',
    'Numero de Repeticiones por experimento': 'Number of repetitions per experiment',
    'Solución': 'Solution',
    'Estado': 'Status',
    'Eliminar simulación': 'Delete simulation',
    'Ver detalle': 'View details',
    'ATENCIÓN: ACCIÓN IRREVERSIBLE\n\nVas a eliminar la simulación:\n"{label}"\n\nEsto borrará permanentemente TODOS los datos, resultados y logs.\n\n¿Estás seguro de que quieres continuar?':
      'WARNING: IRREVERSIBLE ACTION\n\nYou are about to delete the simulation:\n"{label}"\n\nThis will permanently delete ALL data, results and logs.\n\nAre you sure you want to continue?',
    'Error al eliminar la simulación': 'Error deleting the simulation',
    'Simulación "{label}" eliminada': 'Simulation "{label}" deleted',
    'Simulación eliminada. Redirigiendo...': 'Simulation deleted. Redirecting...',
    'No se han encontrado simulaciones.': 'No simulations found.',
    'Lanza una nueva simulación con el botón de arriba.': 'Launch a new simulation with the button above.',
    'Error al cargar las simulaciones.': 'Error loading the simulations.',
    'Error al conectar con el servidor': 'Error connecting to the server',
    '{n} simulación encontrada': '{n} simulation found',
    '{n} simulaciones encontradas': '{n} simulations found',
    'Preparando directorio de simulación...': 'Preparing simulation directory...',
    'Error al preparar la simulación': 'Error preparing the simulation',
    'Directorio creado. Abriendo configuración...': 'Directory created. Opening configuration...',
    'Simulación completada': 'Simulation completed',
    'Cerrar': 'Close',
    'Simulación completada: {title}': 'Simulation completed: {title}',
    'Simulación con ERROR: {title} ({error})': 'Simulation with ERROR: {title} ({error})',
    'Simulación en cola: {title}': 'Simulation queued: {title}',
    'Simulación lanzada: {title}': 'Simulation launched: {title}',
    'Nueva simulación creada: {title}': 'New simulation created: {title}',

    // Detalle de simulación
    'Cargando datos de la simulación...': 'Loading simulation data...',
    'Volver al dashboard': 'Back to dashboard',
    'Descargar log': 'Download log',
    'Información sobre la Simulación realizada': 'Information about the simulation run',
    'Número de repeticiones por experimento': 'Number of repetitions per experiment',
    'Tiempo total de simulación': 'Total simulation time',
    'Solución simulada': 'Simulated solution',
    'Estadísticas generales obtenidas': 'Overall statistics',
    'Ocupación general': 'Overall occupancy',
    'de capacidad media': 'of average capacity',
    'Sentido A': 'Direction A',
    'Sentido B': 'Direction B',
    'Buses': 'Buses',
    'Buses físicos encargados': 'Physical buses assigned',
    'Viajes totales': 'Total trips',
    'viajes ejecutados': 'trips run',
    'Espera media pasajeros': 'Mean passenger wait',
    'tiempo medio de espera': 'mean waiting time',
    'Índice de Regularidad': 'Regularity index',
    'Valor medio': 'Mean value',
    'Análisis de la simulación': 'Simulation analysis',
    'Por ruta': 'By route',
    'Por autobuses': 'By bus',
    'Cargando mapa...': 'Loading map...',
    'Log de ejecución': 'Execution log',
    'Log Completo': 'Full log',
    'Cargando log...': 'Loading log...',
    'Simulación no encontrada (HTTP {status})': 'Simulation not found (HTTP {status})',
    'No se encontró archivo de log.': 'Log file not found.',
    'Error al cargar la simulación.': 'Error loading the simulation.',
    'Error al cargar la simulación': 'Error loading the simulation',
    '(código {code})': '(code {code})',
    'La simulación ha fallado': 'The simulation has failed',
    'Consulta el log de ejecución más abajo para ver el detalle.': 'See the execution log below for details.',
    'Ocupación media Sentido {name}': 'Mean occupancy Direction {name}',
    'Sentido {name}': 'Direction {name}',
    'No hay datos de autobuses disponibles.': 'No bus data available.',
    'Ver por:': 'View by:',
    'Autobús Físico': 'Physical bus',
    'Franja horaria': 'Time slot',
    'Franja horaria:': 'Time slot:',
    'Selecciona un autobús físico:': 'Select a physical bus:',
    'Viajes en esta franja — {n} viaje': 'Trips in this time slot — {n} trip',
    'Viajes en esta franja — {n} viajes': 'Trips in this time slot — {n} trips',
    'Autobús {id} — {n} viaje': 'Bus {id} — {n} trip',
    'Autobús {id} — {n} viajes': 'Bus {id} — {n} trips',
    'Parada': 'Stop',
    'Prog.': 'Sched.',
    'Sentido / Bus': 'Dir. / Bus',
    'Sentido': 'Direction',
    'Ocup.': 'Occ.',
    'Salida': 'Departure',
    'T. viaje': 'Trip time',
    'Regularidad': 'Regularity',
    'Selecciona un viaje para ver detalles': 'Select a trip to see its details',
    'Ocupación media por parada': 'Mean occupancy per stop',
    'Gráfica de ocupación': 'Occupancy chart',
    'Clic para ampliar': 'Click to enlarge',
    'Bus {bus} · Viaje {trip} · {stop} · {time}': 'Bus {bus} · Trip {trip} · {stop} · {time}',
    'Ocupación media': 'Mean occupancy',
    'Tiempo de viaje': 'Trip time',
    '% Simulaciones con retraso': '% of simulations delayed',
    'Retraso medio de salida': 'Mean departure delay',
    'Hora programada': 'Scheduled time',
    'Salida media real': 'Mean actual departure',
    'Valor de Regularidad': 'Regularity value',
    'Normal': 'Normal',
    'Leve': 'Mild',
    'Moderado': 'Moderate',
    'Alto': 'High',
    'Crítico': 'Critical',
    'Nivel de alerta:': 'Alert level:',
    'No se encontraron datos geoespaciales para esta simulación.': 'No geospatial data found for this simulation.',
    'Error al cargar geodata: {error}': 'Error loading geodata: {error}',
    'Mostrar info por:': 'Show info by:',
    'General': 'General',
    'Sin datos': 'No data',
    'Parada {num} · {name}': 'Stop {num} · {name}',
    'Nombre': 'Name',
    'Núm. parada': 'Stop no.',
    'Ocupación media general': 'Overall mean occupancy',
    'Espera media general': 'Overall mean wait',
    'Media de subida de pasajeros': 'Mean passenger boardings',
    'Media de pasajeros que no pudieron subir': 'Mean passengers unable to board',
    'Media de bajada de pasajeros': 'Mean passenger alightings',
    'Ocupación por franja horaria ({dir})': 'Occupancy by time slot ({dir})',
    'Ocupación por franja': 'Occupancy by time slot',
    'Ocupación franja {ts}:00': 'Occupancy time slot {ts}:00',
    'Espera media franja {ts}:00': 'Mean wait time slot {ts}:00',
    'Comparativa ocupación franja {ts}:00 ({dir})': 'Occupancy comparison time slot {ts}:00 ({dir})',
    'Ocupación franja {ts}': 'Occupancy time slot {ts}',
    'Tiempo de tránsito general': 'Overall transit time',
    'Tiempo esperado': 'Expected time',
    'Tiempo de tránsito franja {ts}:00': 'Transit time time slot {ts}:00',
    'Tiempo esperado franja {ts}:00': 'Expected time time slot {ts}:00',
    '(franja {ts})': '(time slot {ts})',
    'Comparativa tiempo de tránsito franja {ts}:00': 'Transit time comparison time slot {ts}:00',
    'Tiempo tránsito franja {ts}': 'Transit time time slot {ts}',
    'Parada origen': 'Origin stop',
    'Parada destino': 'Destination stop',
    'Sin datos de tránsito para este tramo.': 'No transit data for this section.',
    'Gráfica ampliada': 'Enlarged chart',
    'ID de simulación inválido.': 'Invalid simulation ID.',
    'Nueva simulación creada': 'New simulation created',

    // Configuración
    'Guardar': 'Save',
    'Guardar y Lanzar': 'Save and launch',
    'Título': 'Title',
    'Nombre de la simulación': 'Simulation name',
    'Descripción': 'Description',
    'Descripción breve...': 'Short description...',
    'Línea': 'Line',
    'Ejecución': 'Execution',
    'Compartida': 'Shared',
    'Exclusiva (medición de energía)': 'Exclusive (energy measurement)',
    'Exclusiva: espera a que no haya otras simulaciones en marcha y no deja arrancar ninguna mientras dura. Úsala para medir recursos/energía.':
      'Exclusive: waits until no other simulations are running and does not let any start while it lasts. Use it to measure resources/energy.',
    'Semilla para reproducibilidad': 'Seed for reproducibility',
    'Vacío = se genera automáticamente': 'Empty = generated automatically',
    'Entero entre 0 y 18446744073709551615. Misma semilla y mismos parámetros dan los mismos resultados.':
      'Integer between 0 and 18446744073709551615. The same seed and parameters give the same results.',
    'Cargando parámetros de simulación...': 'Loading simulation parameters...',
    'Autobuses': 'Buses',
    'Ruta': 'Route',
    'La semilla debe ser un número entero positivo (máx. 20 cifras)': 'The seed must be a positive integer (max. 20 digits)',
    'Configuración guardada correctamente': 'Configuration saved successfully',
    'Error al guardar: {error}': 'Error saving: {error}',
    'Guardado. Lanzando simulación...': 'Saved. Launching simulation...',
    'Error al lanzar la simulación': 'Error launching the simulation',
    'Simulación en cola (posición {position}): arrancará cuando haya hueco': 'Simulation queued (position {position}): it will start when there is room',
    'Simulación lanzada en segundo plano': 'Simulation launched in the background',
    'Hora:': 'Hour:',
    'Autobús físico': 'Physical bus',
    'Autobuses Físicos': 'Physical buses',
    'Cada autobús físico tiene una lista de salidas desde los terminales de la línea.': 'Each physical bus has a list of departures from the line terminals.',
    '+ Nuevo autobús': '+ New bus',
    'ID del autobús (número):': 'Bus ID (number):',
    'ej. 3599': 'e.g. 3599',
    'Crear': 'Create',
    'El ID es el identificador del autobús físico (matrícula/número de unidad).': 'The ID identifies the physical bus (plate/unit number).',
    'Introduce un ID de autobús': 'Enter a bus ID',
    'Ya existe un autobús con ese ID': 'A bus with that ID already exists',
    'Autobús {id} creado': 'Bus {id} created',
    'Franja {ts}:00 – {next}:00': 'Time slot {ts}:00 – {next}:00',
    '{n} salida programada en esta franja.': '{n} departure scheduled in this time slot.',
    '{n} salidas programadas en esta franja.': '{n} departures scheduled in this time slot.',
    'No hay salidas programadas en la franja {ts}:00 – {next}:00.': 'No departures scheduled in the {ts}:00 – {next}:00 time slot.',
    'Autobús': 'Bus',
    'Dirección': 'Direction',
    'Hora de salida': 'Departure time',
    'Eliminar salida': 'Delete departure',
    'Salida eliminada': 'Departure deleted',
    'No hay autobuses configurados. Añade uno con el botón de arriba.': 'No buses configured. Add one with the button above.',
    'Autobús {id}': 'Bus {id}',
    '{n} salida': '{n} departure',
    '{n} salidas': '{n} departures',
    'Ver salidas': 'Show departures',
    'Ocultar': 'Hide',
    'Eliminar': 'Delete',
    '¿Eliminar el autobús {id} y todas sus salidas?': 'Delete bus {id} and all its departures?',
    'Autobús {id} eliminado': 'Bus {id} deleted',
    'Sin salidas. Añade una con el botón de abajo.': 'No departures. Add one with the button below.',
    'Formato HH:MM': 'Format HH:MM',
    'Nueva salida:': 'New departure:',
    '(desde {stop})': '(from {stop})',
    '+ Añadir': '+ Add',
    'Hora inválida (usa formato H:MM o HH:MM)': 'Invalid time (use H:MM or HH:MM format)',
    'Salida añadida': 'Departure added',
    'Mostrar por:': 'Show by:',
    'Parada {id}': 'Stop {id}',
    'No hay datos de pasajeros para esta parada en la dirección seleccionada.': 'No passenger data for this stop in the selected direction.',
    'Media de subidas inválida: introduce un número ≥ 0': 'Invalid mean boardings: enter a number ≥ 0',
    'Porcentaje de bajadas inválido: introduce un valor entre 0 y {max}': 'Invalid alighting percentage: enter a value between 0 and {max}',
    'No hay cambios que aplicar': 'No changes to apply',
    'La media de subidas actual es 0: no se puede escalar': 'The current mean boardings is 0: it cannot be scaled',
    'Parada {id}: valores actualizados en todas las franjas': 'Stop {id}: values updated in all time slots',
    'Parada {id} franja {ts}h: valores actualizados': 'Stop {id} time slot {ts}h: values updated',
    'Sin datos de bajadas': 'No alighting data',
    'Parada de cabecera/final: no se modelan bajadas parciales': 'Terminal stop: partial alightings are not modelled',
    'Sin datos de subidas': 'No boarding data',
    'Pasajeros en esta parada': 'Passengers at this stop',
    'Valores medios de todas las franjas. Cambia un valor y pulsa <strong>Aplicar</strong> para escalar <em>todas las franjas horarias</em> proporcionalmente.':
      'Mean values across all time slots. Change a value and press <strong>Apply</strong> to scale <em>all time slots</em> proportionally.',
    'Media de pasajeros que llegan a la parada por hora': 'Mean passengers arriving at the stop per hour',
    '% medio de la ocupación del autobús que se baja en la parada': 'Mean % of bus occupancy alighting at the stop',
    'Franjas con datos': 'Time slots with data',
    'Aplicar a todas las franjas': 'Apply to all time slots',
    'Franja horaria: {ts}:00 – {next}:00': 'Time slot: {ts}:00 – {next}:00',
    'Cambia un valor y pulsa <strong>Aplicar</strong> para modificar <em>solo esta franja</em>.':
      'Change a value and press <strong>Apply</strong> to modify <em>this time slot only</em>.',
    'Número de pasajeros que llegan a la parada en esta franja': 'Number of passengers arriving at the stop in this time slot',
    '% de la ocupación del autobús que se baja en la parada': '% of bus occupancy alighting at the stop',
    'Aplicar a esta franja': 'Apply to this time slot',
    'Tramo {from} → {to}': 'Section {from} → {to}',
    'No hay datos de tiempos para este tramo en la dirección seleccionada.': 'No timing data for this section in the selected direction.',
    'Formato inválido — usa MM:SS (ej: 02:35)': 'Invalid format — use MM:SS (e.g. 02:35)',
    'Tramo {key}: tiempos actualizados en todas las franjas': 'Section {key}: times updated in all time slots',
    'Tramo {key} franja {ts}h: tiempo actualizado': 'Section {key} time slot {ts}h: time updated',
    'Tiempo de tránsito (general)': 'Transit time (overall)',
    'Tiempo medio de tránsito en este tramo. Cambia el valor y pulsa <strong>Aplicar</strong> para escalar <em>todas las franjas horarias</em> proporcionalmente.':
      'Mean transit time on this section. Change the value and press <strong>Apply</strong> to scale <em>all time slots</em> proportionally.',
    'Tiempo medio (todas las franjas)': 'Mean time (all time slots)',
    'formato MM:SS': 'format MM:SS',
    'Tramo': 'Section',
    'Cambia el valor y pulsa <strong>Aplicar</strong> para modificar <em>solo esta franja</em>.':
      'Change the value and press <strong>Apply</strong> to modify <em>this time slot only</em>.',
    'Tiempo medio en esta franja': 'Mean time in this time slot',
    'Sin datos para esta franja': 'No data for this time slot',
    'Solo afecta a la franja <strong>{ts}:00 – {next}:00</strong>.': 'Only affects the <strong>{ts}:00 – {next}:00</strong> time slot.',
    'Error al cargar los parámetros.': 'Error loading the parameters.',
    'Cambiar el idioma recarga la página y se perderán los cambios sin guardar. ¿Continuar?':
      'Changing the language reloads the page and unsaved changes will be lost. Continue?',

    // Validación (Bhattacharyya)
    'Validación: simulado frente a esperado': 'Validation: simulated vs expected',
    'Un par simulado/esperado se considera equivalente si su coeficiente de Bhattacharyya es ≥ {umbral}.':
      'A simulated/expected pair is considered equivalent if its Bhattacharyya coefficient is ≥ {umbral}.',
    'Ocupación equivalente': 'Equivalent occupancy',
    'Tiempo equivalente': 'Equivalent time',
    'Conjunto equivalente': 'Equivalent overall',
    '{a} de {b} celdas': '{a} of {b} cells',
    'Coeficiente medio (ocupación)': 'Mean coefficient (occupancy)',
    'Coeficiente medio (tiempo)': 'Mean coefficient (time)',
    'mediana {v}': 'median {v}',
    'Sesgo medio (ocupación)': 'Mean bias (occupancy)',
    'Sesgo medio (tiempo)': 'Mean bias (time)',
    '{v} σ': '{v} σ',
    'Regresión con banda: ocupación': 'Regression with band: occupancy',
    'Regresión con banda: tiempo': 'Regression with band: time',
    'Media simulada frente a esperada: ocupación': 'Simulated vs expected mean: occupancy',
    'Media simulada frente a esperada: tiempo': 'Simulated vs expected mean: time',
    'Descomposición de la validación: ocupación': 'Validation decomposition: occupancy',
    'Descomposición de la validación: tiempo': 'Validation decomposition: time',
    'Equivalencia por franja horaria': 'Equivalence by time slot',
    'Equivalencia por parada': 'Equivalence by stop',
    'Equivalencia por tramo': 'Equivalence by section',
    'Histograma del coeficiente de Bhattacharyya': 'Bhattacharyya coefficient histogram',

    // Alt/aria del selector
    'Cambiar idioma': 'Change language',
  };

  // Normaliza espacios para buscar texto estático del HTML
  const norm = s => s.replace(/\s+/g, ' ').trim();

  function t(es, vars) {
    let s = es;
    if (lang === 'en') {
      s = EN[es] ?? EN[norm(es)] ?? es;
    }
    if (vars) {
      s = s.replace(/\{(\w+)\}/g, (m, k) => (vars[k] !== undefined ? vars[k] : m));
    }
    return s;
  }

  // Traduce un texto estático conservando símbolos iniciales (▶, ←, 🗑…) y los espacios
  function translateStatic(raw) {
    const m = raw.match(/^([^\p{L}\p{N}]*)([\s\S]*?)(\s*)$/u);
    if (!m || !m[2]) return raw;
    const core = norm(m[2]);
    const tr = EN[core] ?? EN[core + ' '];
    return tr === undefined ? raw : m[1] + tr + m[3];
  }

  // Aplica el idioma al HTML estático de la página (solo hace falta en inglés)
  function applyStatic(root) {
    if (lang !== 'en') return;
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
      acceptNode: n => {
        const p = n.parentNode && n.parentNode.nodeName;
        return (p === 'SCRIPT' || p === 'STYLE') ? NodeFilter.FILTER_REJECT : NodeFilter.FILTER_ACCEPT;
      },
    });
    const nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);
    nodes.forEach(n => { n.nodeValue = translateStatic(n.nodeValue); });
    root.querySelectorAll('[title],[placeholder],[alt],[aria-label]').forEach(el => {
      ['title', 'placeholder', 'alt', 'aria-label'].forEach(a => {
        if (el.hasAttribute(a)) el.setAttribute(a, translateStatic(el.getAttribute(a)));
      });
    });
    document.title = translateStatic(document.title);
  }

  function setLang(next) {
    if (!SUPPORTED.includes(next) || next === lang) return;
    if (document.body.classList.contains('config-page') &&
        !confirm(t('Cambiar el idioma recarga la página y se perderán los cambios sin guardar. ¿Continuar?'))) return;
    document.cookie = `${COOKIE}=${next}; path=/; max-age=31536000; SameSite=Lax`;
    location.reload();
  }

  function buildSwitch() {
    const nav = document.querySelector('.header-nav');
    if (!nav) return;
    const wrap = document.createElement('div');
    wrap.className = 'lang-switch';
    wrap.setAttribute('role', 'group');
    wrap.setAttribute('aria-label', t('Cambiar idioma'));
    SUPPORTED.forEach(code => {
      const b = document.createElement('button');
      b.type = 'button';
      b.className = 'lang-btn';
      b.dataset.lang = code;
      b.textContent = code.toUpperCase();
      b.setAttribute('aria-pressed', String(code === lang));
      if (code === lang) b.classList.add('active');
      b.addEventListener('click', () => setLang(code));
      wrap.appendChild(b);
    });
    nav.insertBefore(wrap, nav.firstChild);
  }

  document.documentElement.lang = lang;

  window.I18N = {
    lang,
    locale: lang === 'en' ? 'en-GB' : 'es-ES',
    t,
    setLang,
  };
  window.t = t;

  document.addEventListener('DOMContentLoaded', () => {
    applyStatic(document.body);
    document.title = lang === 'en' ? translateStatic(document.title) : document.title;
    buildSwitch();
  });
})();
