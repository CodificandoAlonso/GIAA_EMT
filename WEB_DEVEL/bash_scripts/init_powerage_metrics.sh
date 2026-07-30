#!/usr/bin/env bash
# ==========================================================================
# metrics.sh — arranque y parada manual del muestreador de energia del host.
#
# monitor_resources.py (contenedor) lo arranca run_simulation.sh solo.
# monitor_energy.py (host, root, RAPL via powercap) NO: es este script.
#
# Secuencia por batch:
#     sudo ./metrics.sh start sol1     # linea base en frio + muestreo
#     ./run_simulation.sh              # en OTRA terminal
#     sudo ./metrics.sh stop  sol1     # volcado + linea base en caliente
#
# Cada etiqueta escribe en su propio directorio, asi que un segundo batch
# no puede sobrescribir al primero y no hay que renombrar nada a mano.
#
# Interfaz asumida de monitor_energy.py: --outdir DIR y --baseline SEGUNDOS,
# volcando energy_summary.json y energy_timeseries.csv en DIR. Si tu copia
# difiere, comprueba `python3 monitor_energy.py --help` y ajusta MON_ARGS.
# ==========================================================================

set -euo pipefail

# ---------------------------- AJUSTES -------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"      # bash_scripts -> WEB_DEVEL -> raiz

MONITOR="$SCRIPT_DIR/monitor_energy.py"
LOGS_DIR="$REPO_ROOT/WEB_DEVEL/data/logs"
RUN_DIR="$LOGS_DIR/_metrics"                       # pidfiles y stdout del muestreador

BASELINE_S=180                # duracion de la linea base, en frio y en caliente
EXPECT_CPUS="0-11"            # cpuset esperado del contenedor (solo P-cores)
IDLE_CPU_MAX=5.0              # % de CPU del contenedor por encima del cual NO se mide la base
POWERCAP="/sys/class/powercap"

# ---------------------------- UTILIDADES ----------------------------------
RED=$'\033[0;31m'; GRN=$'\033[0;32m'; YEL=$'\033[1;33m'; BLU=$'\033[0;34m'; NC=$'\033[0m'
info()  { printf '%s[ i ]%s %s\n' "$BLU" "$NC" "$*"; }
ok()    { printf '%s[ ok]%s %s\n' "$GRN" "$NC" "$*"; }
warn()  { printf '%s[ ! ]%s %s\n' "$YEL" "$NC" "$*"; }
die()   { printf '%s[err]%s %s\n' "$RED" "$NC" "$*" >&2; exit 1; }

need_root() {
    [[ "$(id -u)" -eq 0 ]] || die "requiere root (RAPL). Ejecuta: sudo $0 $*"
}

container_id() { (cd "$REPO_ROOT" && docker compose ps -q 2>/dev/null | head -1) || true; }

container_cpu_pct() {
    local cid="$1" out
    out="$(docker stats --no-stream --format '{{.CPUPerc}}' "$cid" 2>/dev/null || true)"
    printf '%s' "${out%\%}"
}

samplers_running() { pgrep -f 'monitor_energy\.py' 2>/dev/null || true; }

# ---------------------------- COMPROBACIONES ------------------------------
preflight() {
    local strict="${1:-strict}"

    [[ -f "$MONITOR" ]] || die "no encuentro $MONITOR"
    [[ -d "$POWERCAP" ]] || die "$POWERCAP no existe: sin RAPL en este kernel"

    local n_dom
    n_dom="$(find "$POWERCAP" -maxdepth 1 -name 'intel-rapl:*' 2>/dev/null | wc -l)"
    [[ "$n_dom" -gt 0 ]] || die "ningun dominio intel-rapl en $POWERCAP"
    ok "RAPL: $n_dom dominios visibles en $POWERCAP"

    # un solo muestreador, o la serie sale entrelazada e inservible
    local pids; pids="$(samplers_running)"
    if [[ -n "$pids" ]]; then
        warn "ya hay monitor_energy.py corriendo:"
        pgrep -af 'monitor_energy\.py' || true
        die "dos muestreadores escriben el mismo CSV. Para el viejo antes de seguir."
    fi
    ok "no hay otro muestreador activo"

    # governor: si no es performance, la frecuencia varia entre batches
    local gov
    gov="$(cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor 2>/dev/null || echo '?')"
    if [[ "$gov" == "performance" ]]; then
        ok "governor = performance"
    else
        warn "governor = $gov (esperado performance)"
        warn "  sudo cpupower frequency-set -g performance"
        [[ "$strict" == "strict" ]] && die "corrige el governor o relanza con SKIP_GOV=1"
    fi

    # contenedor arriba, pinneado y ocioso
    local cid; cid="$(container_id)"
    if [[ -z "$cid" ]]; then
        warn "contenedor no detectado (docker compose ps vacio)"
        warn "  la linea base debe medirse CON el contenedor levantado y ocioso"
        [[ "$strict" == "strict" ]] && die "levanta el contenedor: docker compose up -d"
    else
        ok "contenedor $cid arriba"

        local cpuset
        cpuset="$(docker inspect -f '{{.HostConfig.CpusetCpus}}' "$cid" 2>/dev/null || true)"
        if [[ "$cpuset" == "$EXPECT_CPUS" ]]; then
            ok "cpuset = $cpuset"
        else
            warn "cpuset = '${cpuset:-<vacio>}', esperado '$EXPECT_CPUS'"
            warn "  sin anclaje a P-cores el reparto P/E contamina la comparacion"
        fi

        local cpu; cpu="$(container_cpu_pct "$cid")"
        if [[ -n "$cpu" ]] && awk -v c="$cpu" -v m="$IDLE_CPU_MAX" 'BEGIN{exit !(c>m)}'; then
            warn "CPU del contenedor = ${cpu}% (umbral ${IDLE_CPU_MAX}%)"
            warn "  algo esta trabajando: batch en curso, o el dashboard Node abierto"
            warn "  esa carga entraria en P_idle y falsearia la energia atribuible"
            [[ "$strict" == "strict" ]] && die "deja la maquina ociosa y repite"
        else
            ok "contenedor ocioso (CPU ${cpu:-?}%)"
        fi
    fi

    # portatil enchufado: en bateria el firmware recorta PL1 a mitad de batch
    local ac
    for f in /sys/class/power_supply/A*/online /sys/class/power_supply/AC*/online; do
        [[ -r "$f" ]] && ac="$(cat "$f")" && break
    done
    if [[ "${ac:-1}" == "1" ]]; then ok "alimentacion de red"
    else warn "EN BATERIA: PL1 se recortara y el batch no sera comparable"; fi
}

# ---------------------------- ACCIONES ------------------------------------
cmd_start() {
    local label="$1"
    need_root "start" "$label"
    preflight "${SKIP_GOV:+lax}"

    local outdir="$LOGS_DIR/_energy_${label}"
    local pidfile="$RUN_DIR/${label}.pid"
    local logfile="$RUN_DIR/${label}.monitor.log"

    if [[ -e "$outdir" ]] && compgen -G "$outdir/*" >/dev/null; then
        local stamp; stamp="$(date +%Y%m%d_%H%M%S)"
        warn "$outdir ya tiene datos; lo aparto a ${outdir}_pre_${stamp}"
        mv "$outdir" "${outdir}_pre_${stamp}"
    fi
    mkdir -p "$outdir" "$RUN_DIR"

    [[ -f "$pidfile" ]] && die "existe $pidfile: hay un start sin su stop"

    info "linea base en FRIO: ${BASELINE_S}s, no toques la maquina"
    info "muestreador desacoplado de esta terminal (setsid): sobrevive al cierre"

    setsid nohup python3 "$MONITOR" \
        --outdir "$outdir" --baseline "$BASELINE_S" \
        >"$logfile" 2>&1 &
    local pid=$!
    echo "$pid" > "$pidfile"
    date +%s > "$RUN_DIR/${label}.t0"      # ancla para localizar el SIMULATION_* del batch

    sleep 3
    kill -0 "$pid" 2>/dev/null || { cat "$logfile" >&2; rm -f "$pidfile"
        die "el muestreador murio al arrancar (log arriba)"; }

    ok "muestreador PID $pid  ->  $outdir"
    echo
    echo "  1. espera ${BASELINE_S}s de linea base antes de lanzar el batch"
    echo "  2. en otra terminal:  ./run_simulation.sh"
    echo "  3. desatendido:       sudo $0 watch $label   (para solo al acabar el batch)"
    echo "     o a mano:          sudo $0 stop  $label"
    echo
    info "dominios detectados:"
    sed -n '1,25p' "$logfile" | sed 's/^/    /'
}

cmd_stop() {
    local label="$1"
    need_root "stop" "$label"

    local outdir="$LOGS_DIR/_energy_${label}"
    local pidfile="$RUN_DIR/${label}.pid"
    local pid=""
    [[ -f "$pidfile" ]] && pid="$(cat "$pidfile")"

    if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
        info "SIGTERM a $pid (SIGKILL perderia el volcado)"
        kill -TERM "$pid"
        for _ in $(seq 1 30); do kill -0 "$pid" 2>/dev/null || break; sleep 1; done
        kill -0 "$pid" 2>/dev/null && die "sigue vivo tras 30s; revisa a mano"
    else
        warn "PID de $pidfile no vivo; intento por patron"
        pkill -TERM -f 'monitor_energy\.py' 2>/dev/null || true
        sleep 3
    fi
    rm -f "$pidfile" "$RUN_DIR/${label}.t0"

    local summ="$outdir/energy_summary.json"
    [[ -f "$summ" ]] || die "no se escribio $summ: el muestreador no volco"
    ok "volcado presente: $summ"

    python3 - "$summ" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
print(f"    duracion : {d.get('duration_s',0)/3600:.2f} h")
print(f"    T pico   : {d.get('peak_pkg_temp_c','?')} C")
drift = d.get('constraints_drift')
print(f"    drift PL1: {drift}"
      + ("   <-- ATENCION: limites RAPL reescritos, batch NO comparable" if drift else ""))
for k, v in (d.get('domains') or {}).items():
    print(f"    {k:16s} {v.get('energy_j',0):>10.0f} J bruta | "
          f"P_idle {v.get('p_idle_w','?')} W | P_med {v.get('mean_power_w','?')} W")
PY

    local postdir="$LOGS_DIR/_energy_${label}_post"
    info "linea base en CALIENTE (${BASELINE_S}s): cuantifica la deriva termica"
    info "solo se puede medir AHORA, antes de que la maquina se enfrie"
    mkdir -p "$postdir"
    timeout $((BASELINE_S + 60)) python3 "$MONITOR" \
        --outdir "$postdir" --baseline "$BASELINE_S" >"$RUN_DIR/${label}.post.log" 2>&1 || true
    [[ -f "$postdir/energy_summary.json" ]] \
        && ok "linea base en caliente -> $postdir" \
        || warn "sin volcado en caliente; revisa $RUN_DIR/${label}.post.log"

    echo
    ok "batch '$label' cerrado. Para el analisis:"
    info "--baseline apunta a un muestreo OCIOSO cuyo summary trae domains[*].mean_power_w;"
    info "usa el de _post (en caliente) o uno en frio dedicado, segun lo que quieras atribuir."
    cat <<EOF

  python3 $SCRIPT_DIR/monitor_analyzer.py \\
      --run $label $LOGS_DIR/SIMULATION_XXXXXXXX_XXXXXX \\
            $outdir/energy_timeseries.csv $outdir/energy_summary.json \\
      --baseline $postdir/energy_summary.json \\
      --outdir $LOGS_DIR/PLOTS/monitoring
EOF
}

# --------------------------------------------------------------------------
# watch: bloquea hasta que el batch termine y entonces hace el stop solo.
#
# Senal de fin: run_simulation.sh manda SIGTERM a monitor_resources.py al
# acabar, y ese volcado crea MONITOR/monitor_summary.json. Es la marca mas
# fiable de "batch terminado", mejor que contar CSVs de RESULTS.
#
# No es obligatorio: monitor_analyzer.py recorta la ventana de energia con
# t0_mono/duration_s, asi que un muestreador que se pase de largo no estorba.
# Lo que watch salva es la linea base EN CALIENTE, que solo vale si se toma
# justo al terminar.
# --------------------------------------------------------------------------
cmd_watch() {
    local label="$1"
    need_root "watch" "$label"

    local t0file="$RUN_DIR/${label}.t0"
    [[ -f "$t0file" ]] || die "no existe $t0file: lanza primero 'start $label'"
    local t0; t0="$(cat "$t0file")"
    local max_h="${MAX_HOURS:-8}"
    local deadline=$(( t0 + max_h * 3600 ))

    info "esperando el SIMULATION_* de este batch (limite ${max_h}h)"

    # localiza el directorio del batch por el sello del nombre, no por mtime
    local simdir=""
    while [[ -z "$simdir" ]]; do
        [[ $(date +%s) -gt $deadline ]] && die "limite de ${max_h}h sin ver ningun SIMULATION_*"
        local d name stamp
        for d in "$LOGS_DIR"/SIMULATION_*; do
            [[ -d "$d" ]] || continue
            name="$(basename "$d")"
            stamp="$(date -d "${name:11:8} ${name:20:2}:${name:22:2}:${name:24:2}" +%s 2>/dev/null || echo 0)"
            [[ "$stamp" -ge "$t0" ]] && simdir="$d"
        done
        [[ -z "$simdir" ]] && sleep 20
    done
    ok "batch en $(basename "$simdir")"

    local summ="$simdir/MONITOR/monitor_summary.json"
    local ts="$simdir/MONITOR/monitor_timeseries.csv"
    info "esperando $summ"

    local last=-1 reps
    while [[ ! -f "$summ" ]]; do
        [[ $(date +%s) -gt $deadline ]] && die "limite de ${max_h}h sin monitor_summary.json"
        if [[ -f "$ts" ]]; then
            # busca la columna por NOMBRE en la cabecera, no por posicion
            reps="$(awk -F, 'NR==1{for(i=1;i<=NF;i++) if($i=="replicas_done") c=i; next}
                             c && $c ~ /^[0-9]+$/ {v=$c} END{print v+0}' "$ts" 2>/dev/null)"
            if [[ -n "$reps" && "$reps" != "$last" ]]; then
                printf '\r    replicas: %-6s  (%s)   ' "$reps" "$(date +%H:%M)"
                last="$reps"
            fi
        fi
        sleep 30
    done
    printf '\n'
    ok "monitor_summary.json presente: batch terminado"

    info "margen de 20s para que run_simulation.sh cierre sus fases"
    sleep 20
    cmd_stop "$label"
}

cmd_status() {
    local pids; pids="$(samplers_running)"
    if [[ -n "$pids" ]]; then
        ok "muestreador activo:"; pgrep -af 'monitor_energy\.py' | sed 's/^/    /'
    else
        info "sin muestreador activo"
    fi
    if compgen -G "$RUN_DIR/*.pid" >/dev/null; then
        info "pidfiles:"
        for f in "$RUN_DIR"/*.pid; do
            printf '    %s -> PID %s' "$(basename "$f" .pid)" "$(cat "$f")"
            kill -0 "$(cat "$f")" 2>/dev/null && echo " (vivo)" || echo " (HUERFANO)"
        done
    fi
    info "directorios de energia en $LOGS_DIR:"
    find "$LOGS_DIR" -maxdepth 1 -name '_energy*' -printf '    %f\n' 2>/dev/null | sort
}

usage() {
    sed -n '2,20p' "${BASH_SOURCE[0]}" | sed 's/^# \?//'
    cat <<EOF

Ordenes:
  sudo $0 start ETIQUETA    linea base en frio + arranca el muestreo
  sudo $0 stop  ETIQUETA    volcado + linea base en caliente + resumen
  sudo $0 watch ETIQUETA    bloquea hasta que acabe el batch y hace el stop solo
       $0 status            que hay corriendo y que hay en disco

Variables:
  SKIP_GOV=1                no abortar si el governor no es performance
  MAX_HOURS=12              limite de espera de watch (por defecto 8)
EOF
}

# ---------------------------- DESPACHO ------------------------------------
case "${1:-}" in
    start)  [[ $# -eq 2 ]] || die "uso: sudo $0 start ETIQUETA"; cmd_start "$2" ;;
    stop)   [[ $# -eq 2 ]] || die "uso: sudo $0 stop ETIQUETA";  cmd_stop  "$2" ;;
    watch)  [[ $# -eq 2 ]] || die "uso: sudo $0 watch ETIQUETA"; cmd_watch "$2" ;;
    status) cmd_status ;;
    *)      usage; exit 1 ;;
esac