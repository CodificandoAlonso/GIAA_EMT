"""
Loading of both GAMA batch outputs and of the known_data empirical reference.

Per model, three tables (cached as pickle in sim_comparison/cache):

visits  one row per bus-stop visit
        replica, bus, travel, stop, dir, pos (stop sequence), time_s (seconds
        since 00:00 at the stop), slot (time slot of the visit), dep_slot (time
        slot of the trip departure), boards (boarded), denied (residual_boards:
        passengers that could not board), dropoffs, occ (occupancy after the
        stop), tbs (travel time from the previous stop, s)
waits   one row per boarding passenger: replica, bus, travel, stop, slot, wait (s)
events  DELAY events: replica, bus, travel, stop, dir, slot, time_s,
        sched_s (scheduled departure), delay_min

Column order of RESULTS/EVENTS/PASSENGERS is the one written by the GAMA save
statements (same as WEB_DEVEL/bash_scripts/data_extractor.py).
"""

import glob
import os
import pickle
from multiprocessing import Pool

import numpy as np
import pandas as pd

from config import CACHE, KNOWN, SIM_ROOT, SIMS, TIMESLOTS

RESULTS_COLS = ["sim", "bus", "travel", "stop", "dir", "time", "slot", "dep_slot",
                "boards", "denied", "dropoffs", "occ", "tbs"]
EVENTS_COLS = ["sim", "bus", "travel", "stop", "dir", "slot", "code", "time", "sched", "delay_min"]
PASS_COLS = ["sim", "bus", "travel", "stop", "slot", "time", "waits"]


def hms_to_s(series: pd.Series) -> np.ndarray:
    parts = series.astype(str).str.split(":", expand=True).astype(float)
    while parts.shape[1] < 3:
        parts[parts.shape[1]] = 0.0
    return (parts[0] * 3600 + parts[1] * 60 + parts[2]).to_numpy()


def stop_order(model: str) -> dict:
    path = os.path.join(SIM_ROOT, SIMS[model], "includes", "INPUTS", "input_stops.txt")
    lines = open(path).read().split()
    return {"toA": [int(s) for s in lines[0].split(",")],
            "toB": [int(s) for s in lines[1].split(",")]}


def _read_results(path):
    df = pd.read_csv(path, header=None, skiprows=1, names=RESULTS_COLS)
    return df


def _read_events(path):
    df = pd.read_csv(path, header=None, skiprows=1, names=EVENTS_COLS)
    return df


def _read_passengers(path):
    df = pd.read_csv(path, header=None, skiprows=1, names=PASS_COLS, dtype={"waits": str})
    txt = df["waits"].fillna("").str.strip("[]\"' ").str.replace(";", ",", regex=False)
    lens = np.where(txt.str.len() > 0, txt.str.count(",") + 1, 0)
    flat = np.array([float(v) for s in txt[txt.str.len() > 0] for v in s.split(",")], dtype=float)
    idx = np.repeat(np.arange(len(df)), lens)
    out = df.iloc[idx][["sim", "bus", "travel", "stop", "slot"]].reset_index(drop=True)
    out["wait"] = flat
    counts = df[["sim", "bus", "travel", "stop", "slot"]].copy()
    counts["n_waits"] = lens
    return out, counts


def _replica(series: pd.Series) -> np.ndarray:
    return series.str.replace("Simulation ", "", regex=False).astype(int).to_numpy()


def load_model(model: str, refresh: bool = False) -> dict:
    cache = os.path.join(CACHE, f"{model}.pkl")
    if os.path.exists(cache) and not refresh:
        with open(cache, "rb") as f:
            return pickle.load(f)

    base = os.path.join(SIM_ROOT, SIMS[model])
    files = {k: sorted(glob.glob(os.path.join(base, k, "log_Simulation *.csv")))
             for k in ("RESULTS", "EVENTS", "PASSENGERS")}
    with Pool(4) as p:
        res = pd.concat(p.map(_read_results, files["RESULTS"]), ignore_index=True)
        ev = pd.concat(p.map(_read_events, files["EVENTS"]), ignore_index=True)
        pw = p.map(_read_passengers, files["PASSENGERS"])
    waits = pd.concat([w for w, _ in pw], ignore_index=True)
    wcounts = pd.concat([c for _, c in pw], ignore_index=True)

    order = stop_order(model)
    pos = {(d, s): i for d in order for i, s in enumerate(order[d])}

    visits = pd.DataFrame({
        "replica": _replica(res["sim"]), "bus": res["bus"].astype(int),
        "travel": res["travel"].astype(int), "stop": res["stop"].astype(int),
        "dir": res["dir"].astype(str),
    })
    visits["pos"] = [pos[(d, s)] for d, s in zip(visits["dir"], visits["stop"])]
    visits["time_s"] = hms_to_s(res["time"])
    for c in ("slot", "dep_slot", "boards", "denied", "dropoffs", "occ"):
        visits[c] = res[c].astype(int)
    visits["tbs"] = res["tbs"].astype(float)

    waits_df = pd.DataFrame({
        "replica": _replica(waits["sim"]), "bus": waits["bus"].astype(int),
        "travel": waits["travel"].astype(int), "stop": waits["stop"].astype(int),
        "slot": waits["slot"].astype(int), "wait": waits["wait"].astype(float),
    })
    wcounts = pd.DataFrame({
        "replica": _replica(wcounts["sim"]), "bus": wcounts["bus"].astype(int),
        "travel": wcounts["travel"].astype(int), "stop": wcounts["stop"].astype(int),
        "slot": wcounts["slot"].astype(int), "n_waits": wcounts["n_waits"].astype(int),
    })

    events = pd.DataFrame({
        "replica": _replica(ev["sim"]), "bus": ev["bus"].astype(int),
        "travel": ev["travel"].astype(int), "stop": ev["stop"].astype(int),
        "dir": ev["dir"].astype(str), "slot": ev["slot"].astype(int),
        "code": ev["code"].astype(str), "time_s": hms_to_s(ev["time"]),
        "sched_s": hms_to_s(ev["sched"]), "delay_min": ev["delay_min"].astype(float),
    })

    out = {"visits": visits, "waits": waits_df, "wait_counts": wcounts, "events": events,
           "order": order,
           "files": {k: len(v) for k, v in files.items()},
           "bytes": {k: sum(os.path.getsize(f) for f in v) for k, v in files.items()}}
    with open(cache, "wb") as f:
        pickle.dump(out, f, protocol=pickle.HIGHEST_PROTOCOL)
    return out


def load_known() -> dict:
    """known_data normal parameters, long format.

    occ:   dir, stop, slot (trip departure slot), mean, std
    times: dir, seg ('A-B'), to_stop, slot, mean, std   (mean = std = 0 -> no data)
    """
    occ, times = [], []
    for d in ("toA", "toB"):
        o = pd.read_csv(os.path.join(KNOWN, f"NORMAL_OCCUPATION_{d}.csv"))
        for _, r in o.iterrows():
            for t in TIMESLOTS:
                occ.append((d, int(r["Stop"]), t, r[f"Mean_{t}"], r[f"std_{t}"]))
        tt = pd.read_csv(os.path.join(KNOWN, f"NORMAL_times_stops_{d}.csv"))
        for _, r in tt.iterrows():
            a, b = r["StopsCodes"].split("-")
            for t in TIMESLOTS:
                times.append((d, r["StopsCodes"], int(b), t, r[f"Mean_{t}"], r[f"Std_{t}"]))
    occ = pd.DataFrame(occ, columns=["dir", "stop", "slot", "mean", "std"])
    times = pd.DataFrame(times, columns=["dir", "seg", "to_stop", "slot", "mean", "std"])
    times.loc[(times["mean"] <= 0) & (times["std"] <= 0), ["mean", "std"]] = np.nan
    return {"occ": occ, "times": times}


if __name__ == "__main__":
    import time
    for m in ("AG", "IA"):
        t = time.time()
        d = load_model(m, refresh=True)
        print(m, {k: len(v) for k, v in d.items() if isinstance(v, pd.DataFrame)},
              d["files"], f"{time.time() - t:.0f}s")
    k = load_known()
    print({k_: len(v) for k_, v in k.items()})
