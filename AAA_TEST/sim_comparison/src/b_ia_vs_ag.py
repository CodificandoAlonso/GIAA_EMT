"""
Analysis B - Controlled comparison between IA and AG (plan section 5).

Outputs
    logs/table2_global_kpis.log (+ .csv)       B1: replica-level KPIs, 95 % CI, differences, equivalence
    logs/b2_distributional.log (+ strata csv)  B2: W1, Bhattacharyya, quantile and tail differences,
                                                   pooled and by stratum
    logs/b3_b4_heterogeneity.log (+ csv)       B3 note and B4: IA-AG differences by direction, stop,
                                                   slot, peak, demand, denied-boarding trips
    figures/fig4_waiting_time.png
    figures/fig5_ia_ag_difference_heatmap.png
    figures/fig7_replica_convergence.png
"""

import os

import numpy as np
import pandas as pd

from config import (CAPACITY, COLOR, CROWDING, FIGS, INK, MARGINS, PEAK_SLOTS, SEED, TIMESLOTS,
                    div_cmap, seq_cmap, setup_matplotlib)
from kpis import prepared, replica_kpis, stratum_sums
from load import load_known
from metrics import (Log, bc_hist, boot_weights, ci_mean, ci_ratio, cohen_d, diff_ci, equivalence,
                     save_csv, w1_samples)

# KPI -> (label, unit, margin key or None, relative margin?)
KPIS = [
    ("occ_mean", "Mean occupancy", "pax", "occupancy_pax", False),
    ("occ_median", "Median occupancy", "pax", "occupancy_pax", False),
    ("occ_sd", "Occupancy SD", "pax", "occupancy_pax", False),
    ("occ_p90", "Occupancy p90", "pax", "occupancy_pax", False),
    ("occ_p95", "Occupancy p95", "pax", "occupancy_pax", False),
    ("share_occ_ge40", "Visits with O >= 40", "%", "prob_pp", False),
    ("share_occ_ge60", "Visits with O >= 60", "%", "prob_pp", False),
    ("share_occ_ge70", "Visits with O >= 70", "%", "prob_pp", False),
    ("share_at_capacity", "Visits at capacity (O = 80)", "%", "prob_pp", False),
    ("wait_mean", "Mean waiting time", "s", "wait_tail_s", False),
    ("wait_median", "Median waiting time", "s", "wait_median_s", False),
    ("wait_p90", "Waiting time p90", "s", "wait_tail_s", False),
    ("wait_p95", "Waiting time p95", "s", "wait_tail_s", False),
    ("wait_p99", "Waiting time p99", "s", "wait_tail_s", False),
    ("wait_cvar95", "Waiting time CVaR95", "s", "wait_tail_s", False),
    ("share_wait_gt15min", "Waits > 15 min", "%", "prob_pp", False),
    ("travel_time_mean", "Mean segment travel time", "s", "travel_time_s", False),
    ("trip_duration_mean", "Mean trip duration", "s", "trip_duration_s", False),
    ("headway_cv", "Headway CV (mean over stops)", "-", "headway_cv", False),
    ("headways_under_2min_pct", "Headways < 2 min (bunching)", "%", "prob_pp", False),
    ("delay_events", "DELAY events per day", "n", None, False),
    ("delay_mean_min", "Mean delay of delayed departures", "min", None, False),
    ("boardings_per_visit", "Boardings per visit", "pax", "flow_per_visit_pax", False),
    ("alightings_per_visit", "Alightings per visit", "pax", "flow_per_visit_pax", False),
    ("boardings_total", "Boardings per day", "pax", None, False),
    ("denied_total", "Denied boardings per day", "pax", "denied_rel", True),
    ("visits_with_denied", "Visits with denied boarding per day", "n", "denied_rel", True),
    ("share_visits_denied", "Share of visits with denied boarding", "%", "prob_pp", False),
    ("denied_per_affected_visit", "Denied per affected visit", "pax", None, False),
    ("share_trips_with_denied", "Trips with denied boarding", "%", "prob_pp", False),
    ("trips", "Completed trips per replica", "n", None, False),
    ("visits", "Bus-stop visits per replica", "n", None, False),
]


# --------------------------------------------------------------------------

def b1(log: Log, k: dict):
    w_ia = boot_weights(len(k["IA"]), seed=SEED)
    w_ag = boot_weights(len(k["AG"]), seed=SEED + 1)
    rows = []
    for col, label, unit, mkey, rel in KPIS:
        a, b = k["IA"][col].to_numpy(float), k["AG"][col].to_numpy(float)
        ma, la, ha, ba = ci_mean(np.nan_to_num(a, nan=np.nanmean(a)), w_ia)
        mb, lb, hb, bb = ci_mean(np.nan_to_num(b, nan=np.nanmean(b)), w_ag)
        lo, hi = diff_ci(ba, bb)
        margin = None
        if mkey:
            margin = MARGINS[mkey] * (abs(mb) if rel else 1)
        rows.append({
            "KPI": label, "unit": unit,
            "IA mean": ma, "IA 95% CI": f"[{la:.3f}, {ha:.3f}]",
            "AG mean": mb, "AG 95% CI": f"[{lb:.3f}, {hb:.3f}]",
            "IA-AG": ma - mb, "diff 95% CI": f"[{lo:.3f}, {hi:.3f}]",
            "rel. diff %": (100 * (ma - mb) / mb) if abs(mb) > 1e-6 else np.nan,
            "Cohen d": cohen_d(a[np.isfinite(a)], b[np.isfinite(b)]),
            "margin": margin,
            "equivalence": equivalence(lo, hi, margin) if mkey else "no margin",
        })
    t = pd.DataFrame(rows)
    save_csv(t, "table2_global_kpis.csv")
    log.h("B1 - Global KPIs (replica level, n = 1000 replicas per model)")
    log.p("Mean over replicas, 95 % percentile CI from 1000 bootstrap resamples of complete replicas (independent")
    log.p("resampling per model, replicas are not matched). Occupancy KPIs exclude terminal visits (O = 0 by rule).")
    log.p("'margin' is absolute in the KPI unit (relative KPIs: 10 % of the AG value).")
    log.table(t, "{:.3f}")
    n = t["equivalence"].value_counts().to_dict()
    log.p(f"Summary: {n}")
    return t


# --------------------------------------------------------------------------

def _strata_compare(name, a: pd.DataFrame, b: pd.DataFrame, keys, value, edges, margin, tails):
    """Per-stratum and pooled IA vs AG distributional comparison."""
    ga, gb = a.groupby(keys)[value], b.groupby(keys)[value]
    idx = sorted(set(ga.groups) | set(gb.groups))
    rows = []
    for s in idx:
        x = ga.get_group(s).to_numpy(float) if s in ga.groups else np.array([])
        y = gb.get_group(s).to_numpy(float) if s in gb.groups else np.array([])
        r = dict(zip(keys, s if isinstance(s, tuple) else (s,)))
        r.update(_dist_row(x, y, edges, tails))
        rows.append(r)
    t = pd.DataFrame(rows)
    pooled = _dist_row(a[value].to_numpy(float), b[value].to_numpy(float), edges, tails)
    ok = t.dropna(subset=["W1"])
    summary = {
        "variable": name, "strata": len(ok), "pooled W1": pooled["W1"],
        "pooled BC": pooled["BC"], "pooled d_mean": pooled["d_mean"],
        "pooled d_p50": pooled["d_p50"], "pooled d_p90": pooled["d_p90"],
        "pooled d_p95": pooled["d_p95"], "pooled d_p99": pooled["d_p99"],
        "strata W1 median": ok["W1"].median(), "strata W1 p90": ok["W1"].quantile(0.9),
        "strata W1 max": ok["W1"].max(),
        "strata with W1 <= margin %": 100 * (ok["W1"] <= margin).mean(),
        "strata BC median": ok["BC"].median(), "strata BC min": ok["BC"].min(),
        "margin": margin,
    }
    for tname in tails:
        summary[f"pooled d_{tname} (pp)"] = pooled[f"d_{tname}"]
        summary[f"strata max |d_{tname}| (pp)"] = ok[f"d_{tname}"].abs().max()
    return t, summary


def _dist_row(x, y, edges, tails):
    r = {"n_IA": x.size, "n_AG": y.size}
    if x.size == 0 or y.size == 0:
        return {**r, "W1": np.nan, "BC": np.nan, "d_mean": np.nan}
    r["mean_IA"], r["mean_AG"] = x.mean(), y.mean()
    r["d_mean"] = x.mean() - y.mean()
    r["W1"] = w1_samples(x, y)
    r["BC"] = bc_hist(x, y, edges)
    for q in (50, 90, 95, 99):
        r[f"d_p{q}"] = np.percentile(x, q) - np.percentile(y, q)
    for tname, f in tails.items():
        r[f"d_{tname}"] = 100 * (f(x).mean() - f(y).mean())
    return r


def b2(log: Log, p: dict):
    va, vb = p["IA"]["visits"], p["AG"]["visits"]
    nl_a, nl_b = va[~va["is_last"]], vb[~vb["is_last"]]
    nf_a, nf_b = va[~va["is_first"]], vb[~vb["is_first"]]
    wa, wb = p["IA"]["waits"], p["AG"]["waits"]
    ea, eb = p["IA"]["events"], p["AG"]["events"]
    int_edges = np.arange(-0.5, CAPACITY + 1.5, 1)
    specs = [
        ("occupancy (pax)", nl_a, nl_b, ["dir", "stop", "dep_slot"], "occ", int_edges, MARGINS["occupancy_pax"],
         {"P(O>=60)": lambda z: z >= CROWDING, "P(O>=80)": lambda z: z >= CAPACITY}),
        ("boardings per visit (pax)", nl_a, nl_b, ["dir", "stop", "slot"], "boards", int_edges,
         MARGINS["flow_per_visit_pax"], {"P(B=0)": lambda z: z == 0}),
        ("alightings per visit (pax)", nf_a, nf_b, ["dir", "stop", "slot"], "dropoffs", int_edges,
         MARGINS["flow_per_visit_pax"], {"P(A=0)": lambda z: z == 0}),
        ("denied per visit (pax)", nl_a, nl_b, ["dir", "stop", "slot"], "denied", int_edges, MARGINS["flow_per_visit_pax"],
         {"P(denied>0)": lambda z: z > 0}),
        ("segment travel time (s)", nf_a, nf_b, ["dir", "stop", "slot"], "tbs", np.arange(0, 4000, 10),
         MARGINS["travel_time_s"], {}),
        ("waiting time (s)", wa, wb, ["dir", "stop", "slot"], "wait", np.arange(0, 10000, 30),
         MARGINS["wait_median_s"], {"P(W>15min)": lambda z: z > 900}),
        ("departure delay of DELAY events (min)", ea, eb, ["dir", "slot"], "delay_min", np.arange(0, 200, 1),
         None, {}),
    ]
    summaries = []
    for name, a, b, keys, val, edges, margin, tails in specs:
        t, s = _strata_compare(name, a, b, keys, val, edges, margin if margin else np.inf, tails)
        save_csv(t, f"b2_strata_{val}.csv")
        summaries.append(s)
    st = pd.DataFrame(summaries)
    save_csv(st, "b2_distributional.csv")
    log.h("B2 - Distributional comparison IA vs AG (pooled over replicas; strata = direction x stop x slot)")
    log.p("W1 = Wasserstein-1 (exact, scipy) in the variable's unit. BC = Bhattacharyya coefficient on a common")
    log.p("discretisation: unit bins for counts/occupancy, 10 s bins for travel times, 30 s bins for waits, 1 min")
    log.p("for delays. d_* = IA - AG (quantiles in the variable's unit, tail probabilities in percentage points).")
    log.p("Occupancy strata: trip departure slot; other variables: slot of the visit. Terminal visits excluded")
    log.p("for occupancy/boardings/denied, first stops excluded for alightings/travel times.")
    for _, r in st.iterrows():
        log.p("")
        log.p(f"* {r['variable']}")
        for kname, val in r.items():
            if kname == "variable" or (isinstance(val, float) and np.isnan(val)):
                continue
            log.p(f"    {kname:34s} {val:.4f}" if isinstance(val, float) else f"    {kname:34s} {val}")
    return st


# --------------------------------------------------------------------------

def b4(log: Log, p: dict, k: dict, known_occ: pd.DataFrame, plt):
    va, vb = p["IA"]["visits"], p["AG"]["visits"]
    keys = ["dir", "stop", "dep_slot"]
    sa, na, cols = stratum_sums(va[~va["is_last"]], keys, "occ")
    sb, nb, cols_b = stratum_sums(vb[~vb["is_last"]], keys, "occ")
    cols_b = list(cols_b)
    order = [cols_b.index(c) for c in cols]
    sb, nb = sb[:, order], nb[:, order]
    w_ia = boot_weights(sa.shape[0], b=500, seed=SEED)
    w_ag = boot_weights(sb.shape[0], b=500, seed=SEED + 1)
    pa, _, _, ba = ci_ratio(sa, na, w_ia)
    pb, _, _, bb = ci_ratio(sb, nb, w_ag)
    d = ba - bb
    lo, hi = np.nanpercentile(d, 2.5, axis=0), np.nanpercentile(d, 97.5, axis=0)
    het = pd.DataFrame(list(cols), columns=keys)
    het["mean_IA"], het["mean_AG"], het["d_mean"] = pa, pb, pa - pb
    het["ci_low"], het["ci_high"] = lo, hi
    het["n_IA"], het["n_AG"] = na.sum(0), nb.sum(0)
    het["equivalence"] = [equivalence(l, h, MARGINS["occupancy_pax"]) for l, h in zip(lo, hi)]
    w1s = pd.read_csv(os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs", "b2_strata_occ.csv"))
    het = het.merge(w1s[["dir", "stop", "dep_slot", "W1", "BC"]], on=keys, how="left")
    het["peak"] = het["dep_slot"].isin(PEAK_SLOTS)
    km = known_occ.rename(columns={"slot": "dep_slot", "mean": "known_mean"})[["dir", "stop", "dep_slot", "known_mean"]]
    het = het.merge(km, on=keys, how="left")
    tert = het["known_mean"].quantile([1 / 3, 2 / 3]).to_numpy()
    het["demand"] = pd.cut(het["known_mean"], [-np.inf, tert[0], tert[1], np.inf], labels=["low", "medium", "high"])
    save_csv(het, "b4_occupancy_strata.csv")

    log.h("B3 - Matched-replica comparison")
    log.p("Not applicable: each GAMA batch draws its own random stream per replica (the MASTER_SEED of the")
    log.p("pipeline is not used by GAMA and the two runs have different seeds), and IA consumes random numbers")
    log.p("in a different order (one draw per passenger agent). Replicas are therefore treated as independent")
    log.p("samples in every CI (independent bootstrap per model).")

    log.h("B4 - Heterogeneity of the IA-AG difference in mean occupancy (strata: direction x stop x departure slot)")
    log.p(f"Replica-bootstrap 95 % CI (500 resamples) of IA - AG per stratum; equivalence margin +-{MARGINS['occupancy_pax']} pax.")
    log.p(f"Demand tertiles from known_data mean occupancy (cut points {tert[0]:.1f} and {tert[1]:.1f} pax),")
    log.p("defined from the empirical reference, independently of the IA-AG comparison.")
    log.p(f"Equivalence of the {len(het)} strata: {het['equivalence'].value_counts().to_dict()}")

    het["abs_d"] = het["d_mean"].abs()

    def grp(df, col):
        g = df.groupby(col, observed=True)
        return pd.DataFrame({
            "strata": g.size(),
            "mean d (IA-AG)": g["d_mean"].mean(),
            "mean |d|": g["abs_d"].mean(),
            "max |d|": g["abs_d"].max(),
            "mean W1": g["W1"].mean(),
            "max W1": g["W1"].max(),
            "% equivalent": g["equivalence"].apply(lambda s: 100 * (s == "EQUIVALENT").mean()),
        }).reset_index()

    for col, title in (("dir", "by direction"), ("peak", "peak (slots 7-9, 17-19) vs off-peak"),
                       ("demand", "by demand tertile (known_data)"), ("dep_slot", "by departure slot")):
        log.p("")
        log.p(title)
        log.table(grp(het, col), "{:.3f}")
    stop_tab = grp(het, ["dir", "stop"])
    log.p("")
    log.p("by stop (route order within direction)")
    order_map = {(dd, s): i for dd, lst in p["AG"]["order"].items() for i, s in enumerate(lst)}
    stop_tab["pos"] = [order_map[(dd, s)] for dd, s in zip(stop_tab["dir"], stop_tab["stop"])]
    log.table(stop_tab.sort_values(["dir", "pos"]).drop(columns="pos"), "{:.3f}")
    worst = het.reindex(het["d_mean"].abs().sort_values(ascending=False).index).head(10)
    log.p("")
    log.p("10 strata with the largest |IA - AG| mean-occupancy difference")
    log.table(worst[keys + ["mean_IA", "mean_AG", "d_mean", "ci_low", "ci_high", "W1", "equivalence"]], "{:.3f}")

    # Trips with and without denied boardings
    rows = []
    for m in ("IA", "AG"):
        v = p[m]["visits"]
        t = v.groupby(["replica", "bus", "travel"]).agg(den=("denied", "sum"), occ=("occ", "mean"), dir=("dir", "first"))
        for has, g in t.groupby(t["den"] > 0):
            rows.append({"model": m, "trips with denied boarding": bool(has), "trips": len(g),
                         "share %": 100 * len(g) / len(t), "mean occupancy over trip": g["occ"].mean(),
                         "denied per trip": g["den"].mean()})
    log.p("")
    log.p("Trips with and without denied boardings")
    log.table(pd.DataFrame(rows), "{:.3f}")

    # Figure 5
    fig, axes = plt.subplots(2, 2, figsize=(13, 8.4))
    from matplotlib.colors import TwoSlopeNorm
    lim = max(0.5, float(het["d_mean"].abs().quantile(0.99)))
    for r, dd in enumerate(("toA", "toB")):
        h = het[het["dir"] == dd]
        stops = p["AG"]["order"][dd][:-1]
        m1 = h.pivot(index="stop", columns="dep_slot", values="d_mean").reindex(index=stops, columns=TIMESLOTS)
        m2 = h.pivot(index="stop", columns="dep_slot", values="W1").reindex(index=stops, columns=TIMESLOTS)
        im1 = axes[r, 0].imshow(m1.values, aspect="auto", cmap=div_cmap(), norm=TwoSlopeNorm(0, -lim, lim))
        im2 = axes[r, 1].imshow(m2.values, aspect="auto", cmap=seq_cmap(), vmin=0,
                                vmax=max(1.0, float(het["W1"].quantile(0.99))))
        for ax, title in ((axes[r, 0], f"{dd}: mean occupancy IA - AG (pax)"),
                          (axes[r, 1], f"{dd}: W1(IA, AG) occupancy (pax)")):
            ax.set_title(title)
            ax.set_yticks(range(len(stops)))
            ax.set_yticklabels(stops, fontsize=7)
            ax.set_xticks(range(0, len(TIMESLOTS), 2))
            ax.set_xticklabels(TIMESLOTS[::2], fontsize=8)
            ax.grid(False)
            ax.set_xlabel("trip departure slot")
        axes[r, 0].set_ylabel("stop (route order)")
        # mark strata that are not equivalent
        ne = h[h["equivalence"] != "EQUIVALENT"]
        for _, z in ne.iterrows():
            if z["stop"] in stops and z["dep_slot"] in TIMESLOTS:
                axes[r, 0].text(TIMESLOTS.index(z["dep_slot"]), stops.index(z["stop"]), "•",
                                ha="center", va="center", fontsize=8, color=INK["primary"])
    fig.colorbar(im1, ax=axes[:, 0], shrink=0.7, label="IA - AG (pax); • = not shown equivalent at ±2 pax")
    fig.colorbar(im2, ax=axes[:, 1], shrink=0.7, label="Wasserstein-1 (pax)")
    fig.suptitle("Figure 5 - IA-AG difference by stop and departure time slot", x=0.42)
    fig.savefig(os.path.join(FIGS, "fig5_ia_ag_difference_heatmap.png"))
    plt.close(fig)
    return het


# --------------------------------------------------------------------------

def fig4(p, k, plt):
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.2), gridspec_kw={"width_ratios": [1.3, 1]})
    ax = axes[0]
    for m in ("IA", "AG"):
        w = np.sort(p[m]["waits"]["wait"].to_numpy())
        idx = np.linspace(0, w.size - 1, 4000).astype(int)
        ax.plot(w[idx] / 60, 1 - (idx + 1) / w.size, color=COLOR[m], label=m)
    ax.set_yscale("log")
    ax.set_xlabel("waiting time (min)")
    ax.set_ylabel("P(W > w)  (log scale)")
    ax.set_title("Survival function of waiting time (all replicas)")
    ax.set_xlim(0, 60)
    ax.legend()
    ax = axes[1]
    qs = [("wait_median", "p50"), ("wait_p90", "p90"), ("wait_p95", "p95"), ("wait_p99", "p99"), ("wait_cvar95", "CVaR95")]
    x = np.arange(len(qs))
    for i, m in enumerate(("IA", "AG")):
        vals = [k[m][c].mean() / 60 for c, _ in qs]
        lo = [np.percentile(k[m][c], 2.5) / 60 for c, _ in qs]
        hi = [np.percentile(k[m][c], 97.5) / 60 for c, _ in qs]
        ax.errorbar(x + (i - 0.5) * 0.25, vals, yerr=[np.subtract(vals, lo), np.subtract(hi, vals)],
                    fmt="o", color=COLOR[m], ms=6, capsize=3, label=m)
    ax.set_xticks(x)
    ax.set_xticklabels([q for _, q in qs])
    ax.set_ylabel("minutes")
    ax.set_title("Replica-level quantiles (mean and 2.5-97.5 % of replicas)")
    ax.legend(loc="upper left")
    ax.grid(axis="x", visible=False)
    fig.suptitle("Figure 4 - Waiting-time distributions, IA vs AG")
    fig.savefig(os.path.join(FIGS, "fig4_waiting_time.png"))
    plt.close(fig)


def fig7(k, plt):
    cols = [("occ_mean", "Mean occupancy (pax)"), ("wait_median", "Median waiting time (s)"),
            ("denied_total", "Denied boardings per day"), ("share_occ_ge60", "Visits with O >= 60 (%)")]
    fig, axes = plt.subplots(2, 2, figsize=(12, 7))
    rng = np.random.default_rng(SEED)
    for ax, (c, label) in zip(axes.flat, cols):
        for m in ("IA", "AG"):
            x = k[m][c].to_numpy(float)
            x = x[rng.permutation(x.size)]
            n = np.arange(1, x.size + 1)
            mean = np.cumsum(x) / n
            sd = np.array([x[:i].std(ddof=1) if i > 1 else np.nan for i in n])
            half = 1.96 * sd / np.sqrt(n)
            ax.plot(n, mean, color=COLOR[m], lw=1.6, label=m)
            ax.fill_between(n, mean - half, mean + half, color=COLOR[m], alpha=0.18, lw=0)
        ax.set_xscale("log")
        ax.set_xlabel("number of replicas (random order)")
        ax.set_title(label)
        ax.legend(loc="upper right")
    fig.suptitle("Figure 7 - Running mean and 95 % CI as replicas accumulate")
    fig.tight_layout()
    fig.savefig(os.path.join(FIGS, "fig7_replica_convergence.png"))
    plt.close(fig)


def main():
    plt = setup_matplotlib()
    k = {m: replica_kpis(m) for m in ("IA", "AG")}
    p = {m: prepared(m) for m in ("IA", "AG")}
    known = load_known()

    log = Log("table2_global_kpis.log", "Table 2 - Global KPI comparison IA vs AG (Analysis B1)")
    b1(log, k)
    log.save()

    log = Log("b2_distributional.log", "Analysis B2 - Distributional comparison IA vs AG")
    b2(log, p)
    log.save()

    log = Log("b3_b4_heterogeneity.log", "Analysis B3-B4 - Matched replicas and heterogeneity of IA-AG differences")
    b4(log, p, k, known["occ"], plt)
    log.save()

    fig4(p, k, plt)
    fig7(k, plt)


if __name__ == "__main__":
    main()
