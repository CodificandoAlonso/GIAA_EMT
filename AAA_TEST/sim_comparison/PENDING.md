# IA vs AG comparison: status

Plan: `formal_analysis_plan.md`. Results and conclusions: `REPORT.md`. Regenerate everything with `python3 src/run_all.py` (about 1 min with the cache, about 3 min without).

| Plan item | Output | Status |
|---|---|---|
| A, Table 1 | `logs/table1_data_quality.log` | Done |
| B1-B4, Table 2, Figs 4, 5, 7 | `logs/table2_*`, `b2_*`, `b3_b4_heterogeneity.log` | Done and reviewed (B3 not applicable: replicas not matched) |
| C1-C5, Table 3, Figs 1, 2 | `logs/table3_empirical_validation.log`, `c1_*`, `c3_*` | Done |
| D1-D5, Table 4, Fig 3 | `logs/table4_operational_risk.log`, `d1_*`, `d2_*`, `d5_*` | Done |
| E, Table 5, Fig 6 | `logs/table5_computational_cost.log` | Done (wall-clock only, one measurement per model) |
| F1-F3, F5, Table 6 | `logs/table6_robustness.log` | Done |
| Report and `run_all.py` | `REPORT.md`, `src/run_all.py` | Done |

## Not done
- **F4** (input-calibration perturbation): needs new simulations with perturbed inputs.
- **E3** (scaling with passenger population): needs a controlled experiment with different demand levels.
- **Cause of the empirical misfit**: the models pile up mass at the capacity cap (O = 80) and underestimate late-slot occupancy; this has not been isolated (cap, calibration, or the fitted-normal reference).
- **Paired-replica analysis** (B3): would need runs with aligned random streams.
