"""
Empirical-only analysis of the C-engine run (plan section 6, with the empirical sides of 7 and 9).

Outputs (folder logs/ and figures/)
    table1_integrity.log                 A (data integrity of this run)
    table3_empirical_validation.log      C1 occupancy, C3 travel times, C5 reporting levels
    table4_operational_risk.log          D1 exceedance vs empirical, D2 denied boardings (descriptive), D5 decisions
    table6_robustness.log                F1/F2 groups, F3 metrics and thresholds
    context_vs_gama.log                  this run next to the GAMA AG and IA runs (context only)
    c1_occupancy_strata.csv, c3_travel_strata.csv, d1_*.csv, d5_decisions.csv, f_*.csv
    figures/fig1..fig3, fig_travel_error.png
"""

import os

import numpy as np
import pandas as pd
from scipy.stats import norm, spearmanr

from config import (BC_ACCEPT, BOOTSTRAP, CAPACITY, COLOR, CROWDING, FIGS, INK, INPUTS, ISSUE_PROB, LOGS, MARGINS, PEAK_SLOTS,
                    REF_LOGS, SEED, SIM_ROOT, THRESHOLDS, TIMESLOTS, W1_ACCEPT_PAX, seq_cmap, setup_matplotlib)
from load import integrity, load_known, load_visits
from metrics import Log, bc_normal, bc_project, boot_weights, ks_vs_normal, save_csv, w1_vs_normal
from strata import GRID, known_aligned, normal_cdf_grid, occ_hist, pmf_stats, step_cdf_grid, w1_normal_from_counts

B_BOOT = 300
K = CAPACITY + 1


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------

def boot_group_means(vals_boot: np.ndarray, msk: np.ndarray):
    b = vals_boot[:, msk].mean(1)
    return np.percentile(b, 2.5), np.percentile(b, 97.5)


def emp_tail(kn, c):
    return np.ones(len(kn)) if c <= 0 else norm.sf((c - 0.5 - kn["mean"].to_numpy()) / kn["std"].to_numpy())


def stop_intensity() -> pd.DataFrame:
    rows = []
    for d in ("toA", "toB"):
        b = pd.read_csv(os.path.join(INPUTS, f"input_data_E01_{d}.csv"))
        nb = b[b["DistributionType"].isin(["NORMAL", "NEGATIVE BINOMIAL"])]
        mean = np.where(nb["DistributionType"] == "NORMAL", nb["Param1"], nb["Param1"] * (1 - nb["Param2"]) / nb["Param2"])
        board = pd.Series(mean, index=nb.index).groupby(nb["Stop"]).mean()
        a = pd.read_csv(os.path.join(INPUTS, f"alighting_params_{d}.csv"))
        bb = a[a["family"] == "betabinom"]
        alight = (bb["alpha"] / (bb["alpha"] + bb["beta"])).groupby(bb["Stop"]).mean()
        for s in set(board.index) | set(alight.index):
            rows.append({"dir": d, "stop": int(s), "board_in": board.get(s, np.nan), "alight_in": alight.get(s, np.nan)})
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------
# C1
# --------------------------------------------------------------------------

def c1_table(h, kn):
    counts = h["counts"].sum(0)
    n = counts.sum(-1)
    pmf = counts / n[:, None]
    st = pmf_stats(pmf)
    mu, sd = kn["mean"].to_numpy(), kn["std"].to_numpy()
    G = normal_cdf_grid(mu, sd)
    F = step_cdf_grid(pmf.astype(np.float32))
    t = kn[["dir", "stop", "dep_slot", "mean", "std", "peak", "demand"]].rename(columns={"mean": "emp_mean", "std": "emp_sd"}).copy()
    t["n_sim"] = n
    t["sim_mean"], t["sim_sd"] = st["mean"], st["sd"]
    t["mean_err"], t["sd_err"] = st["mean"] - mu, st["sd"] - sd
    t["median_err"] = st["median"] - mu
    t["p90_err"] = st["p90"] - (mu + norm.ppf(0.9) * sd)
    t["W1"] = np.abs(F - G).sum(-1) * 0.1
    Gc = np.where(GRID[None, :] < 0, 0.0, np.where(GRID[None, :] >= CAPACITY, 1.0, G)).astype(np.float32)
    t["W1_clipped"] = np.abs(F - Gc).sum(-1) * 0.1
    t["KS"] = np.abs(F - G).max(-1)
    k = np.arange(K)
    t["P60_sim"] = pmf[:, k >= CROWDING].sum(-1)
    t["P60_emp"] = norm.sf((CROWDING - 0.5 - mu) / sd)
    t["P60_err_pp"] = 100 * (t["P60_sim"] - t["P60_emp"])
    t["P80_sim"] = pmf[:, k >= 80].sum(-1)
    t["share_at_cap"] = t["P80_sim"]
    bc, meth, bcn = [], [], []
    for s in range(len(t)):
        x = np.repeat(k, counts[s].astype(int))
        c, m = bc_project(x, mu[s], sd[s], rng=np.random.default_rng(SEED + s))
        bc.append(c)
        meth.append(m)
        bcn.append(bc_normal(st["mean"][s], st["sd"][s], mu[s], sd[s]) if st["sd"][s] > 1e-9 else np.nan)
    t["BC"], t["BC_method"], t["BC_normal"] = bc, meth, bcn
    t["accept_BC"] = t["BC"] >= BC_ACCEPT
    t["accept_W1"] = t["W1"] <= W1_ACCEPT_PAX
    return t, G


def w1_boot(h, G):
    c = h["counts"]
    R, S, Kk = c.shape
    w = boot_weights(R, b=B_BOOT, seed=SEED + 10).astype(np.float32)
    cw = (w @ c.reshape(R, S * Kk)).reshape(B_BOOT, S, Kk)
    return w1_normal_from_counts(cw, G)


# --------------------------------------------------------------------------
# C3
# --------------------------------------------------------------------------

def c3_table(d, known_times):
    v = d["visits"]
    v = v[~v["is_first"]].copy()
    prev = {(dd, lst[i]): lst[i - 1] for dd, lst in d["order"].items() for i in range(1, len(lst))}
    v["seg"] = [f"{prev[(a, s)]}-{s}" for a, s in zip(v["dir"], v["stop"])]
    kt = known_times.dropna(subset=["mean"]).rename(columns={"mean": "emp_mean", "std": "emp_sd"}).set_index(["dir", "seg", "slot"])
    rows = []
    for key, x in v.groupby(["dir", "seg", "slot"])["tbs"]:
        if key not in kt.index:
            continue
        mu, sd = kt.loc[key, "emp_mean"], kt.loc[key, "emp_sd"]
        if sd <= 0:
            continue
        x = x.to_numpy(float)
        qs = np.quantile(x, [0.05, 0.5, 0.95])
        rows.append({"dir": key[0], "seg": key[1], "slot": key[2], "n_sim": x.size, "emp_mean": mu, "emp_sd": sd,
                     "sim_mean": x.mean(), "sim_sd": x.std(ddof=1), "mean_err": x.mean() - mu, "sd_err": x.std(ddof=1) - sd,
                     "q05_err": qs[0] - (mu + norm.ppf(0.05) * sd), "q50_err": qs[1] - mu, "q95_err": qs[2] - (mu + norm.ppf(0.95) * sd),
                     "W1": w1_vs_normal(x, mu, sd), "KS": ks_vs_normal(x, mu, sd),
                     "cover95": float(np.mean(np.abs(x - mu) <= 1.96 * sd)), "negative_support_mass": float(norm.cdf(0, mu, sd))})
    return pd.DataFrame(rows), v


def c3_mae_ci(v, t):
    keys = ["dir", "seg", "slot"]
    tt = t.set_index(keys)
    g = v.groupby(["replica"] + keys)["tbs"].agg(["sum", "size"])
    ssum = g["sum"].unstack(keys, fill_value=0).reindex(range(1000), fill_value=0)
    scnt = g["size"].unstack(keys, fill_value=0).reindex(range(1000), fill_value=0)
    cols = [c for c in ssum.columns if c in tt.index]
    ssum, scnt = ssum[cols].to_numpy(float), scnt[cols].to_numpy(float)
    mu = tt.loc[cols, "emp_mean"].to_numpy()
    w = boot_weights(1000, b=B_BOOT, seed=SEED + 20)
    with np.errstate(invalid="ignore", divide="ignore"):
        boot = (w @ ssum) / (w @ scnt)
    mae = np.nanmean(np.abs(boot - mu), axis=1)
    point = np.nanmean(np.abs(ssum.sum(0) / scnt.sum(0) - mu))
    # |.| is convex, so percentile/basic intervals of the resampled MAE are biased: centre on the point estimate, use the bootstrap SE
    return point, point - 1.96 * mae.std(ddof=1), point + 1.96 * mae.std(ddof=1)


# --------------------------------------------------------------------------
# Figures
# --------------------------------------------------------------------------

def fig1(h, kn, t, plt):
    keys = [("toA", 2539, 7), ("toA", 2539, 13), ("toB", 1167, 18), ("toB", 1167, 12), ("toA", 4188, 8), ("toB", 3929, 22)]
    idx = {(d, s, ts): i for i, (d, s, ts) in enumerate(zip(kn["dir"], kn["stop"], kn["dep_slot"]))}
    fig, axes = plt.subplots(2, 3, figsize=(13, 6.6))
    x = np.arange(K)
    for ax, key in zip(axes.flat, keys):
        i = idx[key]
        mu, sd = kn["mean"].iloc[i], kn["std"].iloc[i]
        pe = np.diff(norm.cdf(np.append(x - 0.5, CAPACITY + 0.5), mu, sd))
        ax.fill_between(x, pe, color=INK["primary"], alpha=0.15, lw=0, label="empirical N(mu, sigma)")
        ax.plot(x, pe, color=INK["primary"], lw=1.2)
        c = h["counts"].sum(0)[i]
        ax.plot(x, c / c.sum(), color=COLOR["C"], lw=1.6, label="C engine")
        ax.set_title(f"{key[0]} stop {key[1]}, slot {key[2]} ({'peak' if key[2] in PEAK_SLOTS else 'off-peak'})\nW1 = {t['W1'].iloc[i]:.2f} pax", fontsize=9)
        ax.set_xlabel("occupancy after the stop (pax)")
        ax.set_xlim(0, CAPACITY)
    axes[0, 0].legend(fontsize=8)
    fig.suptitle("Figure 1 - Occupancy distributions: empirical normal and C-engine run")
    fig.tight_layout()
    fig.savefig(os.path.join(FIGS, "fig1_occupancy_distributions.png"))
    plt.close(fig)


def fig2(t, order, plt):
    fig, axes = plt.subplots(2, 2, figsize=(11, 8.2), gridspec_kw={"width_ratios": [1, 1]})
    vmax = float(max(t["W1"].quantile(0.99), 1.0))
    from matplotlib.colors import TwoSlopeNorm
    for r, d in enumerate(("toA", "toB")):
        stops = order[d][:-1]
        h = t[t["dir"] == d]
        for c, (val, title, cmap, norm_) in enumerate((("W1", f"{d}: W1 vs empirical (pax)", seq_cmap(), None),
                                                       ("mean_err", f"{d}: mean occupancy sim - empirical (pax)", "RdBu_r", "div"))):
            mat = h.pivot(index="stop", columns="dep_slot", values=val).reindex(index=stops, columns=TIMESLOTS)
            lim = max(1.0, float(h["mean_err"].abs().quantile(0.99)))
            kw = dict(vmin=0, vmax=vmax) if norm_ is None else dict(norm=TwoSlopeNorm(0, -lim, lim))
            ax = axes[r, c]
            im = ax.imshow(mat.values, aspect="auto", cmap=cmap, **kw)
            ax.set_title(title, fontsize=10)
            ax.set_yticks(range(len(stops)))
            ax.set_yticklabels(stops, fontsize=7)
            ax.set_xticks(range(0, len(TIMESLOTS), 2))
            ax.set_xticklabels(TIMESLOTS[::2], fontsize=8)
            ax.grid(False)
            ax.set_xlabel("trip departure slot")
            fig.colorbar(im, ax=ax, shrink=0.8)
    fig.suptitle("Figure 2 - Empirical error map by stop and slot (C-engine run)")
    fig.tight_layout()
    fig.savefig(os.path.join(FIGS, "fig2_error_map.png"))
    plt.close(fig)


def fig3(curves, plt):
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.4), sharey=True)
    for ax, scope in zip(axes, ("global", "peak", "off-peak")):
        g = curves[curves["scope"] == scope]
        ax.plot(g["c"], g["EMP"], color=COLOR["EMP"], ls="--", label="empirical normal")
        ax.plot(g["c"], g["C"], color=COLOR["C"], label="C engine")
        ax.fill_between(g["c"], g["C_lo"], g["C_hi"], color=COLOR["C"], alpha=0.2, lw=0)
        ax.set_yscale("log")
        ax.set_ylim(1e-4, 1.2)
        ax.axvline(CROWDING, color=INK["secondary"], lw=0.8, ls=":")
        ax.set_title(scope)
        ax.set_xlabel("threshold c (pax)")
    axes[0].set_ylabel("P(O >= c)  (log scale)")
    axes[0].legend()
    fig.suptitle("Figure 3 - Occupancy exceedance curves (band = 95 % replica-bootstrap CI)")
    fig.tight_layout()
    fig.savefig(os.path.join(FIGS, "fig3_exceedance_curves.png"))
    plt.close(fig)


# --------------------------------------------------------------------------

def main():
    plt = setup_matplotlib()
    d = load_visits()
    h = occ_hist()
    kn = known_aligned(h["index"])
    pos = {(dd, s): i for dd, lst in d["order"].items() for i, s in enumerate(lst)}
    n = {dd: len(l) for dd, l in d["order"].items()}
    kn["pos"] = [pos[(a, s)] for a, s in zip(kn["dir"], kn["stop"])]
    kn["position"] = ["departure terminal" if q == 0 else ("terminal-adjacent" if (q <= 2 or q >= n[a] - 3) else "mid-route") for q, a in zip(kn["pos"], kn["dir"])]
    kn = kn.merge(stop_intensity(), on=["dir", "stop"], how="left")
    sl = kn.drop_duplicates(["dir", "stop"])
    kn["high_boarding"] = kn["board_in"] >= sl["board_in"].quantile(2 / 3)
    kn["high_alighting"] = kn["alight_in"] >= sl["alight_in"].quantile(2 / 3)

    # ---- A
    log = Log("table1_integrity.log", "Table 1 - Data integrity of the C-engine run (Analysis A)")
    ig = integrity(d["visits"], d["order"])
    log.h("A1/A2 - Completeness, coverage and flow conservation")
    log.p("Event order as in GAMA: alighting, then boarding up to capacity; occupancy is recorded after the stop.")
    log.table(pd.DataFrame({"check": list(ig), "value": [str(v) for v in ig.values()]}))
    log.p("")
    log.p(f"Anomaly events (EVENTS/anomalies.csv): {d['n_events']} rows over 1000 replicas.")
    log.p(f"Schedule: {ig['trips_per_replica'][1]} trips per replica; the GAMA runs of AAA_TEST/sim_comparison use 163 trips.")
    for f in ("input_stops.txt", "input_data_E01_toA.csv", "input_data_E01_toB.csv", "alighting_params_toA.csv", "alighting_params_toB.csv",
              "input_times_stops_toA.csv", "input_times_stops_toB.csv", "final_input.json"):
        ref = os.path.join(SIM_ROOT, "SIMULATION_20261012_170524", "includes", "INPUTS", f)
        mine = os.path.join(INPUTS, f)
        same = os.path.exists(ref) and os.path.exists(mine) and open(ref, "rb").read() == open(mine, "rb").read()
        log.p(f"  {f}: {'identical' if same else 'DIFFERENT or missing'} to the GAMA runs' input")
    log.save()

    # ---- C1
    t, G = c1_table(h, kn)
    save_csv(t, "c1_occupancy_strata.csv")
    boot = w1_boot(h, G)
    log = Log("table3_empirical_validation.log", "Table 3 - Empirical validation against known_data, C-engine run (Analysis C)")
    log.p("Calibration-period validation: the reference is a fitted normal of the same operational records that calibrate the inputs.")
    log.h("C1 - Occupancy by direction x stop x trip-departure slot (475 strata, terminal visits excluded)")
    log.p("W1 against the untruncated N(mu, sigma), in passengers, from CDFs on a 0.1 pax grid. BC = project method, accepted if")
    log.p(f">= {BC_ACCEPT}; W1 accepted if <= {W1_ACCEPT_PAX} pax. P60 error = P_sim(O >= 60) - P_emp(O >= 60) in percentage points.")
    fail = t[~t["accept_BC"]]
    summ = {"strata": len(t), "mean |mean err| (pax)": t["mean_err"].abs().mean(), "mean err (signed)": t["mean_err"].mean(),
            "max |mean err|": t["mean_err"].abs().max(), "mean SD err": t["sd_err"].mean(), "mean |SD err|": t["sd_err"].abs().mean(),
            "mean |median err|": t["median_err"].abs().mean(), "mean |p90 err|": t["p90_err"].abs().mean(),
            "W1 median": t["W1"].median(), "W1 p90": t["W1"].quantile(0.9), "W1 max": t["W1"].max(),
            "BC median": t["BC"].median(), "BC min": t["BC"].min(), "accepted BC %": 100 * t["accept_BC"].mean(),
            "accepted W1 %": 100 * t["accept_W1"].mean(), "failing strata (BC)": len(fail), "W1 mean in failing": fail["W1"].mean(),
            "mean |P60 err| pp": t["P60_err_pp"].abs().mean(), "max |P60 err| pp": t["P60_err_pp"].abs().max()}
    log.table(pd.DataFrame({"metric": list(summ), "C engine": list(summ.values())}), "{:.3f}")
    lo, hi = boot_group_means(boot, np.ones(len(t), bool))
    log.p("")
    log.p(f"Mean W1 over strata: {t['W1'].mean():.3f} pax, 95 % replica-bootstrap CI [{lo:.3f}, {hi:.3f}] (tolerance {W1_ACCEPT_PAX}).")
    log.p("")
    log.p("Acceptance method: " + str(t["BC_method"].value_counts().to_dict()))
    log.p("")
    log.p("10 strata with the largest W1")
    log.table(t.nlargest(10, "W1")[["dir", "stop", "dep_slot", "emp_mean", "emp_sd", "sim_mean", "sim_sd", "W1", "BC", "BC_method", "P60_err_pp"]], "{:.3f}")
    log.p("")
    log.p("Mean error (sim - emp) and W1 by trip-departure slot")
    log.table(t.groupby("dep_slot").agg(emp_mean=("emp_mean", "mean"), sim_mean=("sim_mean", "mean"), mean_err=("mean_err", "mean"), W1=("W1", "mean"),
                                        accepted_BC_pct=("accept_BC", lambda s: 100 * s.mean())).reset_index(), "{:.2f}")
    log.p("")
    log.p("Mean error and W1 by stop (route order)")
    st = t.groupby(["dir", "stop"], sort=False).agg(emp_mean=("emp_mean", "mean"), sim_mean=("sim_mean", "mean"), mean_err=("mean_err", "mean"),
                                                   W1=("W1", "mean")).reset_index()
    log.table(st, "{:.2f}")
    log.p("")
    log.p("Share of visits at capacity (O = 80), by slot group")
    log.table(pd.DataFrame({"scope": ["global", "peak", "off-peak"],
                            "simulated P(O = 80) %": [100 * t["P80_sim"].mean(), 100 * t.loc[t["peak"], "P80_sim"].mean(), 100 * t.loc[~t["peak"], "P80_sim"].mean()],
                            "empirical P(X >= 79.5) %": [100 * norm.sf((79.5 - t["emp_mean"]) / t["emp_sd"]).mean(),
                                                         100 * norm.sf((79.5 - t.loc[t["peak"], "emp_mean"]) / t.loc[t["peak"], "emp_sd"]).mean(),
                                                         100 * norm.sf((79.5 - t.loc[~t["peak"], "emp_mean"]) / t.loc[~t["peak"], "emp_sd"]).mean()]}), "{:.3f}")
    log.p("(unweighted mean over strata)")

    # C3
    kt = load_known()["times"]
    t3, v3 = c3_table(d, kt)
    save_csv(t3, "c3_travel_strata.csv")
    point, lo3, hi3 = c3_mae_ci(v3, t3)
    log.h("C3 - Segment travel times by segment x slot of the visit")
    log.p("The simulator draws times from the same fitted normals that known_data holds, so this validates the sampling and calibration")
    log.p("procedure, not an independently learned traffic model.")
    s3 = {"strata": len(t3), "MAE (s)": point, "MAE 95% CI": f"[{lo3:.2f}, {hi3:.2f}]", "mean err (s)": t3["mean_err"].mean(),
          "mean |sd err| (s)": t3["sd_err"].abs().mean(), "mean |q05 err|": t3["q05_err"].abs().mean(), "mean |q50 err|": t3["q50_err"].abs().mean(),
          "mean |q95 err|": t3["q95_err"].abs().mean(), "W1 median": t3["W1"].median(), "W1 p90": t3["W1"].quantile(0.9), "W1 max": t3["W1"].max(),
          "cover95 mean": t3["cover95"].mean(), "cover95 min": t3["cover95"].min(), "strata |mean err| > 10 s": int((t3["mean_err"].abs() > 10).sum())}
    log.table(pd.DataFrame({"metric": list(s3), "C engine": [f"{v:.3f}" if isinstance(v, float) else str(v) for v in s3.values()]}))
    log.p("")
    log.p("10 segment x slot strata with the largest W1")
    log.table(t3.nlargest(10, "W1")[["dir", "seg", "slot", "n_sim", "emp_mean", "emp_sd", "sim_mean", "sim_sd", "mean_err", "W1", "cover95"]], "{:.3f}")
    log.p("")
    log.p("Mean error (sim - emp, s) by slot")
    log.table(t3.groupby("slot")["mean_err"].mean().reset_index(), "{:.2f}")

    # C4 / C2
    log.h("C2 and C4 - Boardings, alightings and waiting times")
    log.p("known_data has no reference for boardings, alightings or waiting times: not validated. Alightings are an imposed calibrated input.")

    # C5
    log.h("C5 - Reporting levels (occupancy, W1 against known_data)")
    levels = {"global (all strata)": np.ones(len(t), bool), "excl. terminals 2646/5727 (pipeline convention)": ~t["stop"].isin([2646, 5727]).to_numpy(),
              "peak slots": t["peak"].to_numpy(), "off-peak": ~t["peak"].to_numpy(), "high-demand tertile": (t["demand"] == "high").to_numpy(),
              "strata with mean >= 40 pax": (t["emp_mean"] >= 40).to_numpy()}
    rows = []
    for name, m in levels.items():
        g = t[m]
        lo_, hi_ = boot_group_means(boot, m)
        rows.append({"level": name, "strata": len(g), "W1 mean": g["W1"].mean(), "W1 95% CI": f"[{lo_:.2f}, {hi_:.2f}]", "W1 max": g["W1"].max(),
                     "BC min": g["BC"].min(), "accepted BC %": 100 * g["accept_BC"].mean(), "accepted W1 %": 100 * g["accept_W1"].mean(),
                     "mean |mean err|": g["mean_err"].abs().mean(), "mean |P60 err| pp": g["P60_err_pp"].abs().mean()})
    log.table(pd.DataFrame(rows), "{:.3f}")
    log.save()
    fig1(h, kn, t, plt)
    fig2(t, d["order"], plt)
    c3_fig(t3, plt)

    # ---- D
    log = Log("table4_operational_risk.log", "Table 4 - Operational risk against the empirical reference, C-engine run (Analysis D)")
    nvis = h["counts"].sum(-1).sum(0)
    w = boot_weights(1000, b=B_BOOT, seed=SEED + 30)
    peak = kn["peak"].to_numpy()
    curves, rows = [], []
    for scope, msk in (("global", np.ones(len(kn), bool)), ("peak", peak), ("off-peak", ~peak)):
        cr = h["counts"][:, msk, :].sum(1)
        tail = np.cumsum(cr[:, ::-1], -1)[:, ::-1]
        den = cr.sum(-1, keepdims=True) * np.ones((1, K))
        with np.errstate(invalid="ignore", divide="ignore"):
            bt = (w @ tail) / (w @ den)
        pt = tail.sum(0) / den.sum(0)
        ew = nvis[msk] / nvis[msk].sum()
        emp = np.array([(ew * emp_tail(kn[msk], c)).sum() for c in range(K)])
        lo_, hi_ = np.percentile(bt, 2.5, 0), np.percentile(bt, 97.5, 0)
        curves.append(pd.DataFrame({"scope": scope, "c": np.arange(K), "EMP": emp, "C": pt, "C_lo": lo_, "C_hi": hi_}))
        for c in THRESHOLDS:
            rows.append({"scope": scope, "c": c, "empirical %": 100 * emp[c], "C engine %": 100 * pt[c], "95% CI": f"[{100 * lo_[c]:.2f}, {100 * hi_[c]:.2f}]",
                         "sim - emp (pp)": 100 * (pt[c] - emp[c]), "CI excludes empirical": bool(emp[c] < lo_[c] or emp[c] > hi_[c])})
    curves = pd.concat(curves, ignore_index=True)
    save_csv(curves, "d1_exceedance_curves.csv")
    log.h("D1 - Occupancy exceedance P(O >= c), % of bus-stop visits (terminal visits excluded)")
    log.p("Empirical: known_data normals mixed with the simulated visit weights; P_emp(O >= c) = P(X >= c - 0.5). For c = 80 the empirical value is")
    log.p("the probability that observed load reaches or exceeds capacity (demand); simulated O = 80 means a full bus (occupancy is capped).")
    log.table(pd.DataFrame(rows), "{:.3f}")
    ss = []
    for c in (60, 70, 80):
        row = kn[["dir", "stop", "dep_slot", "peak", "demand"]].copy()
        row["c"] = c
        row["P_emp"] = emp_tail(kn, c)
        num = h["counts"][:, :, c:].sum(-1).astype(float)
        den = h["counts"].sum(-1).astype(float)
        with np.errstate(invalid="ignore", divide="ignore"):
            bt = (w @ num) / (w @ den)
        row["P_C"] = num.sum(0) / den.sum(0)
        row["P_C_lo"], row["P_C_hi"] = np.nanpercentile(bt, 2.5, 0), np.nanpercentile(bt, 97.5, 0)
        ss.append(row)
    ss = pd.concat(ss, ignore_index=True)
    save_csv(ss, "d1_exceedance_strata.csv")
    log.p("")
    log.p("Stratified absolute error of P(O >= c) against the empirical normal (475 strata), pp")
    rows = []
    for c in (60, 70, 80):
        g = ss[ss["c"] == c]
        e = 100 * (g["P_C"] - g["P_emp"]).abs()
        rows.append({"c": c, "mean |err| pp": e.mean(), "p90 |err|": e.quantile(0.9), "max |err|": e.max(), "strata |err| > 5 pp": int((e > 5).sum()),
                     "strata |err| > 10 pp": int((e > 10).sum()), "sim CI excludes emp %": 100 * ((g["P_emp"] < g["P_C_lo"]) | (g["P_emp"] > g["P_C_hi"])).mean()})
    log.table(pd.DataFrame(rows), "{:.3f}")

    v = d["visits"]
    vn = v[~v["is_last"]]
    perrep = vn.groupby("replica").agg(visits_denied=("denied", lambda x: int((x > 0).sum())), denied=("denied", "sum"))
    log.h("D2 - Denied boardings (descriptive: no empirical reference)")
    log.table(pd.DataFrame({"measure": ["visits with denied boarding per day", "denied passengers per day", "share of visits with denied boarding %", "share of visits at capacity %"],
                            "mean": [perrep["visits_denied"].mean(), perrep["denied"].mean(), 100 * (vn["denied"] > 0).mean(), 100 * (vn["occ"] >= 80).mean()],
                            "p5": [perrep["visits_denied"].quantile(.05), perrep["denied"].quantile(.05), np.nan, np.nan],
                            "p95": [perrep["visits_denied"].quantile(.95), perrep["denied"].quantile(.95), np.nan, np.nan]}), "{:.2f}")
    g = vn.groupby(["dir", "stop", "slot"]).agg(visits=("denied", "size"), share=("denied", lambda x: (x > 0).mean()), denied=("denied", "sum")).reset_index()
    g["denied_per_day"] = g["denied"] / 1000
    log.p("")
    log.p("Worst direction x stop x slot cells by denied passengers per day")
    log.table(g.nlargest(8, "denied_per_day")[["dir", "stop", "slot", "visits", "share", "denied_per_day"]], "{:.4f}")

    log.h(f"D5 - Decision against the empirical reference: issue if P(O >= {CROWDING}) >= {ISSUE_PROB} per stratum")
    g6 = ss[ss["c"] == CROWDING].reset_index(drop=True).copy()
    g6["flag_EMP"] = g6["P_emp"] >= ISSUE_PROB
    g6["flag_C"] = g6["P_C"] >= ISSUE_PROB
    g6["unc_C"] = (g6["P_C_lo"] < ISSUE_PROB) & (g6["P_C_hi"] >= ISSUE_PROB)
    save_csv(g6, "d5_decisions.csv")
    a, b = g6["flag_EMP"], g6["flag_C"]
    pe = a.mean() * b.mean() + (1 - a.mean()) * (1 - b.mean())
    top = lambda s, k: set(s.nlargest(k).index)
    log.table(pd.DataFrame([{"flagged empirical": int(a.sum()), "flagged C engine": int(b.sum()), "agreement %": 100 * (a == b).mean(),
                             "kappa": ((a == b).mean() - pe) / (1 - pe), "false negatives": int((a & ~b).sum()), "false positives": int((~a & b).sum()),
                             "Spearman rho (P60)": spearmanr(g6["P_emp"], g6["P_C"])[0], "top-10 overlap": len(top(g6["P_emp"], 10) & top(g6["P_C"], 10)),
                             "top-20 overlap": len(top(g6["P_emp"], 20) & top(g6["P_C"], 20)), "CI straddles rule": int(g6["unc_C"].sum())}]), "{:.3f}")
    log.p("False negatives by departure slot: " + str(g6[a & ~b]["dep_slot"].value_counts().sort_index().to_dict()))
    log.p("False positives by departure slot: " + str(g6[~a & b]["dep_slot"].value_counts().sort_index().to_dict()))
    log.save()
    fig3(curves, plt)

    # ---- F
    log = Log("table6_robustness.log", "Table 6 - Robustness of the empirical fit, C-engine run (Analysis F)")
    log.h("F1/F2 - Empirical fit by stratum group")
    log.p("Groups come from config (peak slots), known_data (demand tertiles of the empirical mean), route position and the model INPUTS")
    log.p("(boarding intensity = mean of the input boarding distributions per stop; alighting proxy = mean beta-binomial alpha/(alpha+beta)).")
    groups = {"all strata": np.ones(len(kn), bool), "peak": peak, "off-peak": ~peak, "toA": (kn["dir"] == "toA").to_numpy(), "toB": (kn["dir"] == "toB").to_numpy(),
              "demand low": (kn["demand"] == "low").to_numpy(), "demand medium": (kn["demand"] == "medium").to_numpy(), "demand high": (kn["demand"] == "high").to_numpy(),
              "mean >= 40 pax": (kn["mean"] >= 40).to_numpy()}
    for pz in ("departure terminal", "terminal-adjacent", "mid-route"):
        groups[f"position: {pz}"] = (kn["position"] == pz).to_numpy()
    groups["high-demand boarding stops"] = kn["high_boarding"].fillna(False).to_numpy()
    groups["other boarding stops"] = ~kn["high_boarding"].fillna(False).to_numpy()
    groups["high alighting-probability stops"] = kn["high_alighting"].fillna(False).to_numpy()
    groups["other alighting stops"] = ~kn["high_alighting"].fillna(False).to_numpy()
    rows = []
    for name, m in groups.items():
        gg = t[m]
        lo_, hi_ = boot_group_means(boot, m)
        rows.append({"group": name, "strata": int(m.sum()), "W1 mean": gg["W1"].mean(), "W1 95% CI": f"[{lo_:.2f}, {hi_:.2f}]", "mean err (signed)": gg["mean_err"].mean(),
                     "mean |mean err|": gg["mean_err"].abs().mean(), "accepted BC %": 100 * gg["accept_BC"].mean(), "accepted W1 %": 100 * gg["accept_W1"].mean(),
                     "mean P60 err pp (signed)": gg["P60_err_pp"].mean()})
    fg = pd.DataFrame(rows)
    save_csv(fg, "f_groups.csv")
    log.table(fg, "{:.3f}")

    log.h("F3 - Sensitivity to the distance and to the acceptance threshold")
    res = {"W1 (primary, raw normal)": t["W1"], "W1 vs normal clipped to [0, 80]": t["W1_clipped"], "KS vs normal": t["KS"],
           "BC normal-normal (moments)": t["BC_normal"], "BC project method": t["BC"]}
    mt = pd.DataFrame([{"metric": k, "mean": v.mean(), "median": v.median(), "worst stratum": v.min() if k.startswith("BC") else v.max()} for k, v in res.items()])
    save_csv(mt, "f_metric_sensitivity.csv")
    log.table(mt, "{:.4f}")
    log.p("")
    log.p("Share of strata accepted (%) under alternative thresholds")
    rows = [{"rule": f"BC project >= {x}", "accepted %": 100 * (t["BC"] >= x).mean()} for x in (0.90, 0.93, 0.95, 0.97, 0.99)]
    rows += [{"rule": f"BC normal-normal >= {x}", "accepted %": 100 * (t["BC_normal"] >= x).mean()} for x in (0.90, 0.95)]
    rows += [{"rule": f"W1 <= {x} pax", "accepted %": 100 * (t["W1"] <= x).mean()} for x in (1, 2, 3, 4, 5)]
    log.table(pd.DataFrame(rows), "{:.2f}")
    log.h("F4 / F5")
    log.p("F4 (perturbation of the input calibration) needs new simulations: not done. F5: one route, working days, calibration-period validation only.")
    log.save()

    # ---- context
    log = Log("context_vs_gama.log", "Context - this run next to the GAMA AG and IA runs (AAA_TEST/sim_comparison)")
    log.p(f"Different engine; schedule {ig['trips_per_replica'][1]} trips against 163 in the GAMA runs (see table1_integrity.log for the input comparison).")
    log.p("Values for AG and IA are read from AAA_TEST/sim_comparison/logs/c1_occupancy_strata.csv.")
    ref = pd.read_csv(os.path.join(REF_LOGS, "c1_occupancy_strata.csv"))
    rows = []
    for name, df in (("C engine", t), ("AG (GAMA)", ref[ref["model"] == "AG"]), ("IA (GAMA)", ref[ref["model"] == "IA"])):
        rows.append({"run": name, "strata": len(df), "W1 mean": df["W1"].mean(), "W1 median": df["W1"].median(), "mean |mean err|": df["mean_err"].abs().mean(),
                     "mean err (signed)": df["mean_err"].mean(), "mean SD err": df["sd_err"].mean(), "accepted BC %": 100 * df["accept_BC"].mean(),
                     "accepted W1 %": 100 * df["accept_W1"].mean(), "mean |P60 err| pp": df["P60_err_pp"].abs().mean(),
                     "mean P60 err pp (signed)": df["P60_err_pp"].mean()})
    log.table(pd.DataFrame(rows), "{:.3f}")
    rc = pd.read_csv(os.path.join(REF_LOGS, "d1_exceedance_curves.csv"))
    rows = []
    for scope in ("global", "peak"):
        for c in THRESHOLDS:
            r_ = rc[(rc["scope"] == scope) & (rc["c"] == c)].iloc[0]
            cc = curves[(curves["scope"] == scope) & (curves["c"] == c)].iloc[0]
            rows.append({"scope": scope, "c": c, "empirical % (GAMA weights)": 100 * r_["EMP"], "empirical % (C weights)": 100 * cc["EMP"], "C engine %": 100 * cc["C"],
                         "AG %": 100 * r_["AG"], "IA %": 100 * r_["IA"]})
    log.p("")
    log.p("P(O >= c) in % of visits")
    log.table(pd.DataFrame(rows), "{:.3f}")
    tg = pd.read_csv(os.path.join(REF_LOGS, "c3_travel_strata.csv"))
    rows = [{"run": "C engine", "strata": len(t3), "mean err (s)": t3["mean_err"].mean(), "mean |sd err|": t3["sd_err"].abs().mean(), "cover95 mean": t3["cover95"].mean()}]
    for m in ("AG", "IA"):
        x = tg[tg["model"] == m]
        rows.append({"run": f"{m} (GAMA)", "strata": len(x), "mean err (s)": x["mean_err"].mean(), "mean |sd err|": x["sd_err"].abs().mean(), "cover95 mean": x["cover95"].mean()})
    log.p("")
    log.p("Segment travel times")
    log.table(pd.DataFrame(rows), "{:.3f}")
    log.save()


def c3_fig(t3, plt):
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.hist(t3["mean_err"], bins=50, color=COLOR["C"], alpha=0.85)
    ax.set_title("C engine: simulated - empirical mean travel time per segment x slot (s)", fontsize=9)
    ax.set_xlabel("seconds")
    ax.set_ylabel("strata")
    fig.tight_layout()
    fig.savefig(os.path.join(FIGS, "fig_travel_error.png"))
    plt.close(fig)


if __name__ == "__main__":
    main()
