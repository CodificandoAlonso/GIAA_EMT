"""
Loader of the C-engine output (single RESULTS/results.csv with all replicas) and of known_data.

Columns of results.csv: simulation_id, bus_code, travels_completed, stop_num, direction (0 = toA, 1 = toB),
current_time (s since 00:00 at the stop), timeslot (slot of the visit), departure_timeslot (slot of the trip
departure), boards, residual_boards (denied), dropoffs, occupation (after the stop), time_between_stops (s from
the previous stop of the trip, 0 at the first stop).

The visits table has the same columns as AAA_TEST/sim_comparison/src/load.py (replica, bus, travel, stop, dir,
pos, time_s, slot, dep_slot, boards, denied, dropoffs, occ, tbs) plus is_first / is_last.
"""

import os
import pickle

import numpy as np
import pandas as pd

from config import CACHE, INPUTS, KNOWN, SIM, SIM_ROOT, TIMESLOTS


def stop_order() -> dict:
    lines = open(os.path.join(INPUTS, "input_stops.txt")).read().split()
    return {"toA": [int(s) for s in lines[0].split(",")], "toB": [int(s) for s in lines[1].split(",")]}


def load_visits() -> dict:
    cache = os.path.join(CACHE, "visits.pkl")
    if os.path.exists(cache):
        with open(cache, "rb") as f:
            return pickle.load(f)
    path = os.path.join(SIM_ROOT, SIM, "RESULTS", "results.csv")
    r = pd.read_csv(path)
    order = stop_order()
    n_stops = {d: len(s) for d, s in order.items()}
    pos = {(d, s): i for d in order for i, s in enumerate(order[d])}
    v = pd.DataFrame({
        "replica": r["simulation_id"].astype(int), "bus": r["bus_code"].astype(int), "travel": r["travels_completed"].astype(int),
        "stop": r["stop_num"].astype(int), "dir": np.where(r["direction"] == 0, "toA", "toB"),
        "time_s": r["current_time"].astype(float), "slot": r["timeslot"].astype(int), "dep_slot": r["departure_timeslot"].astype(int),
        "boards": r["boards"].astype(int), "denied": r["residual_boards"].astype(int), "dropoffs": r["dropoffs"].astype(int),
        "occ": r["occupation"].astype(int), "tbs": r["time_between_stops"].astype(float)})
    v["pos"] = [pos[(d, s)] for d, s in zip(v["dir"], v["stop"])]
    v = v.sort_values(["replica", "bus", "travel", "pos"]).reset_index(drop=True)
    v["is_first"] = v["pos"] == 0
    v["is_last"] = v["pos"] == v["dir"].map(n_stops) - 1
    anom = pd.read_csv(os.path.join(SIM_ROOT, SIM, "EVENTS", "anomalies.csv"))
    out = {"visits": v, "order": order, "n_events": len(anom),
           "bytes": os.path.getsize(path)}
    with open(cache, "wb") as f:
        pickle.dump(out, f, protocol=pickle.HIGHEST_PROTOCOL)
    return out


def load_known() -> dict:
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


def integrity(v: pd.DataFrame, order: dict) -> dict:
    g = v.groupby(["replica", "bus", "travel"], sort=False)
    prev = g["occ"].shift(1).fillna(0)
    delta = v["occ"] - (prev + v["boards"] - v["dropoffs"])
    trips = v.drop_duplicates(["replica", "bus", "travel"])
    return {
        "replicas": v["replica"].nunique(), "visits": len(v), "visits_per_replica": v.groupby("replica").size().agg(["min", "max"]).tolist(),
        "trips_per_replica": trips.groupby("replica").size().agg(["min", "max"]).tolist(),
        "duplicate_keys": int(v.duplicated(["replica", "bus", "travel", "stop", "dir"]).sum()),
        "missing": int(v.isna().sum().sum()),
        "conservation_violations": int((delta != 0).sum()), "lost_passengers": int(-delta[delta < 0].sum()),
        "occ_negative": int((v["occ"] < 0).sum()), "occ_above_80": int((v["occ"] > 80).sum()),
        "alight_gt_onboard": int((v["dropoffs"] > prev).sum()),
        "terminal_occ_not_zero": int((v.loc[v["is_last"], "occ"] != 0).sum()),
        "denied_while_below_capacity": int(((v["denied"] > 0) & (v["occ"] < 80)).sum()),
        "visits_at_capacity": int((v["occ"] >= 80).sum()),
        "visits_after_24h": int((v["time_s"] >= 86400).sum()),
    }
