"""
Analysis E - Computational cost (plan section 8).

Only wall-clock times written by the pipeline logs (log_result_*.log) are used. CPU, memory and energy
are deliberately not reported (not requested). Both runs: same machine, 8 GAMA cores, 1000 replicas,
byte-identical inputs, run one after the other (IA's simulation phase started when AG's pipeline had
finished; both logs say 'Concurrent runs at start: 1').

Outputs
    logs/table5_computational_cost.log (+ .csv)
    figures/fig6_efficiency_fidelity.png
"""

import glob
import os
import re

import numpy as np
import pandas as pd

from config import COLOR, FIGS, INK, SIM_ROOT, SIMS, setup_matplotlib
from kpis import prepared
from metrics import Log, save_csv


def hms(txt: str) -> int:
    h = re.search(r"(\d+)h", txt)
    m = re.search(r"(\d+)m", txt)
    s = re.search(r"(\d+)s", txt)
    return 3600 * int(h.group(1) if h else 0) + 60 * int(m.group(1) if m else 0) + int(s.group(1) if s else 0)


def parse(model: str) -> dict:
    path = glob.glob(os.path.join(SIM_ROOT, SIMS[model], "log_result_*.log"))[0]
    txt = re.sub(r"\x1b\[[0-9;]*m", "", open(path).read())
    out = {}
    for key, pat in (("simulation_s", r"3\. Simulation:\s+([0-9hms ]+)"), ("extract_s", r"5\. Data extraction & analysis:\s+([0-9hms ]+)"),
                     ("pipeline_s", r"TOTAL PIPELINE TIME:\s+([0-9hms ]+)")):
        m = re.search(pat, txt)
        out[key] = hms(m.group(1)) if m else np.nan
    out["start"] = re.search(r"Starting GAMA headless batch execution", txt) is not None
    out["cores"] = int(re.search(r"HPC cores:\s+(\d+)\s*\n", txt.split("SIMULATION EXECUTION PIPELINE")[1]).group(1))
    out["concurrent"] = re.search(r"Concurrent runs at start:\s+(\d+)", txt).group(1)
    ts = re.findall(r"\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\]", txt)
    out["t_first"], out["t_exec"], out["t_last"] = ts[0], re.search(r"\[([\d\- :]+)\][^\n]*Phase 1: Simulation", txt).group(1), ts[-1]
    return out


def main():
    plt = setup_matplotlib()
    ag, ia = parse("AG"), parse("IA")
    log = Log("table5_computational_cost.log", "Table 5 - Computational cost (Analysis E)")
    log.h("E1 - Wall-clock time (one measurement per model)")
    log.p("Source: pipeline logs. Simulation phase = GAMA headless batch (includes JVM start-up and the writing of the")
    log.p("RESULTS / EVENTS / PASSENGERS files of 1000 replicas). Pipeline = preparation + simulation + extraction.")
    log.p("Single run per model: no variance can be estimated, so no CI and no significance claim.")
    log.p(f"AG: execution phase began {ag['t_exec']}, log ends {ag['t_last']}; IA: execution phase began {ia['t_exec']}, log ends {ia['t_last']}.")
    log.p(f"Concurrent runs reported at start: AG {ag['concurrent']}, IA {ia['concurrent']}. IA preparation started {ia['t_first']} (before AG finished at {ag['t_last']})")
    log.p("but its simulation phase started only after the AG pipeline ended, so the two simulation phases did not overlap.")
    rows = []
    for name, key in (("Simulation phase", "simulation_s"), ("Whole pipeline", "pipeline_s"), ("Data extraction", "extract_s")):
        a, i = ag[key], ia[key]
        rows.append({"phase": name, "AG (s)": a, "IA (s)": i, "AG (h:mm:ss)": f"{a // 3600}:{a % 3600 // 60:02d}:{a % 60:02d}",
                     "IA (h:mm:ss)": f"{i // 3600}:{i % 3600 // 60:02d}:{i % 60:02d}",
                     "speedup S = T_IA/T_AG": i / a, "reduction R = 1 - T_AG/T_IA (%)": 100 * (1 - a / i)})
    t = pd.DataFrame(rows)
    save_csv(t, "table5_computational_cost.csv")
    log.table(t, "{:.2f}")
    log.p("")
    log.p("Throughput and cost per replica (simulation phase, 1000 replicas, 8 cores)")
    thr = pd.DataFrame([{"model": m, "replicas/hour": 3600 * 1000 / d["simulation_s"], "wall-clock s per replica": d["simulation_s"] / 1000,
                         "core-seconds per replica (8 cores x wall-clock; allocated, not measured CPU)": 8 * d["simulation_s"] / 1000}
                        for m, d in (("AG", ag), ("IA", ia))])
    log.table(thr, "{:.2f}")
    log.p("Per-replica wall-clock distribution (median, IQR) is not available: the pipeline logs only the total of the batch.")

    log.h("E2 - Output size and workload")
    pa, pi = prepared("AG"), prepared("IA")
    rows = []
    for k in ("RESULTS", "EVENTS", "PASSENGERS"):
        rows.append({"file set": k, "AG MB": pa["bytes"][k] / 2 ** 20, "IA MB": pi["bytes"][k] / 2 ** 20,
                     "AG KB per replica": pa["bytes"][k] / 1000 / 1024, "IA KB per replica": pi["bytes"][k] / 1000 / 1024})
    log.table(pd.DataFrame(rows), "{:.2f}")
    log.p("")
    log.p(f"Bus-stop visits per replica: AG {len(pa['visits']) // 1000}, IA {len(pi['visits']) // 1000} (same service).")
    log.p(f"Boarding passengers per replica (passenger entities created by the model that board): AG {len(pa['waits']) / 1000:.0f}, IA {len(pi['waits']) / 1000:.0f}.")
    log.p("CPU time, peak memory, agent messages and protocol exchanges: not measured (not requested / not logged); not estimated.")

    log.h("E3 - Scaling")
    log.p("Only one operating point exists (same demand, route and 1000 replicas). Scaling with passenger population, route")
    log.p("size or replica count cannot be inferred from it; a controlled scaling experiment would be a new experiment (not done).")

    log.h("E4 - Efficiency vs fidelity")
    c1 = pd.read_csv(os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs", "c1_occupancy_strata.csv"))
    rows = []
    for scope, msk in (("global", lambda d: np.ones(len(d), bool)), ("peak", lambda d: d["peak"].to_numpy()), ("mean >= 40 pax", lambda d: (d["emp_mean"] >= 40).to_numpy())):
        for m, d in (("AG", ag), ("IA", ia)):
            h = c1[c1["model"] == m]
            g = h[msk(h)]
            rows.append({"scope": scope, "model": m, "runtime (h)": d["simulation_s"] / 3600, "mean W1 vs empirical (pax)": g["W1"].mean(),
                         "accepted BC %": 100 * g["accept_BC"].mean()})
    tt = pd.DataFrame(rows)
    log.table(tt, "{:.3f}")
    g = tt[tt["scope"] == "global"].set_index("model")
    gain = g.loc["AG", "mean W1 vs empirical (pax)"] - g.loc["IA", "mean W1 vs empirical (pax)"]
    extra_h = g.loc["IA", "runtime (h)"] - g.loc["AG", "runtime (h)"]
    log.p("")
    log.p(f"IA needs {extra_h:.2f} h more wall-clock for 1000 replicas and reduces the mean occupancy W1 by {gain:.3f} pax "
          f"({100 * gain / g.loc['AG', 'mean W1 vs empirical (pax)']:.1f} % of the AG error), against a 2 pax tolerance (see Table 3 for the CI).")
    log.save()

    fig, axes = plt.subplots(1, 3, figsize=(13, 4), sharey=False)
    for ax, scope in zip(axes, ("global", "peak", "mean >= 40 pax")):
        h = tt[tt["scope"] == scope]
        for _, r in h.iterrows():
            ax.scatter(r["runtime (h)"], r["mean W1 vs empirical (pax)"], s=110, color=COLOR[r["model"]], zorder=3)
            ax.annotate(r["model"], (r["runtime (h)"], r["mean W1 vs empirical (pax)"]), textcoords="offset points", xytext=(8, 6))
        ax.set_xlim(0, 2.8)
        ax.set_ylim(0, max(10, h["mean W1 vs empirical (pax)"].max() * 1.15))
        ax.axhline(2.0, color=INK["secondary"], lw=0.8, ls=":")
        ax.set_title(scope)
        ax.set_xlabel("wall-clock for 1000 replicas (h)")
    axes[0].set_ylabel("mean W1 of occupancy vs known_data (pax)")
    fig.suptitle("Figure 6 - Runtime vs empirical error (dotted: 2 pax acceptance tolerance)")
    fig.tight_layout()
    fig.savefig(os.path.join(FIGS, "fig6_efficiency_fidelity.png"))
    plt.close(fig)


if __name__ == "__main__":
    main()
