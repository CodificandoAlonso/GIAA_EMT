"""
Analysis C - Empirical validation against known_data (plan section 6).

Outputs
    logs/table3_empirical_validation.log   C1 occupancy, C2 (no reference), C3 travel times, C4, C5
    logs/c1_occupancy_strata.csv           per stratum (dir x stop x departure slot) and model
    logs/c1_delta_summary.csv              Delta_s = W1_IA - W1_AG, mean over strata with replica-bootstrap CI
    logs/c3_travel_strata.csv              per segment x slot and model
    figures/fig1_occupancy_distributions.png
    figures/fig2_error_map.png

known_data is the empirical reference as is: N(mu, sigma) per stop and slot (occupancy) and per
segment and slot (travel times). The reference is a fitted normal, not raw observations, so the
primary distance is W1 against the normal (untruncated; sensitivity to clipping in F3).
"""

import os

import numpy as np
import pandas as pd
from scipy.stats import norm

from config import (BC_ACCEPT, BOOTSTRAP, CAPACITY, COLOR, CROWDING, FIGS, INK, PEAK_SLOTS, SEED,
                    TIMESLOTS, W1_ACCEPT_PAX, div_cmap, seq_cmap, setup_matplotlib)
from kpis import prepared
from load import load_known
from metrics import (Log, bc_project, boot_weights, ci_mean, ci_ratio, ks_vs_normal, save_csv,
                     w1_vs_normal)
from strata import (GRID, known_aligned, normal_cdf_grid, occ_hist, pmf_stats, step_cdf_grid,
                    w1_normal_from_counts)

B_BOOT = 300


# --------------------------------------------------------------------------
# C1 - occupancy
# --------------------------------------------------------------------------

def c1_table(model: str, h: dict, kn: pd.DataFrame) -> pd.DataFrame:
    counts = h["counts"].sum(0)                                   # (S, K) pooled over replicas
    n = counts.sum(-1)
    pmf = counts / n[:, None]
    st = pmf_stats(pmf)
    mu, sd = kn["mean"].to_numpy(), kn["std"].to_numpy()
    G = normal_cdf_grid(mu, sd)
    F = step_cdf_grid(pmf.astype(np.float32))
    w1 = np.abs(F - G).sum(-1) * 0.1
    ks = np.abs(F - G).max(-1)
    t = kn[["dir", "stop", "dep_slot", "mean", "std", "peak", "demand"]].rename(
        columns={"mean": "emp_mean", "std": "emp_sd"}).copy()
    t["model"] = model
    t["n_sim"] = n
    t["sim_mean"], t["sim_sd"] = st["mean"], st["sd"]
    t["mean_err"] = st["mean"] - mu
    t["sd_err"] = st["sd"] - sd
    t["median_err"] = st["median"] - mu
    t["p90_err"] = st["p90"] - (mu + norm.ppf(0.9) * sd)
    t["W1"], t["KS"] = w1, ks
    k = np.arange(CAPACITY + 1)
    t["P60_sim"] = pmf[:, k >= CROWDING].sum(-1)
    t["P60_emp"] = norm.sf((CROWDING - 0.5 - mu) / sd)
    t["P60_err_pp"] = 100 * (t["P60_sim"] - t["P60_emp"])
    bc, meth = [], []
    for s in range(len(t)):
        x = np.repeat(k, counts[s].astype(int))
        c, m = bc_project(x, mu[s], sd[s], rng=np.random.default_rng(SEED + s))
        bc.append(c)
        meth.append(m)
    t["BC"], t["BC_method"] = bc, meth
    t["accept_BC"] = t["BC"] >= BC_ACCEPT
    t["accept_W1"] = t["W1"] <= W1_ACCEPT_PAX
    return t


def c1_delta(hs: dict, kn: pd.DataFrame, t: pd.DataFrame, extra_groups: dict = None):
    """Delta_s = W1_IA - W1_AG per stratum, and replica-bootstrap CIs of group means."""
    mu, sd = kn["mean"].to_numpy(), kn["std"].to_numpy()
    G = normal_cdf_grid(mu, sd)
    boots = {}
    for i, m in enumerate(("IA", "AG")):
        c = hs[m]["counts"]
        R, S, K = c.shape
        w = boot_weights(R, b=B_BOOT, seed=SEED + 10 + i).astype(np.float32)
        cw = (w @ c.reshape(R, S * K)).reshape(B_BOOT, S, K)
        boots[m] = w1_normal_from_counts(cw, G)                      # (B, S)
    d_boot = boots["IA"] - boots["AG"]
    ia = t[t["model"] == "IA"].reset_index(drop=True)
    ag = t[t["model"] == "AG"].reset_index(drop=True)
    d_point = ia["W1"].to_numpy() - ag["W1"].to_numpy()
    rows = []
    groups = {"all strata": np.ones(len(kn), bool),
              "peak": kn["peak"].to_numpy(), "off-peak": ~kn["peak"].to_numpy(),
              "toA": (kn["dir"] == "toA").to_numpy(), "toB": (kn["dir"] == "toB").to_numpy(),
              "demand low": (kn["demand"] == "low").to_numpy(),
              "demand medium": (kn["demand"] == "medium").to_numpy(),
              "demand high": (kn["demand"] == "high").to_numpy(),
              "mean >= 40 pax": (kn["mean"] >= 40).to_numpy()}
    groups.update(extra_groups or {})
    for name, msk in groups.items():
        b = d_boot[:, msk].mean(1)
        rows.append({"group": name, "strata": int(msk.sum()),
                     "W1 IA": ia["W1"][msk].mean(), "W1 AG": ag["W1"][msk].mean(),
                     "mean Delta (IA-AG)": d_point[msk].mean(),
                     "CI low": np.percentile(b, 2.5), "CI high": np.percentile(b, 97.5),
                     "strata IA better %": 100 * (d_point[msk] < 0).mean(),
                     "median Delta": np.median(d_point[msk]), "max |Delta|": np.abs(d_point[msk]).max()})
    return pd.DataFrame(rows), d_point, boots


# --------------------------------------------------------------------------
# C3 - travel times
# --------------------------------------------------------------------------

def c3_table(model: str, p: dict, known_times: pd.DataFrame):
    v = p["visits"]
    v = v[~v["is_first"]].copy()
    prev = {}
    for d, lst in p["order"].items():
        for i in range(1, len(lst)):
            prev[(d, lst[i])] = lst[i - 1]
    v["seg"] = [f"{prev[(d, s)]}-{s}" for d, s in zip(v["dir"], v["stop"])]
    kt = known_times.dropna(subset=["mean"]).rename(columns={"mean": "emp_mean", "std": "emp_sd"})
    g = v.groupby(["dir", "seg", "slot"])["tbs"]
    rows = []
    k = kt.set_index(["dir", "seg", "slot"])
    for key, x in g:
        if key not in k.index:
            continue
        mu, sd = k.loc[key, "emp_mean"], k.loc[key, "emp_sd"]
        x = x.to_numpy(float)
        if sd <= 0:
            continue
        qs = np.quantile(x, [0.05, 0.5, 0.95])
        rows.append({"model": model, "dir": key[0], "seg": key[1], "slot": key[2], "n_sim": x.size,
                     "emp_mean": mu, "emp_sd": sd, "sim_mean": x.mean(), "sim_sd": x.std(ddof=1),
                     "mean_err": x.mean() - mu, "sd_err": x.std(ddof=1) - sd,
                     "q05_err": qs[0] - (mu + norm.ppf(0.05) * sd), "q50_err": qs[1] - mu,
                     "q95_err": qs[2] - (mu + norm.ppf(0.95) * sd),
                     "W1": w1_vs_normal(x, mu, sd), "KS": ks_vs_normal(x, mu, sd),
                     "cover95": float(np.mean(np.abs(x - mu) <= 1.96 * sd)),
                     "negative_support_mass": float(norm.cdf(0, mu, sd))})
    t = pd.DataFrame(rows)
    cols = ["dir", "seg", "slot"]
    s = v.groupby(["replica"] + cols)["tbs"].agg(["sum", "size"])
    return t, v, s


def c3_mae_ci(v: pd.DataFrame, t: pd.DataFrame, seed: int):
    """MAE of pooled stratum means against the normal means, replica-bootstrap CI."""
    keys = ["dir", "seg", "slot"]
    t = t.set_index(keys)
    g = v.groupby(["replica"] + keys)["tbs"].agg(["sum", "size"])
    ssum = g["sum"].unstack(keys, fill_value=0).reindex(range(1000), fill_value=0)
    scnt = g["size"].unstack(keys, fill_value=0).reindex(range(1000), fill_value=0)
    cols = [c for c in ssum.columns if c in t.index]
    ssum, scnt = ssum[cols].to_numpy(float), scnt[cols].to_numpy(float)
    mu = t.loc[cols, "emp_mean"].to_numpy()
    w = boot_weights(1000, b=B_BOOT, seed=seed)
    with np.errstate(invalid="ignore", divide="ignore"):
        boot = (w @ ssum) / (w @ scnt)
    mae = np.nanmean(np.abs(boot - mu), axis=1)
    point = np.nanmean(np.abs(ssum.sum(0) / scnt.sum(0) - mu))
    return point, np.percentile(mae, 2.5), np.percentile(mae, 97.5), mae


# --------------------------------------------------------------------------
# Figures
# --------------------------------------------------------------------------

def fig1(hs, kn, t, plt):
    strata = [("toA", 2539, 7), ("toA", 2539, 13), ("toB", 1167, 18), ("toB", 1167, 12),
              ("toA", 4188, 8), ("toB", 3929, 22)]
    idx = {(d, s, ts): i for i, (d, s, ts) in enumerate(zip(kn["dir"], kn["stop"], kn["dep_slot"]))}
    strata = [s for s in strata if s in idx]
    fig, axes = plt.subplots(2, 3, figsize=(13, 6.6))
    x = np.arange(CAPACITY + 1)
    for ax, key in zip(axes.flat, strata):
        i = idx[key]
        mu, sd = kn["mean"].iloc[i], kn["std"].iloc[i]
        pe = np.diff(norm.cdf(np.append(x - 0.5, CAPACITY + 0.5), mu, sd))
        ax.fill_between(x, pe, color=INK["primary"], alpha=0.15, lw=0, label="empirical N(mu, sigma)")
        ax.plot(x, pe, color=INK["primary"], lw=1.2)
        for m in ("IA", "AG"):
            c = hs[m]["counts"].sum(0)[i]
            ax.plot(x, c / c.sum(), color=COLOR[m], lw=1.6, label=m)
        r = t[(t["dir"] == key[0]) & (t["stop"] == key[1]) & (t["dep_slot"] == key[2])]
        w1 = {m: float(r[r["model"] == m]["W1"].iloc[0]) for m in ("IA", "AG")}
        peak = "peak" if key[2] in PEAK_SLOTS else "off-peak"
        ax.set_title(f"{key[0]} stop {key[1]}, slot {key[2]} ({peak})\nW1: IA {w1['IA']:.2f}, AG {w1['AG']:.2f}", fontsize=9)
        ax.set_xlabel("occupancy after the stop (pax)")
        ax.set_xlim(0, CAPACITY)
    axes[0, 0].legend(fontsize=8)
    fig.suptitle("Figure 1 - Occupancy distributions: empirical normal, IA and AG")
    fig.tight_layout()
    fig.savefig(os.path.join(FIGS, "fig1_occupancy_distributions.png"))
    plt.close(fig)


def fig2(t, order, plt):
    fig, axes = plt.subplots(2, 3, figsize=(14, 8.2), gridspec_kw={"width_ratios": [1, 1, 0.85]})
    vmax = float(max(t["W1"].quantile(0.99), 1.0))
    for r, d in enumerate(("toA", "toB")):
        stops = order[d][:-1]
        for c, m in enumerate(("IA", "AG")):
            h = t[(t["model"] == m) & (t["dir"] == d)]
            mat = h.pivot(index="stop", columns="dep_slot", values="W1").reindex(index=stops, columns=TIMESLOTS)
            ax = axes[r, c]
            im = ax.imshow(mat.values, aspect="auto", cmap=seq_cmap(), vmin=0, vmax=vmax)
            ax.set_title(f"{d}: W1 vs empirical, {m} (pax)", fontsize=10)
            ax.set_yticks(range(len(stops)))
            ax.set_yticklabels(stops, fontsize=7)
            ax.set_xticks(range(0, len(TIMESLOTS), 2))
            ax.set_xticklabels(TIMESLOTS[::2], fontsize=8)
            ax.grid(False)
            ax.set_xlabel("trip departure slot")
        ia = t[(t["model"] == "IA") & (t["dir"] == d)].set_index(["stop", "dep_slot"])["W1"]
        ag = t[(t["model"] == "AG") & (t["dir"] == d)].set_index(["stop", "dep_slot"])["W1"]
        dm = (ia - ag).unstack().reindex(index=stops, columns=TIMESLOTS)
        lim = max(0.05, float(np.nanmax(np.abs(dm.values))))
        from matplotlib.colors import TwoSlopeNorm
        ax = axes[r, 2]
        im2 = ax.imshow(dm.values, aspect="auto", cmap=div_cmap(), norm=TwoSlopeNorm(0, -lim, lim))
        ax.set_title(f"{d}: Delta = W1 IA - W1 AG (pax)", fontsize=10)
        ax.set_yticks(range(len(stops)))
        ax.set_yticklabels(stops, fontsize=7)
        ax.set_xticks(range(0, len(TIMESLOTS), 2))
        ax.set_xticklabels(TIMESLOTS[::2], fontsize=8)
        ax.grid(False)
        ax.set_xlabel("trip departure slot")
    fig.colorbar(im, ax=axes[:, :2], shrink=0.7, label="Wasserstein-1 against known_data (pax)")
    fig.colorbar(im2, ax=axes[:, 2], shrink=0.7, label="negative = IA closer")
    fig.suptitle("Figure 2 - Empirical error map by stop and slot (blue = larger error; Delta red = IA closer)", x=0.45)
    fig.savefig(os.path.join(FIGS, "fig2_error_map.png"))
    plt.close(fig)


def fig_travel(t, plt):
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2), sharey=True)
    for ax, m in zip(axes, ("IA", "AG")):
        h = t[t["model"] == m]
        ax.hist(h["mean_err"], bins=50, color=COLOR[m], alpha=0.85)
        ax.set_title(f"{m}: simulated - empirical mean travel time per segment x slot (s)")
        ax.set_xlabel("seconds")
    axes[0].set_ylabel("strata")
    fig.tight_layout()
    fig.savefig(os.path.join(FIGS, "c3_travel_time_error.png"))
    plt.close(fig)


# --------------------------------------------------------------------------

def main():
    plt = setup_matplotlib()
    hs = {m: occ_hist(m) for m in ("IA", "AG")}
    p = {m: prepared(m) for m in ("IA", "AG")}
    kn = known_aligned(hs["IA"]["index"])
    log = Log("table3_empirical_validation.log", "Table 3 - Empirical validation against known_data (Analysis C)")
    log.p("Reference: known_data normal parameters, used as is. Not independent of the simulation inputs: the same")
    log.p("operational records calibrate both the inputs and this reference (calibration-period validation, plan 2.3).")

    # ---- C1
    t = pd.concat([c1_table(m, hs[m], kn) for m in ("IA", "AG")], ignore_index=True)
    save_csv(t, "c1_occupancy_strata.csv")
    dsum, d_point, boots = c1_delta(hs, kn, t)
    save_csv(dsum, "c1_delta_summary.csv")

    log.h("C1 - Occupancy by direction x stop x trip-departure slot (475 strata, terminal visits excluded)")
    log.p("Distances are against the untruncated N(mu, sigma) of known_data. W1 in passengers, from CDFs on a 0.1 pax grid.")
    log.p("BC = Bhattacharyya coefficient with the project method (normal-normal if the simulated sample passes the")
    log.p(f"simplified normality test, else gaussian KDE vs normal); accepted if BC >= {BC_ACCEPT}. W1 accepted if <= {W1_ACCEPT_PAX} pax.")
    log.p("P60 error = P_sim(O >= 60) - P_emp(O >= 60) in percentage points (empirical: normal tail with continuity correction).")
    rows = []
    for m in ("IA", "AG"):
        h = t[t["model"] == m]
        fail = h[~h["accept_BC"]]
        rows.append({
            "model": m, "strata": len(h),
            "mean |mean err| (pax)": h["mean_err"].abs().mean(), "max |mean err|": h["mean_err"].abs().max(),
            "mean SD err": h["sd_err"].mean(), "mean |SD err|": h["sd_err"].abs().mean(),
            "mean |median err|": h["median_err"].abs().mean(), "mean |p90 err|": h["p90_err"].abs().mean(),
            "W1 median": h["W1"].median(), "W1 p90": h["W1"].quantile(0.9), "W1 max": h["W1"].max(),
            "BC median": h["BC"].median(), "BC min": h["BC"].min(),
            "accepted BC %": 100 * h["accept_BC"].mean(), "accepted W1 %": 100 * h["accept_W1"].mean(),
            "failing strata (BC)": len(fail),
            "W1 mean in failing": fail["W1"].mean() if len(fail) else np.nan,
            "mean |P60 err| pp": h["P60_err_pp"].abs().mean(), "max |P60 err| pp": h["P60_err_pp"].abs().max(),
        })
    log.table(pd.DataFrame(rows).set_index("model").T.reset_index().rename(columns={"index": "metric"}), "{:.3f}")

    log.p("")
    log.p("Primary estimand: Delta_s = W1_IA,s - W1_AG,s (negative favours IA). Mean over strata with a 95 % percentile CI")
    log.p(f"from {B_BOOT} bootstrap resamples of complete replicas (independent per model).")
    log.table(dsum, "{:.4f}")
    log.p("")
    ci_all = dsum.iloc[0]
    log.p(f"Reading: mean Delta = {ci_all['mean Delta (IA-AG)']:+.4f} pax, CI [{ci_all['CI low']:+.4f}, {ci_all['CI high']:+.4f}]; "
          f"margin for a practically relevant fidelity gain = {W1_ACCEPT_PAX} pax (config) -> "
          + ("difference within margin" if max(abs(ci_all['CI low']), abs(ci_all['CI high'])) < W1_ACCEPT_PAX else "NOT within margin"))
    worst = t.sort_values("W1", ascending=False).head(10)
    log.p("")
    log.p("10 strata with the largest W1 (either model)")
    log.table(worst[["model", "dir", "stop", "dep_slot", "emp_mean", "emp_sd", "sim_mean", "sim_sd", "W1", "BC", "BC_method",
                     "P60_err_pp"]], "{:.3f}")
    log.p("")
    log.p("Method of BC acceptance by model")
    log.table(t.groupby(["model", "BC_method"]).size().rename("strata").reset_index())
    ne = t[t["model"] == "IA"][["dir", "stop", "dep_slot"]].copy()
    ne["W1_IA"] = t[t["model"] == "IA"]["W1"].to_numpy()
    ne["W1_AG"] = t[t["model"] == "AG"]["W1"].to_numpy()
    ne["Delta"] = ne["W1_IA"] - ne["W1_AG"]
    log.p("")
    log.p("5 strata where IA is closest and 5 where AG is closest (Delta = W1_IA - W1_AG)")
    log.table(pd.concat([ne.nsmallest(5, "Delta"), ne.nlargest(5, "Delta")]), "{:.3f}")

    # ---- C2
    log.h("C2 - Boardings and alightings")
    log.p("known_data contains only occupancy and segment travel-time normals. There is no empirical reference for")
    log.p("boardings or alightings per visit, so they are NOT validated here; the IA vs AG comparison (B2) is the only")
    log.p("evidence. Alightings are an externally imposed calibrated input (beta-binomial), so agreement between the")
    log.p("models says nothing about passenger decision-making.")

    # ---- C3
    kt = load_known()["times"]
    t3, v3, _ = zip(*[(lambda r: (r[0], r[1], r[2]))(c3_table(m, p[m], kt)) for m in ("IA", "AG")])
    t3 = pd.concat(t3, ignore_index=True)
    save_csv(t3, "c3_travel_strata.csv")
    log.h("C3 - Segment travel times by segment x slot of the visit")
    log.p("Times are sampled by the simulator from the same fitted normal distributions that known_data holds (plan 6, C3):")
    log.p("this validates the sampling and calibration procedure, not an independently learned traffic model.")
    log.p("MAE = mean over strata of |pooled simulated mean - empirical mean|, replica-bootstrap CI. cover95 = share of simulated")
    log.p("times inside mu +- 1.96 sigma (nominal 95 % if the simulator reproduces the normal; lower where the normal has")
    log.p("negative support truncated/clipped by the simulator).")
    rows = []
    for i, m in enumerate(("IA", "AG")):
        h = t3[t3["model"] == m]
        point, lo, hi, _ = c3_mae_ci(v3[i], h, SEED + 20 + i)
        rows.append({"model": m, "strata": len(h), "MAE mean (s)": point, "MAE 95% CI": f"[{lo:.2f}, {hi:.2f}]",
                     "mean err (s)": h["mean_err"].mean(), "mean |sd err| (s)": h["sd_err"].abs().mean(),
                     "mean |q05 err|": h["q05_err"].abs().mean(), "mean |q50 err|": h["q50_err"].abs().mean(),
                     "mean |q95 err|": h["q95_err"].abs().mean(), "W1 median": h["W1"].median(),
                     "W1 p90": h["W1"].quantile(0.9), "W1 max": h["W1"].max(),
                     "cover95 mean": h["cover95"].mean(), "cover95 min": h["cover95"].min(),
                     "strata |mean err| > 10 s": int((h["mean_err"].abs() > 10).sum())})
    log.table(pd.DataFrame(rows).set_index("model").T.reset_index().rename(columns={"index": "metric"}), "{:.3f}")
    ia3 = t3[t3["model"] == "IA"].set_index(["dir", "seg", "slot"])
    ag3 = t3[t3["model"] == "AG"].set_index(["dir", "seg", "slot"])
    common = ia3.index.intersection(ag3.index)
    dw = (ia3.loc[common, "W1"] - ag3.loc[common, "W1"])
    log.p("")
    log.p(f"Delta W1 (IA - AG) over {len(common)} common segment x slot strata: mean {dw.mean():+.3f} s, "
          f"median {dw.median():+.3f} s, IA closer in {100 * (dw < 0).mean():.1f} % of strata (margin 10 s).")
    worst3 = t3.sort_values("W1", ascending=False).head(10)
    log.p("")
    log.p("10 segment x slot strata with the largest W1")
    log.table(worst3[["model", "dir", "seg", "slot", "n_sim", "emp_mean", "emp_sd", "sim_mean", "sim_sd", "mean_err", "W1",
                      "cover95", "negative_support_mass"]], "{:.3f}")
    log.p("")
    log.p("Residual pattern: mean error (sim - emp) by slot (mean over segments) and by direction")
    res = t3.groupby(["model", "slot"])["mean_err"].mean().unstack(0)
    log.table(res.reset_index(), "{:.2f}")
    log.p("")
    log.table(t3.groupby(["model", "dir"])["mean_err"].agg(["mean", lambda s: s.abs().mean()]).rename(
        columns={"<lambda_0>": "mean |err|"}).reset_index(), "{:.3f}")

    # ---- C4
    log.h("C4 - Waiting times")
    log.p("There is no empirical waiting-time reference in known_data. Waiting time is a derived simulation output: it is")
    log.p("compared between IA and AG (B1/B2) and checked for internal consistency (A3), and is NOT empirically validated.")

    # ---- C5
    log.h("C5 - Reporting levels (occupancy, W1 against known_data)")
    rows = []
    for m in ("IA", "AG"):
        h = t[t["model"] == m]
        lv = {"global (pooled over strata)": np.ones(len(h), bool), "peak slots": h["peak"].to_numpy(),
              "off-peak": ~h["peak"].to_numpy(),
              "excl. terminals 2646/5727 (pipeline convention)": ~h["stop"].isin([2646, 5727]).to_numpy(),
              "high-demand tertile": (h["demand"] == "high").to_numpy(),
              "strata with mean >= 40 pax": (h["emp_mean"] >= 40).to_numpy()}
        for name, msk in lv.items():
            g = h[msk]
            rows.append({"model": m, "level": name, "strata": len(g), "W1 mean": g["W1"].mean(),
                         "W1 max": g["W1"].max(), "BC min": g["BC"].min(), "accepted BC %": 100 * g["accept_BC"].mean(),
                         "accepted W1 %": 100 * g["accept_W1"].mean(), "mean |mean err|": g["mean_err"].abs().mean(),
                         "mean |P60 err| pp": g["P60_err_pp"].abs().mean()})
    log.table(pd.DataFrame(rows), "{:.3f}")
    log.save()

    fig1(hs, kn, t, plt)
    fig2(t, p["AG"]["order"], plt)
    fig_travel(t3, plt)


if __name__ == "__main__":
    main()
