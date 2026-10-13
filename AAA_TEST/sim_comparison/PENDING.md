# IA vs AG comparison: status and what's left

Plan: `formal_analysis_plan.md`.

| Model | Simulation | Replicas |
|---|---|---|
| AG (aggregate) | `SIMULATION_20261012_170524` | 1,000 |
| IA (passenger agents) | `SIMULATION_20261012_172453` | 1,000 |

Empirical reference: `WEB_DEVEL/data/known_data`, used as is.

Last commit: `b869f2ee`.

## Done

| Plan item | Output | Status |
|---|---|---|
| Loader, cache and replica KPIs | `src/load.py`, `src/kpis.py`, `src/metrics.py`, `src/config.py` | Done. Parsed data is cached in `cache/`, which git ignores. |
| Pre-specified margins and thresholds | `src/config.py`, written at the top of every log | Done. Fixed before any comparison was computed. |
| **A, Table 1** (integrity) | `logs/table1_data_quality.log`, `logs/a2_violations_*.csv` | Done. |
| **B1, Table 2** (global KPIs) | `logs/table2_global_kpis.log` / `.csv` | Done. 24 of 26 KPIs equivalent; inconclusive: waiting-time p99 and denied boardings per day. |
| **B2** (distributional comparison) | `logs/b2_distributional.log` / `.csv`, `logs/b2_strata_*.csv` | Written, **not reviewed yet**. |
| **B3** (matched replicas) | text in `b3_b4_heterogeneity.log` | Written in code. Not applicable: the replicas aren't matched, so they're treated as independent samples. |

### Findings so far

- **Coverage:** both runs are complete and use the same service. Every replica has 163 trips and 2,202 stop visits, with no duplicates or missing values.
- **IA loses passengers** in 887 visits (0.04 %, in 589 replicas). About 6 passengers per replica leave the bus without being counted as alightings. AG conserves flows exactly.
- **IA leaves passengers behind on buses with room.** 5.2 % of IA waiting times are longer than the time since a previous bus that had room, against 2.0 % in AG.
  - In AG the excess is about one dwell time (a timing convention).
  - In IA it's minutes, and 60 % of the cases happen when two buses pass less than 2 min apart. The cause is the IA boarding protocol: only passengers who answer the arrival broadcast within 3 cycles get on.
- **Global KPIs:**
  - Equivalent: occupancy (all statistics), travel time, trip duration (IA +26 s), boardings and alightings, median waiting time, bunching, crowding shares.
  - IA has fewer denied boardings: −11 % per day, CI −56.7 to −25.3 against a ±36.4 margin (inconclusive).
  - IA has a lower waiting-time p99: −61 s, CI −80 to −41 against a ±60 margin (inconclusive).
  - IA's delayed departures are also 1 min less delayed on average (4.3 vs 5.4 min). That KPI has no margin.

## What's left

### Analysis B (in progress)
- [ ] Run `src/b_ia_vs_ag.py` again. The B4 fix (`abs_d` column) is committed but hasn't run, so `logs/b3_b4_heterogeneity.log` doesn't exist yet.
- [ ] Review `b2_distributional.log`: W1 and Bhattacharyya per variable and stratum, quantile and tail differences.
- [ ] Review B4: per-stratum IA − AG with bootstrap CIs, by direction, stop, slot, peak, demand tertile, and trips with or without denied boarding.
- [ ] Check the figures:
  - Fig 4, waiting-time distributions;
  - Fig 5, IA − AG heatmap by stop × slot;
  - Fig 7, convergence as replicas accumulate.

### Analysis C: validation against `known_data` (not started), Table 3 and Figs 1–2
- [ ] **C1, occupancy:** for each direction × stop × departure slot, compare each model with N(μ, σ) from `known_data`.
  - Mean and SD error, median and p90.
  - W1 against the normal.
  - Bhattacharyya with the project method and the ≥ 0.97 acceptance rule.
  - P(O ≥ c).
- [ ] **Primary estimand:** Δ_s = D_IA,s − D_AG,s using W1, with a replica-bootstrap CI for the mean Δ.
- [ ] **C2, boardings/alightings:** `known_data` has no reference for these. The table will say so, and the comparison stays IA vs AG only (B2).
- [ ] **C3, segment travel times:** against the `known_data` normals. Mean error, MAE, quantile differences, W1, coverage of the empirical 95 % interval, residual map. Also state that times are sampled from the fitted distributions.
- [ ] **C4, waiting times:** no empirical reference; reported as a model output only.
- [ ] **C5, reporting levels:**
  - global;
  - stratified;
  - operational extremes: peak slots, high-demand stops, strata with mean ≥ 40.
  - Also: share of strata accepted, and the size of the error in strata that fail.
- [ ] **Fig 1:** occupancy distributions (empirical normal, IA, AG) for representative peak and off-peak strata.
- [ ] **Fig 2:** error map by stop × slot for each model.

### Analysis D: operational risk (not started), Table 4 and Fig 3
- [ ] **D1, exceedance:** curves of P(O ≥ c) for c = 0–80 (empirical normal mixture, IA, AG), global and peak. Stratified table at 60 / 70 / 80 with CIs. Separate "bus reaches capacity" from "demand exceeds capacity".
- [ ] **D2, denied boardings:** per replica: visits with denials, passengers denied, mean and p95 per affected visit, worst stops and slots.
- [ ] **D3, queues:** persistence only (runs of consecutive full buses at the same stop). The full queue path can't be rebuilt because arrival times aren't logged.
- [ ] **D4, tails:** p90/p95/p99 and CVaR95 for occupancy, waits and denied boardings, plus the worst stop/slot combinations with CIs.
- [ ] **D5, decision agreement:** apply the rule P(O ≥ 60) ≥ 0.10 per stratum to the empirical data, IA and AG. Report agreement, false negatives and false positives against the empirical data, and how much the top-10 rankings overlap.
- [ ] **Fig 3:** exceedance curves.

### Analysis E: computational cost (not started), Table 5 and Fig 6
- [ ] Wall-clock time from the pipeline logs only: AG 36 min 13 s vs IA 2 h 26 min 53 s, same machine, 8 cores, not overlapping. That gives speedup S ≈ 4.06 and a 75 % reduction. It's one measurement per model and includes startup and file writing.
- [ ] Time per replica, throughput and output size per replica (RESULTS / PASSENGERS / EVENTS).
- [ ] No CPU, memory or energy metrics, as you asked.
- [ ] **Fig 6:** runtime against empirical error (mean W1), global and peak.

### Analysis F: robustness (not started), Table 6
- [ ] **F1/F2:** IA − AG differences and empirical fit by direction, peak, demand tertile, terminal-adjacent stops, and high-demand boarding and alighting stops (taken from the input distributions, not the outputs).
- [ ] **F3:** repeat with other metrics (W1, Kolmogorov–Smirnov, normal Bhattacharyya, project-method Bhattacharyya) and other acceptance thresholds (Bhattacharyya 0.90–0.99, W1 1–5 pax), and check whether the preferred model changes.
- [ ] **F4:** not done. It needs new simulations with perturbed inputs.
- [ ] **F5:** short external-validity statement: one route, workdays only, validation within the calibration period.

### Report
- [ ] `REPORT.md` in English: answers to RQ1–RQ5, Tables 1–6 and Figs 1–7 as in plan section 11, and which outcome of section 13 applies (A–E). Add statistical vs operational significance for each main result.
- [ ] `run_all.py` to regenerate everything (~5–10 min with the cache).
- [ ] Commit and push.

## How to run what exists

```bash
cd AAA_TEST/sim_comparison/src
python3 load.py          # builds the cache (~1.5 min)
python3 a_integrity.py   # Table 1
python3 b_ia_vs_ag.py    # Table 2, B2, B3-B4, Figs 4, 5, 7
```
