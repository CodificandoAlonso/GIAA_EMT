"""
Parte 1: oferta de viajes en laborables sin gratuidad y dotacion de referencia.

Salidas en AAA_TEST/output/part1/:
    trips.csv                  un viaje por fila (sentido, salida, coche, paradas registradas...)
    daily_summary.csv          por dia: viajes por sentido, coches, primera/ultima salida, validez
    departures_per_slot.csv    salidas por franja: mediana, p25, p75 de los dias validos,
                               planificado (NEW_ANAAL_FREQ/departures.csv), dia de referencia y final_input.json
    headways_per_slot.csv      intervalo entre salidas consecutivas del mismo sentido, por franja
    monthly_summary.csv        viajes/dia y coches/dia por mes
    reference_candidates.csv   los dias validos ordenados por parecido al perfil tipico
    reference_allocation.json  dotacion de referencia en el formato de final_input.json
    *.png                      graficas del informe

Todos los laborables (L-V) se tratan como un unico tipo de dia.
"""

import json
import os

import numpy as np
import pandas as pd

from common import (COLOR, HEADER, INK, ROOT, STOPS, TIMESLOTS, flag_anomalies,
                    load_direction, outdir, setup_matplotlib)

OUT = outdir("part1")
DIRS = ("toA", "toB")
SERVICE_SLOTS = list(range(6, 23))   # franjas con servicio regular en todos los dias


# --------------------------------------------------------------------------
# 1. Tabla de viajes
# --------------------------------------------------------------------------

def build_trips() -> pd.DataFrame:
    trips = []
    for d in DIRS:
        df = flag_anomalies(load_direction(d))
        df["is_header"] = df["Stop"] == HEADER[d]
        g = df.groupby("TripId")
        t = g.agg(
            dep=("dep", "first"), date=("EventDate", "first"), slot=("TimeSlot", "first"),
            vehicle=("LogicVehicle", "first"), weekday=("Weekday", "first"),
            n_stops=("Stop", "size"), has_header=("is_header", "any"),
            first_pos=("pos", "min"), last_pos=("pos", "max"),
            first_pass=("pass_time", "min"), last_pass=("pass_time", "max"),
            anom_thr=("thr", "any"), anom_cons=("cons", "any"),
            occ_seq=("Occupation", lambda s: tuple(s)),
        ).reset_index()
        t["dir"] = d
        t["full"] = t["n_stops"] == len(STOPS[d])
        trips.append(t)
    trips = pd.concat(trips, ignore_index=True)
    trips["month"] = trips["dep"].dt.strftime("%Y-%m")
    trips["duration_min"] = (trips["last_pass"] - trips["dep"]).dt.total_seconds() / 60
    return trips.sort_values(["dir", "dep"]).reset_index(drop=True)


def mark_duplicates(trips: pd.DataFrame) -> pd.DataFrame:
    """Viajes que no son una expedicion distinta (anomalia de registro, no de conteo).

    dup_same_dep   misma salida al segundo y mismo sentido que otro viaje (otro coche):
                   el mismo servicio registrado dos veces.
    dup_restart    el mismo coche vuelve a salir en el mismo sentido < 5 min despues:
                   reinicio del viaje en el equipo embarcado.
    fragment       continuacion de un viaje partido en dos TripId: mismo coche y
                   sentido, sale < 60 min despues del anterior y empieza en una
                   parada posterior a la ultima registrada por el anterior.
    En cada grupo se conserva el registro con mas paradas (o el primer trozo).
    """
    trips = trips.copy()
    trips["dup_same_dep"] = False
    trips["dup_restart"] = False
    trips["fragment"] = False

    order = trips.sort_values(["dir", "dep", "n_stops"], ascending=[True, True, False])
    trips.loc[order.index[order.duplicated(["dir", "dep"])], "dup_same_dep"] = True

    rest = trips[~trips["dup_same_dep"]].sort_values(["dir", "vehicle", "dep"])
    gap = rest.groupby(["dir", "vehicle"])["dep"].diff().dt.total_seconds() / 60
    # De cada pareja (< 5 min), descarta el que tenga menos paradas registradas
    for idx in rest.index[gap < 5]:
        prev_idx = rest.index[rest.index.get_loc(idx) - 1]
        loser = idx if trips.at[idx, "n_stops"] <= trips.at[prev_idx, "n_stops"] else prev_idx
        trips.at[loser, "dup_restart"] = True

    rest = trips[~(trips["dup_same_dep"] | trips["dup_restart"])].sort_values(["date", "vehicle", "dep"])
    g = rest.groupby(["date", "vehicle"])
    prev_dir = g["dir"].shift()
    prev_last = g["last_pos"].shift()
    gap = g["dep"].diff().dt.total_seconds() / 60
    prev_trip = g["TripId"].shift()
    is_frag = (prev_dir == rest["dir"]) & (gap < 60) & (rest["first_pos"] > prev_last)
    trips.loc[rest.index[is_frag], "fragment"] = True
    trips["fragment_of"] = None
    trips.loc[rest.index[is_frag], "fragment_of"] = prev_trip[is_frag].values

    trips["duplicate"] = trips["dup_same_dep"] | trips["dup_restart"] | trips["fragment"]
    return trips


# --------------------------------------------------------------------------
# 2. Resumen diario y validez de los dias
# --------------------------------------------------------------------------

def daily_summary(trips: pd.DataFrame) -> pd.DataFrame:
    t = trips[~trips["duplicate"]]
    per_dir = t.groupby(["date", "dir"]).size().unstack("dir").fillna(0).astype(int)
    per_dir.columns = [f"trips_{c}" for c in per_dir.columns]
    day = per_dir.copy()
    day["trips_total"] = day.sum(axis=1)
    g = t.groupby("date")
    day["vehicles"] = g["vehicle"].nunique()
    day["first_dep"] = g["dep"].min().dt.strftime("%H:%M")
    day["last_dep"] = g["dep"].max().dt.strftime("%H:%M")
    day["weekday"] = g["weekday"].first()
    day["month"] = g["month"].first()
    day["full_trip_share"] = g["full"].mean().round(3)

    # Franjas de servicio sin ninguna salida en algun sentido -> hueco de registro
    slots = t.groupby(["date", "dir", "slot"]).size()
    empty = {}
    for date in day.index:
        n = 0
        for d in DIRS:
            for s in SERVICE_SLOTS:
                n += slots.get((date, d, s), 0) == 0
        empty[date] = n
    day["empty_service_slots"] = pd.Series(empty)

    # Dias anormalmente pobres: viajes por sentido por debajo de mediana - 3*MAD
    low = pd.Series(False, index=day.index)
    for d in DIRS:
        x = day[f"trips_{d}"]
        mad = (x - x.median()).abs().median()
        low |= x < x.median() - 3 * 1.4826 * mad
    day["low_volume"] = low
    day["valid"] = (day["empty_service_slots"] == 0) & ~day["low_volume"]
    return day.reset_index()


def slot_matrix(trips: pd.DataFrame, dates) -> pd.DataFrame:
    """Salidas por (dia, sentido, franja) -> filas = dia, columnas = (sentido, franja)."""
    t = trips[(~trips["duplicate"]) & trips["date"].isin(dates)]
    m = t.groupby(["date", "dir", "slot"]).size().unstack(["dir", "slot"]).fillna(0)
    cols = pd.MultiIndex.from_product([DIRS, TIMESLOTS])
    return m.reindex(columns=cols, fill_value=0).reindex(index=sorted(dates), fill_value=0)


def headways(trips: pd.DataFrame, dates) -> pd.DataFrame:
    """Minutos entre salidas consecutivas del mismo sentido, asignados a la franja de la segunda."""
    t = trips[(~trips["duplicate"]) & trips["date"].isin(dates)].sort_values("dep")
    t = t.assign(headway=t.groupby(["date", "dir"])["dep"].diff().dt.total_seconds() / 60)
    return t.dropna(subset=["headway"])[["date", "dir", "slot", "dep", "vehicle", "headway"]]


# --------------------------------------------------------------------------
# 3. Referencias externas
# --------------------------------------------------------------------------

def planned_per_slot() -> pd.Series:
    """Horario planificado laborable (NEW_ANAAL_FREQ/departures.csv)."""
    p = pd.read_csv(os.path.join(ROOT, "NEW_ANAAL_FREQ", "departures.csv"))
    first = p[p["stop_idx"] == 1].copy()
    first["slot"] = first["dep_time"].str[:2].astype(int)
    first["dir"] = first["stop_code"].map({HEADER[d]: d for d in DIRS})
    s = first.groupby(["dir", "slot"]).size()
    return s.reindex(pd.MultiIndex.from_product([DIRS, TIMESLOTS]), fill_value=0)


def allocation_per_slot(alloc: dict) -> pd.Series:
    rows = []
    for deps in alloc.values():
        for stop, hhmm in deps:
            d = "toA" if int(stop) == HEADER["toA"] else "toB"
            rows.append((d, int(hhmm.split(":")[0])))
    s = pd.Series(1, index=pd.MultiIndex.from_tuples(rows)).groupby(level=[0, 1]).sum()
    return s.reindex(pd.MultiIndex.from_product([DIRS, TIMESLOTS]), fill_value=0)


def allocation_for_day(trips: pd.DataFrame, date: str) -> dict:
    """Dotacion de un dia real en el formato de final_input.json."""
    t = trips[(~trips["duplicate"]) & (trips["date"] == date)].sort_values("dep")
    alloc = {}
    for veh, g in t.groupby("vehicle"):
        alloc[str(veh)] = [[str(HEADER[d]), f"{dep.hour}:{dep.minute:02d}"]
                           for d, dep in zip(g["dir"], g["dep"])]
    return dict(sorted(alloc.items()))


def apportion(m: pd.DataFrame, totals: dict) -> pd.Series:
    """Salidas enteras por (sentido, franja) que suman el total diario mediano de
    cada sentido, repartidas segun el perfil medio por franja (restos mayores)."""
    out = {}
    mean = m.mean()
    for d in DIRS:
        share = mean[d] / mean[d].sum()
        raw = share * totals[d]
        base = np.floor(raw)
        left = int(round(totals[d] - base.sum()))
        order = (raw - base).sort_values(ascending=False).index[:left]
        base[order] += 1
        for s_, v in base.items():
            out[(d, s_)] = int(v)
    return pd.Series(out)


def synthetic_allocation(trips: pd.DataFrame, valid_dates, target: pd.Series):
    """Dotacion de referencia construida con los 8 meses de dias validos.

    1. Salidas por (sentido, franja): el total diario mediano de cada sentido,
       repartido segun el perfil medio por franja de los dias validos (apportion).
    2. Minuto de cada salida dentro de la franja: cuantiles (j + 0.5) / k de las
       horas de salida reales de esa franja y sentido en todos los dias validos,
       de modo que las salidas caen donde caen de verdad (no equiespaciadas).
    3. Encadenado de coches: el coche que sale de una cabecera queda libre en la
       otra cuando llega (duracion mediana del viaje completo en esa franja, que
       ya incluye la espera en terminal: el paso por la terminal coincide con la
       siguiente salida). Asignacion voraz en orden de salida, primero el coche
       que mas lleva esperando; si no hay ninguno libre se anade uno. Sin
       posicionamientos en vacio, es la flota minima para ese horario.
    """
    t = trips[(~trips["duplicate"]) & trips["date"].isin(valid_dates)]
    minute = t["dep"].dt.hour * 60 + t["dep"].dt.minute + t["dep"].dt.second / 60

    deps = []
    for d in DIRS:
        for s in TIMESLOTS:
            k = int(round(target[(d, s)]))
            if k == 0:
                continue
            pool = minute[(t["dir"] == d) & (t["slot"] == s)].values
            q = np.quantile(pool, [(j + 0.5) / k for j in range(k)])
            mins = np.round(q).astype(int)
            for j in range(1, len(mins)):           # salidas distintas y crecientes
                mins[j] = max(mins[j], mins[j - 1] + 1)
            deps += [(int(m), d) for m in mins]
    deps.sort()

    full = t[t["full"]]
    dur = full.groupby(["dir", "slot"])["duration_min"].median()
    def duration(d, s):
        for delta in (0, -1, 1, -2, 2, -3, 3):
            if (d, s + delta) in dur.index:
                return float(dur[(d, s + delta)])
        return float(full.loc[full["dir"] == d, "duration_min"].median())

    other = {"toA": "toB", "toB": "toA"}
    waiting = {"toA": [], "toB": []}        # coches esperando en la cabecera de cada sentido
    buses = []                              # lista de [ (minuto, sentido), ... ]
    for m, d in deps:
        free = [b for b in waiting[d] if b[0] <= m]
        if free:
            bus = min(free, key=lambda b: b[0])
            waiting[d].remove(bus)
            idx = bus[1]
        else:
            idx = len(buses)
            buses.append([])
        buses[idx].append((m, d))
        waiting[other[d]].append((m + duration(d, m // 60), idx))

    alloc = {}
    for i, b in enumerate(buses):
        alloc[str(4001 + i)] = [[str(HEADER[d]), f"{m // 60}:{m % 60:02d}"] for m, d in b]
    return alloc, dur


def allocation_headways(alloc: dict) -> pd.DataFrame:
    rows = []
    for deps in alloc.values():
        for stop, hhmm in deps:
            h, mm = map(int, hhmm.split(":"))
            rows.append(("toA" if int(stop) == HEADER["toA"] else "toB", h * 60 + mm))
    df = pd.DataFrame(rows, columns=["dir", "minute"]).sort_values(["dir", "minute"])
    df["slot"] = df["minute"] // 60
    df["headway"] = df.groupby("dir")["minute"].diff()
    return df.dropna(subset=["headway"])


def chain_check(trips: pd.DataFrame, date: str) -> dict:
    """Coherencia de las cadenas de cada coche: los sentidos deberian alternarse."""
    t = trips[(~trips["duplicate"]) & (trips["date"] == date)].sort_values("dep")
    same_dir = overlaps = 0
    for _, g in t.groupby("vehicle"):
        dirs = g["dir"].tolist()
        same_dir += sum(a == b for a, b in zip(dirs, dirs[1:]))
        overlaps += int((g["dep"].iloc[1:].values < g["last_pass"].iloc[:-1].values).sum())
    return {"consecutive_same_direction": same_dir, "overlapping_trips": overlaps}


# --------------------------------------------------------------------------
# 4. Graficas
# --------------------------------------------------------------------------

def plot_daily(day: pd.DataFrame, ref_date: str, plt):
    fig, ax = plt.subplots(figsize=(11, 3.6))
    x = pd.to_datetime(day["date"])
    for d in DIRS:
        ax.plot(x, day[f"trips_{d}"], color=COLOR[d], lw=1.4, label=d)
    bad = day[~day["valid"]]
    ax.scatter(pd.to_datetime(bad["date"]), bad["trips_toA"], s=36, facecolor="none",
               edgecolor=INK["primary"], lw=1.2, zorder=5, label="día descartado")
    ax.axvline(pd.to_datetime(ref_date), color=INK["secondary"], ls="--", lw=1)
    ax.annotate("mejor día real", (pd.to_datetime(ref_date), ax.get_ylim()[1]),
                xytext=(4, -12), textcoords="offset points", color=INK["secondary"], fontsize=9)
    ax.set_ylabel("viajes / día")
    ax.set_title("Viajes registrados por día laborable (sin gratuidad)")
    ax.legend(loc="lower left", ncol=3)
    fig.savefig(os.path.join(OUT, "daily_trips.png"))
    plt.close(fig)


def plot_slots(per_slot: pd.DataFrame, plt):
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.2), sharey=True)
    for ax, d in zip(axes, DIRS):
        s = per_slot[per_slot["dir"] == d]
        ax.fill_between(s["slot"], s["p25"], s["p75"], color=COLOR[d], alpha=0.18, lw=0,
                        label="p25–p75 de los días válidos")
        ax.plot(s["slot"], s["median"], color=COLOR[d], label="mediana de los días válidos")
        ax.plot(s["slot"], s["reference_synthetic"], color=INK["primary"], lw=0, marker="o", ms=5,
                label="dotación de referencia")
        ax.plot(s["slot"], s["final_input_json"], color=INK["secondary"], lw=0, marker="x", ms=6,
                label="final_input.json actual")
        ax.plot(s["slot"], s["planned"], color=INK["secondary"], lw=1.2, ls="--", label="horario planificado")
        ax.set_title(f"{d}: salidas por franja")
        ax.set_xlabel("franja (hora de salida)")
        ax.set_xticks(TIMESLOTS[::2])
    axes[0].set_ylabel("salidas")
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=5, bbox_to_anchor=(0.5, -0.06), fontsize=9)
    fig.savefig(os.path.join(OUT, "departures_per_slot.png"))
    plt.close(fig)


def plot_headways(hw: pd.DataFrame, plt):
    fig, axes = plt.subplots(1, 2, figsize=(12, 3.8), sharey=True)
    for ax, d in zip(axes, DIRS):
        h = hw[(hw["dir"] == d) & hw["slot"].isin(TIMESLOTS)]
        data = [h.loc[h["slot"] == s, "headway"].values for s in TIMESLOTS]
        bp = ax.boxplot(data, positions=TIMESLOTS, widths=0.55, showfliers=False, patch_artist=True)
        for box in bp["boxes"]:
            box.set(facecolor=COLOR[d], alpha=0.35, edgecolor=COLOR[d])
        for part in ("whiskers", "caps", "medians"):
            for line in bp[part]:
                line.set(color=INK["secondary"], lw=1)
        ax.set_title(f"{d}: intervalo entre salidas")
        ax.set_xlabel("franja")
        ax.set_xticks(TIMESLOTS[::2])
        ax.set_xticklabels(TIMESLOTS[::2])
    axes[0].set_ylabel("minutos")
    axes[0].set_ylim(0, 60)
    fig.savefig(os.path.join(OUT, "headways_per_slot.png"))
    plt.close(fig)


def plot_monthly(monthly: pd.DataFrame, plt):
    fig, ax = plt.subplots(figsize=(8, 3.4))
    x = np.arange(len(monthly))
    ax.bar(x - 0.2, monthly["trips_toA_per_day"], 0.38, color=COLOR["toA"], label="toA")
    ax.bar(x + 0.2, monthly["trips_toB_per_day"], 0.38, color=COLOR["toB"], label="toB")
    ax.set_xticks(x)
    ax.set_xticklabels(monthly["month"], rotation=0)
    ax.set_ylabel("viajes / día (media)")
    ax.set_title("Viajes registrados por día, por mes (días válidos)")
    ax.legend(loc="upper left")
    ax.grid(axis="x", visible=False)
    fig.savefig(os.path.join(OUT, "monthly_trips.png"))
    plt.close(fig)


# --------------------------------------------------------------------------

def main():
    plt = setup_matplotlib()
    trips = mark_duplicates(build_trips())
    trips.drop(columns=["occ_seq"]).to_csv(os.path.join(OUT, "trips.csv"), index=False)

    day = daily_summary(trips)
    day.to_csv(os.path.join(OUT, "daily_summary.csv"), index=False)
    valid_dates = day.loc[day["valid"], "date"].tolist()

    # Perfil tipico = mediana de salidas por (sentido, franja) en los dias validos
    m = slot_matrix(trips, valid_dates)
    target = m.median()

    # Distancia de cada dia valido al perfil tipico (L1 sobre las 38 celdas)
    hw = headways(trips, valid_dates)
    hw_target = hw.groupby(["dir", "slot"])["headway"].median()
    hw_day = hw.groupby(["date", "dir", "slot"])["headway"].median()
    cand = pd.DataFrame(index=m.index)
    cand["l1_departures"] = (m - target).abs().sum(axis=1)
    cand["trips_total"] = m.sum(axis=1)
    cand["vehicles"] = day.set_index("date").loc[m.index, "vehicles"]
    devs = {}
    for date in m.index:
        x = hw_day.loc[date]
        devs[date] = float((x - hw_target.reindex(x.index)).abs().mean())
    cand["headway_mad_min"] = pd.Series(devs)
    veh_med = day.loc[day["valid"], "vehicles"].median()
    cand["vehicles_diff"] = (cand["vehicles"] - veh_med).abs()
    chains = {date: chain_check(trips, date) for date in m.index}
    cand["chain_breaks"] = pd.Series({k: v["consecutive_same_direction"] for k, v in chains.items()})
    cand["chain_overlaps"] = pd.Series({k: v["overlapping_trips"] for k, v in chains.items()})
    # Criterio: (1) cadenas coherentes (cada coche alterna sentido y no solapa viajes:
    # si no, falta algun viaje registrado y el simulador "teletransportaria" el coche),
    # (2) coches dentro de +-1 de la mediana, (3) minima distancia al perfil de
    # salidas por franja, (4) desempate por regularidad de intervalos.
    cand["eligible"] = ((cand["chain_breaks"] == 0) & (cand["chain_overlaps"] == 0)
                        & (cand["vehicles_diff"] <= 1))
    cand = cand.sort_values(["eligible", "l1_departures", "headway_mad_min", "vehicles_diff"],
                            ascending=[False, True, True, True])
    cand = cand.join(day.set_index("date")[["weekday", "month"]])
    cand.reset_index().rename(columns={"index": "date"}).to_csv(
        os.path.join(OUT, "reference_candidates.csv"), index=False)
    ref_date = cand.index[0]
    best_unconstrained = cand.sort_values(["l1_departures", "headway_mad_min"]).index[0]

    real_alloc = allocation_for_day(trips, ref_date)
    with open(os.path.join(OUT, "reference_real_day.json"), "w") as f:
        json.dump(real_alloc, f, indent=1)

    totals = {d: int(round(day.loc[day["valid"], f"trips_{d}"].median())) for d in DIRS}
    synth_target = apportion(m, totals)
    synth_alloc, durations = synthetic_allocation(trips, valid_dates, synth_target)
    with open(os.path.join(OUT, "reference_allocation.json"), "w") as f:
        json.dump(synth_alloc, f, indent=1)
    durations.unstack(0).round(1).to_csv(os.path.join(OUT, "trip_duration_per_slot.csv"))

    with open(os.path.join(ROOT, "BASE_DATA", "final_input.json")) as f:
        base_alloc = json.load(f)

    # Que dia real es final_input.json (mismo conjunto de salidas por coche)
    base_set = {(k, s, t) for k, v in base_alloc.items() for s, t in v}
    base_match = None
    for date in day["date"]:
        a = allocation_for_day(trips, date)
        if {(k, s, t) for k, v in a.items() for s, t in v} == base_set:
            base_match = date
            break

    per_slot = pd.DataFrame({
        "median": target,
        "p25": m.quantile(0.25),
        "p75": m.quantile(0.75),
        "mean": m.mean().round(2),
        "planned": planned_per_slot(),
        "reference_synthetic": allocation_per_slot(synth_alloc),
        "reference_real_day": allocation_per_slot(real_alloc),
        "final_input_json": allocation_per_slot(base_alloc),
    })
    per_slot.index.names = ["dir", "slot"]
    per_slot = per_slot.reset_index()
    per_slot.to_csv(os.path.join(OUT, "departures_per_slot.csv"), index=False)

    hw_stats = hw.groupby(["dir", "slot"])["headway"].describe(percentiles=[0.1, 0.5, 0.9]).round(1)
    hw_stats["synthetic_median"] = allocation_headways(synth_alloc).groupby(["dir", "slot"])["headway"].median()
    hw_stats["final_input_json_median"] = allocation_headways(base_alloc).groupby(["dir", "slot"])["headway"].median()
    hw_stats.to_csv(os.path.join(OUT, "headways_per_slot.csv"))

    vd = day[day["valid"]]
    monthly = vd.groupby("month").agg(
        days=("date", "size"),
        trips_toA_per_day=("trips_toA", "mean"),
        trips_toB_per_day=("trips_toB", "mean"),
        vehicles_per_day=("vehicles", "mean"),
    ).round(1).reset_index()
    monthly.to_csv(os.path.join(OUT, "monthly_summary.csv"), index=False)

    # Efecto de quitar los viajes con anomalias de conteo sobre la oferta
    clean = trips[~trips["duplicate"] & trips["date"].isin(valid_dates)]
    drop = clean[~(clean["anom_thr"] | clean["anom_cons"])]
    hw_drop = headways(drop.assign(duplicate=False), valid_dates)
    effect = {
        "trips_per_day_all": round(clean.groupby("date").size().median(), 1),
        "trips_per_day_without_anomalous": round(drop.groupby("date").size().median(), 1),
        "anomalous_trip_share": round(1 - len(drop) / len(clean), 4),
        "headway_p90_all_min": round(hw["headway"].quantile(0.9), 1),
        "headway_p90_without_anomalous_min": round(hw_drop["headway"].quantile(0.9), 1),
        "headways_over_30min_all": int((hw["headway"] > 30).sum()),
        "headways_over_30min_without_anomalous": int((hw_drop["headway"] > 30).sum()),
    }

    corr = vd[["trips_total", "vehicles"]].corr().iloc[0, 1]
    trips_per_vehicle = (vd["trips_total"] / vd["vehicles"]).describe().round(2).to_dict()
    weekday = vd.groupby("weekday")[["trips_toA", "trips_toB", "vehicles"]].mean().round(1)
    weekday = weekday.reindex([w for w in ["L", "M", "X", "J", "V"] if w in weekday.index])

    summary = {
        "days_total": int(len(day)),
        "days_valid": int(day["valid"].sum()),
        "days_invalid_empty_slots": int((day["empty_service_slots"] > 0).sum()),
        "days_invalid_low_volume": int(day["low_volume"].sum()),
        "trips_total": int(len(trips)),
        "duplicates_same_dep": int(trips["dup_same_dep"].sum()),
        "duplicates_restart": int(trips["dup_restart"].sum()),
        "fragments": int(trips["fragment"].sum()),
        "valid_days_trips_per_dir_median": {d: float(vd[f"trips_{d}"].median()) for d in DIRS},
        "valid_days_vehicles_median": float(vd["vehicles"].median()),
        "corr_trips_vehicles": round(float(corr), 3),
        "trips_per_vehicle_day": trips_per_vehicle,
        "planned_trips_per_dir": {d: int(planned_per_slot()[d].sum()) for d in DIRS},
        "reference_synthetic": {
            "trips": {d: int(allocation_per_slot(synth_alloc)[d].sum()) for d in DIRS},
            "vehicles": len(synth_alloc),
            "l1": float((allocation_per_slot(synth_alloc) - target).abs().sum()),
            "trips_per_vehicle": round(sum(len(v) for v in synth_alloc.values()) / len(synth_alloc), 2),
        },
        "reference_real_date": ref_date,
        "reference_real": cand.loc[ref_date].to_dict(),
        "eligible_days": int(cand["eligible"].sum()),
        "days_with_chain_breaks": int((cand["chain_breaks"] > 0).sum()),
        "best_unconstrained_date": best_unconstrained,
        "best_unconstrained": cand.loc[best_unconstrained].to_dict(),
        "reference_real_trips": {d: int(allocation_per_slot(real_alloc)[d].sum()) for d in DIRS},
        "target_trips_per_dir": {d: float(target[d].sum()) for d in DIRS},
        "final_input_json_matches_date": base_match,
        "final_input_json_trips": {d: int(allocation_per_slot(base_alloc)[d].sum()) for d in DIRS},
        "final_input_json_vehicles": len(base_alloc),
        "final_input_json_l1": float((allocation_per_slot(base_alloc) - target).abs().sum()),
        "anomalous_trip_removal_effect": effect,
        "weekday_means": weekday.to_dict(orient="index"),
    }
    with open(os.path.join(OUT, "summary.json"), "w") as f:
        json.dump(summary, f, indent=2, default=str)

    plot_daily(day, ref_date, plt)
    plot_slots(per_slot, plt)
    plot_headways(hw, plt)
    plot_monthly(monthly, plt)
    print(json.dumps(summary, indent=2, default=str))


if __name__ == "__main__":
    main()
