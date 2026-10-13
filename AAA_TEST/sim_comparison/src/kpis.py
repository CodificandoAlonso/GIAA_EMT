"""
Replica-level KPIs (plan B1, D2, D4) and per-stratum helpers.

Conventions
    - Terminal visits (last stop of each trip) are excluded from occupancy KPIs:
      everybody alights there, so occupancy is 0 by construction in both models.
    - Occupancy strata use the trip departure slot (dep_slot), as in
      data_extractor.py and known_data. Flows, waits and travel times use the
      slot of the visit (slot).
    - Waiting times belong to the visit where the passenger boards. Every stop
      code belongs to one direction except the terminals 2646/5727, where
      boarding only happens at the start of a trip, so stop -> direction is
      unique for boardings.
"""

import os
import pickle

import numpy as np
import pandas as pd

from config import CACHE, CAPACITY, CROWDING
from load import load_model


def prepared(model: str) -> dict:
    """Visits with route flags, waits with direction, events. Cached."""
    cache = os.path.join(CACHE, f"{model}_prepared.pkl")
    if os.path.exists(cache):
        with open(cache, "rb") as f:
            return pickle.load(f)
    d = load_model(model)
    v = d["visits"].sort_values(["replica", "bus", "travel", "pos"]).reset_index(drop=True)
    n_stops = {k: len(s) for k, s in d["order"].items()}
    v["is_first"] = v["pos"] == 0
    v["is_last"] = v["pos"] == v["dir"].map(n_stops) - 1
    g = v.groupby(["replica", "bus", "travel"], sort=False)
    v["trip_start"] = g["time_s"].transform("min")
    v["trip_end"] = g["time_s"].transform("max")

    stop_dir = (v.loc[v["boards"] > 0, ["stop", "dir"]].drop_duplicates()
                .set_index("stop")["dir"].to_dict())
    w = d["waits"].copy()
    w["dir"] = w["stop"].map(stop_dir)
    out = {"visits": v, "waits": w, "events": d["events"], "order": d["order"], "bytes": d["bytes"]}
    with open(cache, "wb") as f:
        pickle.dump(out, f, protocol=pickle.HIGHEST_PROTOCOL)
    return out


def _q(x, q):
    return x.quantile(q)


def replica_kpis(model: str) -> pd.DataFrame:
    cache = os.path.join(CACHE, f"{model}_kpis.pkl")
    if os.path.exists(cache):
        return pd.read_pickle(cache)
    p = prepared(model)
    v, w, ev = p["visits"], p["waits"], p["events"]
    occ = v[~v["is_last"]]
    go = occ.groupby("replica")["occ"]
    k = pd.DataFrame({
        "occ_mean": go.mean(), "occ_median": go.median(), "occ_sd": go.std(),
        "occ_p90": go.quantile(0.90), "occ_p95": go.quantile(0.95),
        "share_occ_ge40": occ.assign(x=occ["occ"] >= 40).groupby("replica")["x"].mean() * 100,
        "share_occ_ge60": occ.assign(x=occ["occ"] >= CROWDING).groupby("replica")["x"].mean() * 100,
        "share_occ_ge70": occ.assign(x=occ["occ"] >= 70).groupby("replica")["x"].mean() * 100,
        "share_at_capacity": occ.assign(x=occ["occ"] >= CAPACITY).groupby("replica")["x"].mean() * 100,
    })
    gw = w.groupby("replica")["wait"]
    k["wait_mean"] = gw.mean()
    k["wait_median"] = gw.median()
    k["wait_p90"] = gw.quantile(0.90)
    k["wait_p95"] = gw.quantile(0.95)
    k["wait_p99"] = gw.quantile(0.99)
    p95 = w["replica"].map(k["wait_p95"])
    k["wait_cvar95"] = w[w["wait"] >= p95].groupby("replica")["wait"].mean()
    k["share_wait_gt15min"] = w.assign(x=w["wait"] > 900).groupby("replica")["x"].mean() * 100

    seg = v[~v["is_first"]]
    k["travel_time_mean"] = seg.groupby("replica")["tbs"].mean()
    trips = v.drop_duplicates(["replica", "bus", "travel"])
    k["trip_duration_mean"] = (trips["trip_end"] - trips["trip_start"]).groupby(trips["replica"]).mean()

    hw = v[~v["is_last"]].sort_values(["replica", "dir", "stop", "time_s"])
    hw = hw.assign(h=hw.groupby(["replica", "dir", "stop"])["time_s"].diff()).dropna(subset=["h"])
    cv = hw.groupby(["replica", "dir", "stop"])["h"].agg(lambda x: x.std() / x.mean())
    k["headway_cv"] = cv.groupby("replica").mean()
    k["headways_under_2min_pct"] = hw.assign(x=hw["h"] < 120).groupby("replica")["x"].mean() * 100

    gv = v.groupby("replica")
    k["visits"] = gv.size()
    k["trips"] = trips.groupby("replica").size()
    k["boardings_total"] = gv["boards"].sum()
    k["alightings_total"] = gv["dropoffs"].sum()
    k["boardings_per_visit"] = k["boardings_total"] / k["visits"]
    k["alightings_per_visit"] = k["alightings_total"] / k["visits"]
    k["denied_total"] = gv["denied"].sum()
    k["visits_with_denied"] = v.assign(x=v["denied"] > 0).groupby("replica")["x"].sum()
    k["share_visits_denied"] = k["visits_with_denied"] / k["visits"] * 100
    aff = v[v["denied"] > 0].groupby("replica")["denied"]
    k["denied_per_affected_visit"] = aff.mean()
    k["denied_affected_p95"] = aff.quantile(0.95)
    tden = v.groupby(["replica", "bus", "travel"])["denied"].sum()
    k["share_trips_with_denied"] = (tden > 0).groupby("replica").mean() * 100

    ge = ev.groupby("replica")
    k["delay_events"] = ge.size().reindex(k.index, fill_value=0)
    k["delay_mean_min"] = ge["delay_min"].mean()
    k = k.sort_index()
    k.to_pickle(cache)
    return k


def stratum_sums(v: pd.DataFrame, keys, value: str, n_rep: int = 1000) -> tuple:
    """Per-replica sums and counts of `value` for every stratum: (S, N, index).

    S, N: arrays (n_rep, n_strata). Used for replica-bootstrap CIs of stratum means."""
    g = v.groupby(["replica"] + list(keys))[value].agg(["sum", "size"])
    s = g["sum"].unstack(list(range(1, len(keys) + 1)), fill_value=0)
    n = g["size"].unstack(list(range(1, len(keys) + 1)), fill_value=0)
    s = s.reindex(range(n_rep), fill_value=0)
    n = n.reindex(range(n_rep), fill_value=0).reindex(columns=s.columns, fill_value=0)
    return s.to_numpy(float), n.to_numpy(float), s.columns
