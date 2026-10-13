"""
Analysis A - Data integrity and simulation invariants (plan section 4).

Outputs
    logs/table1_data_quality.log    Table 1: coverage, missingness, invariant violations
    logs/a2_violations_IA.csv / _AG.csv   every visit that breaks flow conservation
"""

import json
import os

import numpy as np
import pandas as pd

from config import CAPACITY, LOGS, MODELS, SIM_ROOT, SIMS
from load import load_model
from metrics import Log, save_csv


def trips_view(v: pd.DataFrame) -> pd.DataFrame:
    v = v.sort_values(["replica", "bus", "travel", "pos"]).reset_index(drop=True)
    g = v.groupby(["replica", "bus", "travel"], sort=False)
    v["prev_occ"] = g["occ"].shift()
    v["is_first"] = v["prev_occ"].isna()
    v["is_last"] = g.cumcount(ascending=False) == 0
    v["dt"] = g["time_s"].diff()
    return v


def main():
    log = Log("table1_data_quality.log", "Table 1 - Dataset coverage and quality (Analysis A)")
    log.p("AG = " + SIMS["AG"] + " (GAMA, without_agents) | IA = " + SIMS["IA"] + " (GAMA, with_agents)")
    log.p("Inputs: byte-identical includes/INPUTS in both runs; schedule final_input.json (12 buses, 82 + 81 trips).")
    sched = json.load(open(os.path.join(SIM_ROOT, SIMS["AG"], "includes", "INPUTS", "final_input.json")))
    n_trips_sched = sum(len(v) for v in sched.values())
    order = load_model("AG")["order"]
    expected_visits = sum(len(order["toA"] if s[0] == "2646" else order["toB"]) for v in sched.values() for s in v)

    rows, keysets, a2_rows, a3_rows, a4_rows = [], {}, [], [], []
    for m in MODELS:
        d = load_model(m)
        v = trips_view(d["visits"])
        w, wc, ev = d["waits"], d["wait_counts"], d["events"]

        per_rep = v.groupby("replica").agg(visits=("stop", "size"),
                                           trips=("travel", lambda s: 0))
        trips_rep = v.groupby("replica").apply(lambda g: g[["bus", "travel"]].drop_duplicates().shape[0],
                                               include_groups=False)
        keys = v[["replica", "bus", "travel", "stop", "dir"]]
        dup = int(keys.duplicated().sum())
        keysets[m] = set(map(tuple, v[["bus", "travel", "dir", "stop"]].drop_duplicates().to_numpy()))
        miss = d["visits"].isna().sum()

        # A1
        rows.append({
            "model": m,
            "replicas": v["replica"].nunique(),
            "files RESULTS/EVENTS/PASSENGERS": "/".join(str(d["files"][k]) for k in ("RESULTS", "EVENTS", "PASSENGERS")),
            "trips/replica (min-max)": f"{trips_rep.min()}-{trips_rep.max()} (sched {n_trips_sched})",
            "visits/replica (min-max)": f"{per_rep['visits'].min()}-{per_rep['visits'].max()} (exp {expected_visits})",
            "duplicate visit keys": dup,
            "missing values (visits)": int(miss.sum()),
            "visits after 24:00": int((v["time_s"] >= 24 * 3600).sum()),
        })

        # A2 flow conservation and capacity
        cons = v["occ"] == v["prev_occ"] + v["boards"] - v["dropoffs"]
        nonfirst = ~v["is_first"]
        viol = v[nonfirst & ~cons].copy()
        viol["delta"] = viol["occ"] - (viol["prev_occ"] + viol["boards"] - viol["dropoffs"])
        save_csv(viol.drop(columns=["is_first", "is_last"]), f"a2_violations_{m}.csv")
        a2_rows.append({
            "model": m,
            "visits": len(v),
            "conservation violations": len(viol),
            "% of visits": 100 * len(viol) / len(v),
            "replicas affected": viol["replica"].nunique(),
            "passengers lost (sum of negative deltas)": int(-viol.loc[viol["delta"] < 0, "delta"].sum()),
            "first-stop occ != boards": int((v["is_first"] & (v["occ"] != v["boards"])).sum()),
            "terminal occ != 0": int((v["is_last"] & (v["occ"] != 0)).sum()),
            "occ < 0": int((v["occ"] < 0).sum()),
            f"occ > {CAPACITY}": int((v["occ"] > CAPACITY).sum()),
            "alight > on board": int((nonfirst & (v["dropoffs"] > v["prev_occ"])).sum()),
            "negative counts": int((v[["boards", "denied", "dropoffs"]] < 0).to_numpy().sum()),
            "denied while occ < cap": int(((v["denied"] > 0) & (v["occ"] < CAPACITY)).sum()),
            "visits at capacity": int((v["occ"] == CAPACITY).sum()),
        })
        if len(viol):
            a2_rows[-1]["violations by stop position"] = viol["pos"].value_counts().sort_index().to_dict()

        # A3 waiting times
        j = v[["replica", "bus", "travel", "stop", "boards", "denied"]].merge(
            wc[["replica", "bus", "travel", "stop", "n_waits"]], how="left", on=["replica", "bus", "travel", "stop"])
        j["n_waits"] = j["n_waits"].fillna(0)
        hw = v.sort_values(["replica", "dir", "stop", "time_s"])[
            ["replica", "bus", "travel", "dir", "stop", "time_s", "denied"]].copy()
        gh = hw.groupby(["replica", "dir", "stop"], sort=False)
        hw["headway"] = gh["time_s"].diff()
        hw["prev_denied"] = gh["denied"].shift()
        ww = w[["replica", "bus", "travel", "stop", "wait"]].merge(
            hw[["replica", "bus", "travel", "stop", "headway", "prev_denied"]],
            on=["replica", "bus", "travel", "stop"], how="left")
        has_prev = ww["headway"].notna()
        longer = has_prev & (ww["wait"] > ww["headway"] + 1)
        inc = longer & (ww["prev_denied"] == 0)
        excess = (ww.loc[inc, "wait"] - ww.loc[inc, "headway"])
        a3_rows.append({
            "model": m,
            "waiting times": len(w),
            "negative waits": int((w["wait"] < 0).sum()),
            "missing waits": int(w["wait"].isna().sum()),
            "visits with #waits == boarded": f"{100 * (j['n_waits'] == j['boards']).mean():.3f} %",
            "wait max (s)": float(w["wait"].max()),
            "wait > 1 h": int((w["wait"] > 3600).sum()),
            "median headway at stops (s)": float(hw["headway"].median()),
            "waits longer than the time since the previous bus": f"{100 * longer[has_prev].mean():.2f} %",
            "... of which the previous bus denied boardings": f"{100 * (ww.loc[longer, 'prev_denied'] > 0).mean():.2f} %",
            "... previous bus had room (inconsistent)": int(inc.sum()),
            "inconsistent: % of all waits": f"{100 * inc.sum() / len(ww):.2f} %",
            "inconsistent: excess over headway p50/p90 (s)": f"{excess.median():.0f} / {excess.quantile(0.9):.0f}",
            "inconsistent: at bunched visits (headway < 120 s)": f"{100 * (ww.loc[inc, 'headway'] < 120).mean():.1f} %",
        })

        # A4 time consistency
        a4_rows.append({
            "model": m,
            "negative travel times": int((v["tbs"] < 0).sum()),
            "non-monotonic times in trip": int((v["dt"] < 0).sum()),
            "travel time at first stop != 0": int((v["is_first"] & (v["tbs"] != 0)).sum()),
            "slot != hour(time)": int((v["slot"] != v["time_s"] // 3600).sum()),
            "travel time vs time difference (median |diff| s)": float((v.loc[~v["is_first"], "tbs"] - v.loc[~v["is_first"], "dt"]).abs().median()),
            "DELAY events": len(ev),
            "DELAY events with delay <= 0": int((ev["delay_min"] <= 0).sum()),
            "event codes": ev["code"].value_counts().to_dict(),
        })

    log.h("A1 - Completeness and coverage")
    log.table(pd.DataFrame(rows))
    same = keysets["IA"] == keysets["AG"]
    log.p(f"Same scheduled service (bus, trip, direction, stop) in IA and AG: {same} "
          f"({len(keysets['IA'])} vs {len(keysets['AG'])} distinct visit keys). No replica failed or was excluded.")

    log.h("A2 - Passenger-flow conservation O_i = O_(i-1) + B_i - A_i, capacity and terminal rules")
    log.p("Event order (GAMA): alighting, then boarding up to capacity; occupancy is recorded after the stop.")
    log.p("B = boarded passengers ('boards' column), A = alightings ('dropoffs'), denied = 'residual_boards'.")
    log.table(pd.DataFrame(a2_rows).drop(columns=["violations by stop position"], errors="ignore").set_index("model").T.reset_index()
              .rename(columns={"index": "check"}), index=False)
    for r in a2_rows:
        if "violations by stop position" in r:
            log.p(f"{r['model']}: violations by stop position in route = {r['violations by stop position']}")
    log.p("Every violation in IA has a negative delta: occupancy falls below previous + boarded - alighted,")
    log.p("i.e. passengers leave the bus without being counted as alightings. They are spread over the day")
    log.p("(not only end of service). They are kept in all analyses (plan: violations are not removed).")

    log.h("A3 - Waiting-time consistency")
    log.table(pd.DataFrame(a3_rows).set_index("model").T.reset_index().rename(columns={"index": "check"}), index=False)
    log.p("One waiting time is recorded per boarded passenger; denied passengers have no waiting time at that visit.")
    log.p("A wait longer than the time since the previous bus at the same stop means the passenger was already")
    log.p("queueing when that bus passed. This should only happen if that bus was full (denied boardings > 0):")
    log.p("the check verifies that left-behind passengers stay in the queue and keep their accumulated wait.")
    log.p("Finding: some passengers wait longer than the time since a previous bus that still had room.")
    log.p("  AG: the excess is of the order of a dwell time (median ~30 s): stop times are recorded at departure,")
    log.p("      so passengers arriving while the previous bus was dwelling appear to have waited longer than the")
    log.p("      headway. Timing convention, not an error.")
    log.p("  IA: the excess is much larger (minutes) and concentrates on bunched buses. In the IA model a bus asks")
    log.p("      the stop to notify waiting passengers on arrival and only boards the passengers that answer that")
    log.p("      broadcast with a 'Board me' request within 3 cycles (handle_stop_response_and_boards). Passengers")
    log.p("      arriving after the broadcast, or not served when two buses are at the stop, stay in the queue even")
    log.p("      if the bus has room. This is a behavioural difference of the IA protocol that lengthens IA waits.")
    log.p("No passenger arrival timestamps are written, so waits cannot be re-derived independently.")

    log.h("A4 - Time and schedule consistency")
    log.table(pd.DataFrame(a4_rows).set_index("model").T.reset_index().rename(columns={"index": "check"}), index=False)
    log.p("'travel time' = time_between_stops of the arriving stop; 'time difference' = difference of recorded stop")
    log.p("times between consecutive stops (includes dwell at the previous stop).")
    log.p("Only delayed departures are written as DELAY events, so a mean departure delay over all trips cannot be")
    log.p("computed; Analysis B reports the number of DELAY events and their mean delay.")
    log.save()


if __name__ == "__main__":
    main()
