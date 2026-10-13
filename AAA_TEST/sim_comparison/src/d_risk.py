"""
Analysis D - Capacity adequacy and operational risk (plan section 7).

Outputs
    logs/table4_operational_risk.log  D1-D5
    logs/d1_exceedance_strata.csv     P(O >= c), c in 60/70/80, per stratum: empirical, IA, AG (+ CI)
    logs/d1_exceedance_curves.csv     global / peak curves for c = 0..80
    logs/d2_denied_by_stop_slot.csv   share of visits with denied boarding by direction x stop x slot
    logs/d5_decisions.csv             issue / no-issue classification per stratum
    figures/fig3_exceedance_curves.png

"Bus reaches capacity" is simulated O = 80 (occupancy is capped by the model); the empirical
counterpart is the normal tail P(X >= 79.5), which measures how often the observed load would
reach capacity and can exceed it (demand exceeding capacity is not observable in the simulation).
"""

import os

import numpy as np
import pandas as pd
from scipy.stats import norm, spearmanr

from config import (BOOTSTRAP, CAPACITY, COLOR, CROWDING, FIGS, INK, ISSUE_PROB, MARGINS, PEAK_SLOTS, SEED,
                    THRESHOLDS, setup_matplotlib)
from kpis import prepared, replica_kpis
from metrics import Log, boot_weights, ci_mean, diff_ci, equivalence, save_csv
from strata import known_aligned, occ_hist

B_BOOT = 300
K = CAPACITY + 1
CS = (60, 70, 80)


def tail_counts(c: np.ndarray, thr) -> np.ndarray:
    """(R, S, K) -> (R, S) visits with O >= thr."""
    return c[:, :, thr:].sum(-1)


def emp_tail(kn: pd.DataFrame, c: int) -> np.ndarray:
    if c <= 0:
        return np.ones(len(kn))
    return norm.sf((c - 0.5 - kn["mean"].to_numpy()) / kn["std"].to_numpy())


def ratio_boot(num, den, w):
    """(R,) or (R,S) sums -> point, CI low, high, bootstrap draws."""
    with np.errstate(invalid="ignore", divide="ignore"):
        boot = (w @ num) / (w @ den)
    pt = num.sum(0) / den.sum(0)
    return pt, np.nanpercentile(boot, 2.5, axis=0), np.nanpercentile(boot, 97.5, axis=0), boot


# --------------------------------------------------------------------------

def d1(log, hs, kn, plt):
    nvis = hs["IA"]["counts"].sum(-1).sum(0)                 # visits per stratum (all replicas), IA
    wts = {m: boot_weights(1000, b=B_BOOT, seed=SEED + 30 + i) for i, m in enumerate(("IA", "AG"))}
    peak = kn["peak"].to_numpy()
    mix_w = nvis / nvis.sum()
    curves, rows = [], []
    for scope, msk in (("global", np.ones(len(kn), bool)), ("peak", peak), ("off-peak", ~peak)):
        cs = np.arange(0, K)
        emp_w = mix_w[msk] / mix_w[msk].sum()
        emp = np.array([(emp_w * emp_tail(kn[msk], c)).sum() for c in cs])
        cur = {"c": cs, "scope": scope, "EMP": emp}
        for m in ("IA", "AG"):
            cr = hs[m]["counts"][:, msk, :].sum(1)            # (R, K)
            tail = np.cumsum(cr[:, ::-1], -1)[:, ::-1]        # P(O >= c) numerator
            den = cr.sum(-1, keepdims=True) * np.ones((1, K))
            pt, lo, hi, boot = ratio_boot(tail, den, wts[m])
            cur[m], cur[f"{m}_lo"], cur[f"{m}_hi"] = pt, lo, hi
            cur[f"{m}_boot"] = boot
        curves.append(pd.DataFrame({k: v for k, v in cur.items() if not k.endswith("_boot")}))
        for c in THRESHOLDS:
            r = {"scope": scope, "c": c, "empirical": emp[c], "IA": cur["IA"][c], "AG": cur["AG"][c],
                 "IA 95% CI": f"[{100 * cur['IA_lo'][c]:.2f}, {100 * cur['IA_hi'][c]:.2f}]",
                 "AG 95% CI": f"[{100 * cur['AG_lo'][c]:.2f}, {100 * cur['AG_hi'][c]:.2f}]"}
            dlo, dhi = diff_ci(cur["IA_boot"][:, c], cur["AG_boot"][:, c])
            r["IA-AG (pp)"] = 100 * (r["IA"] - r["AG"])
            r["IA-AG 95% CI (pp)"] = f"[{100 * dlo:.2f}, {100 * dhi:.2f}]"
            r["equivalence (+-2 pp)"] = equivalence(100 * dlo, 100 * dhi, MARGINS["prob_pp"])
            r["IA-emp (pp)"] = 100 * (r["IA"] - emp[c])
            r["AG-emp (pp)"] = 100 * (r["AG"] - emp[c])
            rows.append(r)
    allc = pd.concat(curves, ignore_index=True)
    save_csv(allc, "d1_exceedance_curves.csv")
    t = pd.DataFrame(rows)
    for col in ("empirical", "IA", "AG"):
        t[col] = 100 * t[col]
    log.h("D1 - Occupancy exceedance P(O >= c), % of bus-stop visits (terminal visits excluded)")
    log.p("Empirical: known_data normals, mixed with the visit weights of the schedule (identical in both models);")
    log.p("P_emp(O >= c) = P(X >= c - 0.5) for the normal, so for c = 80 it is the probability that observed load would")
    log.p("reach or exceed capacity (demand), while simulated O = 80 means a full bus (occupancy is capped).")
    log.p("CIs: 300 replica-bootstrap resamples. 'IA-emp' / 'AG-emp' in percentage points.")
    log.table(t, "{:.3f}")

    # stratified table
    S = len(kn)
    ss = []
    for c in CS:
        row = kn[["dir", "stop", "dep_slot", "peak", "demand"]].copy()
        row["c"] = c
        row["P_emp"] = emp_tail(kn, c)
        for m in ("IA", "AG"):
            num = tail_counts(hs[m]["counts"], c).astype(float)
            den = hs[m]["counts"].sum(-1).astype(float)
            pt, lo, hi, _ = ratio_boot(num, den, wts[m])
            row[f"P_{m}"], row[f"P_{m}_lo"], row[f"P_{m}_hi"] = pt, lo, hi
        ss.append(row)
    ss = pd.concat(ss, ignore_index=True)
    save_csv(ss, "d1_exceedance_strata.csv")
    log.p("")
    log.p("Stratified (direction x stop x departure slot, 475 strata): absolute error of P(O >= c) against the empirical normal, pp")
    rows = []
    for c in CS:
        g = ss[ss["c"] == c]
        for m in ("IA", "AG"):
            e = 100 * (g[f"P_{m}"] - g["P_emp"]).abs()
            rows.append({"c": c, "model": m, "strata": len(g), "mean |err| pp": e.mean(), "p90 |err|": e.quantile(0.9),
                         "max |err|": e.max(), "strata |err| > 5 pp": int((e > 5).sum()),
                         "strata |err| > 10 pp": int((e > 10).sum()),
                         "emp CI-free: sim CI excludes emp %": 100 * ((g["P_emp"] < g[f"P_{m}_lo"]) | (g["P_emp"] > g[f"P_{m}_hi"])).mean()})
        d = 100 * (g["P_IA"] - g["P_AG"])
        rows.append({"c": c, "model": "IA-AG", "strata": len(g), "mean |err| pp": d.abs().mean(), "p90 |err|": d.abs().quantile(0.9),
                     "max |err|": d.abs().max(), "strata |err| > 5 pp": int((d.abs() > 5).sum()),
                     "strata |err| > 10 pp": int((d.abs() > 10).sum()), "emp CI-free: sim CI excludes emp %": np.nan})
    log.table(pd.DataFrame(rows), "{:.3f}")
    fig3(allc, plt)
    return ss


def fig3(allc, plt):
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.4), sharey=True)
    for ax, scope in zip(axes, ("global", "peak", "off-peak")):
        g = allc[allc["scope"] == scope]
        ax.plot(g["c"], g["EMP"], color=COLOR["EMP"], lw=1.6, ls="--", label="empirical normal")
        for m in ("IA", "AG"):
            ax.plot(g["c"], g[m], color=COLOR[m], label=m)
            ax.fill_between(g["c"], g[f"{m}_lo"], g[f"{m}_hi"], color=COLOR[m], alpha=0.2, lw=0)
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

def d2(log, p, k):
    log.h("D2 - Full buses and denied boarding (per replica, n = 1000 replicas per model)")
    log.p("Empirical records of denied boardings are not available in known_data: IA vs AG comparison only.")
    cols = [("visits_with_denied", "Visits with denied boarding per day", "n"),
            ("denied_total", "Denied passengers per day", "pax"),
            ("share_visits_denied", "Share of visits with denied boarding", "%"),
            ("denied_per_affected_visit", "Mean denied per affected visit", "pax"),
            ("denied_affected_p95", "p95 denied per affected visit (replica value)", "pax"),
            ("share_trips_with_denied", "Trips with denied boarding", "%")]
    w = {m: boot_weights(1000, seed=SEED + 40 + i) for i, m in enumerate(("IA", "AG"))}
    rows = []
    for c, label, u in cols:
        r = {"KPI": label, "unit": u}
        bs = {}
        for m in ("IA", "AG"):
            x = k[m][c].to_numpy(float)
            x = np.nan_to_num(x, nan=np.nanmean(x))
            mean, lo, hi, boot = ci_mean(x, w[m])
            r[m], r[f"{m} 95% CI"] = mean, f"[{lo:.3f}, {hi:.3f}]"
            r[f"{m} p5-p95 of replicas"] = f"[{np.percentile(x, 5):.2f}, {np.percentile(x, 95):.2f}]"
            bs[m] = boot
        lo, hi = diff_ci(bs["IA"], bs["AG"])
        r["IA-AG"], r["diff 95% CI"] = r["IA"] - r["AG"], f"[{lo:.3f}, {hi:.3f}]"
        rows.append(r)
    log.table(pd.DataFrame(rows), "{:.3f}")

    # worst stop x slot
    rows = []
    for m in ("IA", "AG"):
        v = p[m]["visits"]
        v = v[~v["is_last"]]
        g = v.assign(x=v["denied"] > 0, d=v["denied"]).groupby(["dir", "stop", "slot"]).agg(
            visits=("x", "size"), share=("x", "mean"), denied=("d", "sum"))
        g["denied_per_day"] = g["denied"] / 1000
        g["model"] = m
        rows.append(g.reset_index())
    g = pd.concat(rows)
    save_csv(g, "d2_denied_by_stop_slot.csv")
    log.p("")
    log.p("Worst direction x stop x slot cells by denied passengers per service day (point estimates, pooled over replicas)")
    for m in ("IA", "AG"):
        h = g[g["model"] == m].nlargest(8, "denied_per_day")
        log.p(f"  {m}")
        log.table(h[["dir", "stop", "slot", "visits", "share", "denied_per_day"]], "{:.4f}")
    tot = g.pivot_table(index=["dir", "stop", "slot"], columns="model", values="denied_per_day").fillna(0)
    top = lambda m: set(tot[m].nlargest(10).index)
    log.p("")
    log.p(f"Top-10 cells overlap IA vs AG: {len(top('IA') & top('AG'))}/10; Spearman rank correlation of denied/day over cells: "
          f"{spearmanr(tot['IA'], tot['AG'])[0]:.3f}")
    by_stop = g.groupby(["model", "dir", "stop"])["denied_per_day"].sum().unstack(0)
    log.p("")
    log.p("Denied passengers per day by stop (sum over slots), IA vs AG")
    log.table(by_stop.reset_index().assign(ratio=lambda d: d["IA"] / d["AG"]).sort_values("AG", ascending=False).head(12), "{:.3f}")
    by_slot = g.groupby(["model", "slot"])["denied_per_day"].sum().unstack(0)
    log.p("")
    log.p("Denied passengers per day by slot")
    log.table(by_slot.reset_index().assign(ratio=lambda d: d["IA"] / d["AG"]), "{:.3f}")


def d3(log, p):
    log.h("D3 - Queue persistence (runs of consecutive buses with denied boardings at the same stop, same replica)")
    log.p("Arrival times of passengers are not logged, so the queue size and the full queue trajectory cannot be rebuilt;")
    log.p("only persistence is measured: how many successive buses leave passengers behind at one stop.")
    rows = []
    for m in ("IA", "AG"):
        v = p[m]["visits"]
        v = v[~v["is_last"]].sort_values(["replica", "dir", "stop", "time_s"])
        flag = (v["denied"] > 0).to_numpy()
        key = (v["replica"].astype(np.int64) * 100000 + v["stop"].astype(np.int64) * 10 + (v["dir"] == "toB").astype(np.int64)).to_numpy()
        # run ids
        new = np.ones(len(v), bool)
        new[1:] = (key[1:] != key[:-1]) | (flag[1:] != flag[:-1])
        rid = np.cumsum(new)
        runs = pd.DataFrame({"rid": rid[flag], "rep": v["replica"].to_numpy()[flag]}).groupby("rid").agg(len=("rid", "size"), rep=("rep", "first"))
        L = runs["len"]
        per_rep_max = runs.groupby("rep")["len"].max().reindex(range(1000), fill_value=0)
        rows.append({"model": m, "denied visits": int(flag.sum()), "runs": len(L), "mean run length": L.mean(),
                     "P(run >= 2)": (L >= 2).mean(), "P(run >= 3)": (L >= 3).mean(), "P(run >= 5)": (L >= 5).mean(),
                     "max run": int(L.max()), "mean max run per replica": per_rep_max.mean(),
                     "share of denied visits that continue a run %": 100 * (flag.sum() - len(L)) / flag.sum()})
    log.table(pd.DataFrame(rows), "{:.3f}")


def d4(log, hs, p, k, kn):
    log.h("D4 - Tail measures (replica level, mean over 1000 replicas with 95 % bootstrap CI)")
    rows = []
    w = {m: boot_weights(1000, seed=SEED + 50 + i) for i, m in enumerate(("IA", "AG"))}
    vals = {}
    for m in ("IA", "AG"):
        cr = hs[m]["counts"].sum(1)                            # (R, K)
        cdf = np.cumsum(cr, -1) / cr.sum(-1, keepdims=True)
        kk = np.arange(K)
        q = {f"occ_p{x}": (cdf < x / 100).sum(-1) for x in (90, 95, 99)}
        cv = []
        for r in range(cr.shape[0]):
            thr = q["occ_p95"][r]
            sel = kk >= thr
            cv.append((cr[r][sel] * kk[sel]).sum() / cr[r][sel].sum())
        q["occ_cvar95"] = np.array(cv)
        for c, kc in (("wait_p90", "wait_p90"), ("wait_p95", "wait_p95"), ("wait_p99", "wait_p99"), ("wait_cvar95", "wait_cvar95"),
                      ("denied_total", "denied_total")):
            q[c] = k[m][kc].to_numpy(float)
        q["denied_total_p95_over_replicas"] = np.full(1000, np.percentile(k[m]["denied_total"], 95))
        vals[m] = q
    specs = [("occ_p90", "Occupancy p90 (pax)", MARGINS["occupancy_pax"]), ("occ_p95", "Occupancy p95 (pax)", MARGINS["occupancy_pax"]),
             ("occ_p99", "Occupancy p99 (pax)", MARGINS["occupancy_pax"]), ("occ_cvar95", "Occupancy CVaR95 (pax)", MARGINS["occupancy_pax"]),
             ("wait_p90", "Waiting p90 (s)", MARGINS["wait_tail_s"]), ("wait_p95", "Waiting p95 (s)", MARGINS["wait_tail_s"]),
             ("wait_p99", "Waiting p99 (s)", MARGINS["wait_tail_s"]), ("wait_cvar95", "Waiting CVaR95 (s)", MARGINS["wait_tail_s"])]
    for key, label, mg in specs:
        r = {"measure": label}
        bs = {}
        for m in ("IA", "AG"):
            mean, lo, hi, boot = ci_mean(vals[m][key].astype(float), w[m])
            r[m], r[f"{m} 95% CI"] = mean, f"[{lo:.2f}, {hi:.2f}]"
            bs[m] = boot
        lo, hi = diff_ci(bs["IA"], bs["AG"])
        r["IA-AG"], r["diff 95% CI"], r["margin"] = r["IA"] - r["AG"], f"[{lo:.2f}, {hi:.2f}]", mg
        r["equivalence"] = equivalence(lo, hi, mg)
        rows.append(r)
    log.table(pd.DataFrame(rows), "{:.2f}")
    log.p("")
    log.p("Denied passengers per service day: distribution across the 1000 replicas")
    rows = []
    for m in ("IA", "AG"):
        x = k[m]["denied_total"]
        rows.append({"model": m, "mean": x.mean(), "p5": x.quantile(0.05), "p50": x.median(), "p95": x.quantile(0.95), "p99": x.quantile(0.99),
                     "max": x.max(), "CVaR95": x[x >= x.quantile(0.95)].mean()})
    log.table(pd.DataFrame(rows), "{:.1f}")
    log.p("")
    log.p("Worst strata by empirical P(O >= 60), with simulated P and 95 % CI (D1 table)")
    ss = pd.read_csv(os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs", "d1_exceedance_strata.csv"))
    g = ss[ss["c"] == 60].nlargest(10, "P_emp")
    g = g.assign(IA_CI=[f"[{a:.3f}, {b:.3f}]" for a, b in zip(g["P_IA_lo"], g["P_IA_hi"])],
                 AG_CI=[f"[{a:.3f}, {b:.3f}]" for a, b in zip(g["P_AG_lo"], g["P_AG_hi"])])
    log.table(g[["dir", "stop", "dep_slot", "P_emp", "P_IA", "IA_CI", "P_AG", "AG_CI"]], "{:.3f}")
    log.p("")
    log.p("Worst strata by simulated P(O >= 60): IA and AG")
    for m in ("IA", "AG"):
        gm = ss[ss["c"] == 60].nlargest(8, f"P_{m}")
        log.p(f"  {m}")
        log.table(gm[["dir", "stop", "dep_slot", "P_emp", f"P_{m}", f"P_{m}_lo", f"P_{m}_hi"]], "{:.3f}")


def d5(log, ss):
    log.h(f"D5 - Decision agreement: issue if P(O >= {CROWDING}) >= {ISSUE_PROB} per direction x stop x departure slot")
    g = ss[ss["c"] == CROWDING].reset_index(drop=True).copy()
    for m in ("IA", "AG"):
        g[f"flag_{m}"] = g[f"P_{m}"] >= ISSUE_PROB
        g[f"unc_{m}"] = (g[f"P_{m}_lo"] < ISSUE_PROB) & (g[f"P_{m}_hi"] >= ISSUE_PROB)
    g["flag_EMP"] = g["P_emp"] >= ISSUE_PROB
    save_csv(g, "d5_decisions.csv")
    n = len(g)
    log.p(f"Strata flagged: empirical {int(g['flag_EMP'].sum())}/{n}, IA {int(g['flag_IA'].sum())}/{n}, AG {int(g['flag_AG'].sum())}/{n}.")
    rows = []
    for ref, other in (("AG", "IA"), ("EMP", "IA"), ("EMP", "AG")):
        a, b = g[f"flag_{ref}"], g[f"flag_{other}"]
        agree = (a == b).mean()
        po, pe = agree, a.mean() * b.mean() + (1 - a.mean()) * (1 - b.mean())
        kappa = (po - pe) / (1 - pe) if pe < 1 else np.nan
        pr, po_ = (g["P_emp"] if ref == "EMP" else g[f"P_{ref}"]), g[f"P_{other}"]
        top = lambda s: set(s.nlargest(10).index)
        rows.append({"reference": ref, "compared": other, "agreement %": 100 * agree, "kappa": kappa,
                     "false negatives (ref flags, other not)": int((a & ~b).sum()),
                     "false positives (other flags, ref not)": int((~a & b).sum()),
                     "Spearman rho (P60)": spearmanr(pr, po_)[0], "top-10 overlap": len(top(pr) & top(po_)),
                     "top-20 overlap": len(set(pr.nlargest(20).index) & set(po_.nlargest(20).index))})
    log.table(pd.DataFrame(rows), "{:.3f}")
    log.p("")
    log.p(f"Strata whose simulated CI straddles the {ISSUE_PROB} rule (flag not stable across replica resampling): "
          f"IA {int(g['unc_IA'].sum())}, AG {int(g['unc_AG'].sum())}")
    diff = g[g["flag_IA"] != g["flag_AG"]]
    log.p(f"Strata where IA and AG disagree: {len(diff)}")
    if len(diff):
        log.table(diff[["dir", "stop", "dep_slot", "P_emp", "P_IA", "P_AG"]], "{:.3f}")
    miss = g[g["flag_EMP"] & ~(g["flag_IA"] | g["flag_AG"])]
    log.p("")
    log.p(f"Empirically flagged strata missed by BOTH models: {len(miss)}")
    for ref in ("IA", "AG"):
        fn = g[g["flag_EMP"] & ~g[f"flag_{ref}"]]
        log.p(f"  {ref} false negatives by departure slot: {fn['dep_slot'].value_counts().sort_index().to_dict()}")
        fp = g[~g["flag_EMP"] & g[f"flag_{ref}"]]
        log.p(f"  {ref} false positives by departure slot: {fp['dep_slot'].value_counts().sort_index().to_dict()}")


def main():
    plt = setup_matplotlib()
    hs = {m: occ_hist(m) for m in ("IA", "AG")}
    p = {m: prepared(m) for m in ("IA", "AG")}
    k = {m: replica_kpis(m) for m in ("IA", "AG")}
    kn = known_aligned(hs["IA"]["index"])
    log = Log("table4_operational_risk.log", "Table 4 - Operational risk (Analysis D)")
    ss = d1(log, hs, kn, plt)
    d2(log, p, k)
    d3(log, p)
    d4(log, hs, p, k, kn)
    d5(log, ss)
    log.save()


if __name__ == "__main__":
    main()
