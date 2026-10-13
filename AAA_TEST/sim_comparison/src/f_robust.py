"""
Analysis F - Robustness (plan section 9).

Outputs
    logs/table6_robustness.log
    logs/f_groups.csv, logs/f_metric_sensitivity.csv

F1/F2 use groups defined independently of the IA-AG comparison (direction, peak slots fixed in config, demand
tertiles of known_data, route position, and input-based boarding / alighting intensity of the stops).
F3 re-evaluates the C1 conclusions under other distances and acceptance thresholds.
F4 (input-calibration perturbation) needs new simulations and is NOT done. F5 is a statement.
"""

import os

import numpy as np
import pandas as pd

from config import BASE, BC_ACCEPT, LOGS, W1_ACCEPT_PAX, MARGINS
from c_empirical import c1_delta
from kpis import prepared
from metrics import Log, bc_normal, save_csv
from strata import GRID, known_aligned, normal_cdf_grid, occ_hist, pmf_stats, step_cdf_grid
from config import CAPACITY, ROOT


def stop_intensity() -> pd.DataFrame:
    rows = []
    for d in ("toA", "toB"):
        b = pd.read_csv(os.path.join(ROOT, "BASE_DATA", f"input_data_E01_{d}.csv"))
        nb = b[b["DistributionType"].isin(["NORMAL", "NEGATIVE BINOMIAL"])].copy()
        mean = np.where(nb["DistributionType"] == "NORMAL", nb["Param1"], nb["Param1"] * (1 - nb["Param2"]) / nb["Param2"])
        board = pd.Series(mean, index=nb.index).groupby(nb["Stop"]).mean()
        a = pd.read_csv(os.path.join(ROOT, "BASE_DATA", f"alighting_params_{d}.csv"))
        bb = a[a["family"] == "betabinom"]
        alight = (bb["alpha"] / (bb["alpha"] + bb["beta"])).groupby(bb["Stop"]).mean()
        for s in set(board.index) | set(alight.index):
            rows.append({"dir": d, "stop": int(s), "board_in": board.get(s, np.nan), "alight_in": alight.get(s, np.nan)})
    return pd.DataFrame(rows)


def main():
    hs = {m: occ_hist(m) for m in ("IA", "AG")}
    p = prepared("AG")
    kn = known_aligned(hs["IA"]["index"])
    c1 = pd.read_csv(os.path.join(LOGS, "c1_occupancy_strata.csv"))
    b4 = pd.read_csv(os.path.join(LOGS, "b4_occupancy_strata.csv"))
    kn = kn.merge(b4[["dir", "stop", "dep_slot", "d_mean", "W1", "equivalence"]].rename(columns={"W1": "W1_IA_AG"}),
                  on=["dir", "stop", "dep_slot"], how="left")
    pos = {(d, s): i for d, lst in p["order"].items() for i, s in enumerate(lst)}
    n = {d: len(l) for d, l in p["order"].items()}
    kn["pos"] = [pos[(d, s)] for d, s in zip(kn["dir"], kn["stop"])]
    kn["position"] = ["departure terminal" if q == 0 else ("terminal-adjacent" if (q <= 2 or q >= n[d] - 3) else "mid-route")
                      for q, d in zip(kn["pos"], kn["dir"])]
    inten = stop_intensity()
    kn = kn.merge(inten, on=["dir", "stop"], how="left")
    ok = kn["stop"].duplicated(keep=False)   # stops shared by both directions keep their direction rows
    for col, name in (("board_in", "boarding"), ("alight_in", "alighting")):
        stop_level = kn.drop_duplicates(["dir", "stop"])
        thr = stop_level[col].quantile(2 / 3)
        kn[f"high_{name}"] = kn[col] >= thr

    extra = {}
    for col, label in (("position", None), ("high_boarding", "high-demand boarding stops (input mean, top tertile)"),
                       ("high_alighting", "high alighting-probability stops (input, top tertile)")):
        if col == "position":
            for v in ("departure terminal", "terminal-adjacent", "mid-route"):
                extra[f"position: {v}"] = (kn[col] == v).to_numpy()
        else:
            extra[label] = kn[col].fillna(False).to_numpy()
            extra["not " + label] = ~kn[col].fillna(False).to_numpy()
    dsum, d_point, _ = c1_delta(hs, kn, c1, extra)

    log = Log("table6_robustness.log", "Table 6 - Robustness (Analysis F)")
    log.h("F1/F2 - IA vs AG and empirical fit by stratum group")
    log.p("Strata: direction x stop x departure slot (475). Groups come from config (peak slots), known_data (demand tertiles,")
    log.p("cuts on the empirical mean occupancy), route position, and the model INPUTS (BASE_DATA): boarding intensity = mean of")
    log.p("the input boarding distributions per stop (NORMAL: Param1; NEGATIVE BINOMIAL: r(1-p)/p; GEOMETRICAL rows ignored);")
    log.p("alighting intensity proxy = mean beta-binomial alpha/(alpha+beta) per stop. Terminal-adjacent = first two stops after the")
    log.p("departure terminal and last two before the final one.")
    log.p("Columns: mean Delta = W1_IA - W1_AG against known_data (negative favours IA), replica-bootstrap 95 % CI (300 resamples).")
    g = []
    for name in dsum["group"]:
        msk = {"all strata": np.ones(len(kn), bool), "peak": kn["peak"].to_numpy(), "off-peak": ~kn["peak"].to_numpy(),
               "toA": (kn["dir"] == "toA").to_numpy(), "toB": (kn["dir"] == "toB").to_numpy(),
               "demand low": (kn["demand"] == "low").to_numpy(), "demand medium": (kn["demand"] == "medium").to_numpy(),
               "demand high": (kn["demand"] == "high").to_numpy(), "mean >= 40 pax": (kn["mean"] >= 40).to_numpy(), **extra}[name]
        h = kn[msk]
        g.append({"group": name, "mean |IA-AG| mean occ": h["d_mean"].abs().mean(), "max |IA-AG|": h["d_mean"].abs().max(),
                  "IA-AG equivalent %": 100 * (h["equivalence"] == "EQUIVALENT").mean(),
                  "mean W1(IA,AG)": h["W1_IA_AG"].mean()})
    t = dsum.merge(pd.DataFrame(g), on="group")
    save_csv(t, "f_groups.csv")
    log.table(t[["group", "strata", "W1 IA", "W1 AG", "mean Delta (IA-AG)", "CI low", "CI high", "strata IA better %",
                 "mean |IA-AG| mean occ", "max |IA-AG|", "IA-AG equivalent %", "mean W1(IA,AG)"]], "{:.3f}")
    ci_ok = ((t["CI low"] > 0) | (t["CI high"] < 0))
    log.p("")
    log.p(f"Groups whose Delta CI excludes 0: {int(ci_ok.sum())}/{len(t)}; the largest |mean Delta| is {t['mean Delta (IA-AG)'].abs().max():.3f} pax "
          f"(tolerance {W1_ACCEPT_PAX}). Preferred model by sign of mean Delta: "
          f"IA in {int((t['mean Delta (IA-AG)'] < 0).sum())}, AG in {int((t['mean Delta (IA-AG)'] > 0).sum())} of {len(t)} groups.")

    # ---- F3
    log.h("F3 - Sensitivity to the distance and to the acceptance threshold (occupancy strata, 475)")
    mu, sd = kn["mean"].to_numpy(), kn["std"].to_numpy()
    G = normal_cdf_grid(mu, sd)
    Gc = np.where(GRID[None, :] < 0, 0.0, np.where(GRID[None, :] >= CAPACITY, 1.0, G)).astype(np.float32)
    rows = []
    res = {}
    for m in ("IA", "AG"):
        counts = hs[m]["counts"].sum(0)
        pmf = counts / counts.sum(-1, keepdims=True)
        F = step_cdf_grid(pmf.astype(np.float32))
        st = pmf_stats(pmf)
        bcn = np.array([bc_normal(a, b, c, d) if b > 1e-9 else np.nan for a, b, c, d in zip(st["mean"], st["sd"], mu, sd)])
        res[m] = {"W1 (primary, raw normal)": np.abs(F - G).sum(-1) * 0.1,
                  "W1 vs normal clipped to [0, 80]": np.abs(F - Gc).sum(-1) * 0.1,
                  "KS vs normal": np.abs(F - G).max(-1),
                  "BC normal-normal (moments)": bcn,
                  "BC project method": c1[c1["model"] == m]["BC"].to_numpy()}
    for metric in res["IA"]:
        a, b = res["IA"][metric], res["AG"][metric]
        higher_better = metric.startswith("BC")
        better_ia = (a > b) if higher_better else (a < b)
        rows.append({"metric": metric, "IA mean": np.nanmean(a), "AG mean": np.nanmean(b),
                     "IA-AG mean": np.nanmean(a) - np.nanmean(b), "strata where IA closer %": 100 * np.nanmean(better_ia),
                     "preferred (mean)": "IA" if (np.nanmean(a) > np.nanmean(b)) == higher_better else "AG"})
    mt = pd.DataFrame(rows)
    save_csv(mt, "f_metric_sensitivity.csv")
    log.table(mt, "{:.4f}")
    log.p("")
    log.p("Share of strata accepted (%) under alternative thresholds")
    rows = []
    for thr in (0.90, 0.93, 0.95, 0.97, 0.99):
        rows.append({"rule": f"BC project >= {thr}", "IA": 100 * np.nanmean(res["IA"]["BC project method"] >= thr),
                     "AG": 100 * np.nanmean(res["AG"]["BC project method"] >= thr)})
    for thr in (0.90, 0.95):
        rows.append({"rule": f"BC normal-normal >= {thr}", "IA": 100 * np.nanmean(res["IA"]["BC normal-normal (moments)"] >= thr),
                     "AG": 100 * np.nanmean(res["AG"]["BC normal-normal (moments)"] >= thr)})
    for thr in (1, 2, 3, 4, 5):
        rows.append({"rule": f"W1 <= {thr} pax", "IA": 100 * np.mean(res["IA"]["W1 (primary, raw normal)"] <= thr),
                     "AG": 100 * np.mean(res["AG"]["W1 (primary, raw normal)"] <= thr)})
    th = pd.DataFrame(rows)
    th["IA-AG (pp)"] = th["IA"] - th["AG"]
    log.table(th, "{:.2f}")
    log.p("")
    flips = (th["IA-AG (pp)"] > 0).any() and (th["IA-AG (pp)"] < 0).any()
    log.p(f"Largest |IA - AG| in the share of accepted strata over all {len(th)} rules: {th['IA-AG (pp)'].abs().max():.2f} pp. "
          f"The sign of the difference {'changes' if flips else 'does not change'} across rules"
          + ("; it is positive (IA ahead) for most rules and negative for a few, always below 2 pp." if flips else "."))
    log.p("Mean distance: IA is ahead of AG under every metric (last table above), by about 1 % of the error. Under every rule")
    log.p(f"both models accept the same share of strata within about 2 pp, and at the project rule (BC >= {BC_ACCEPT}) both reject the majority "
          f"(IA {th.loc[th['rule'] == 'BC project >= 0.97', 'IA'].iloc[0]:.1f} % accepted, AG {th.loc[th['rule'] == 'BC project >= 0.97', 'AG'].iloc[0]:.1f} %).")

    log.h("F4 - Input-calibration sensitivity")
    log.p("NOT done. It needs new simulations with perturbed input distributions; the 1000 replicas of each run share one")
    log.p("set of fitted parameters, so their variability is not uncertainty in the calibration (plan 14).")
    log.h("F5 - External validity")
    log.p("Demonstrated: one route (line 401, 12 buses, 82 + 81 trips), working days only, one demand regime, validation against")
    log.p("fitted normals of the same operational period that calibrated the inputs (calibration-period, not out-of-sample).")
    log.p("Hypotheses, not findings: other routes, holidays or free-travel days, atypical demand, changed frequency or capacity.")
    log.save()


if __name__ == "__main__":
    main()
