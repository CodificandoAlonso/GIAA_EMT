# Empirical-only analyses of the C-engine runs

Code in `src/` (select the run with `SIM_RUN=<folder under WEB_DEVEL/data/logs>`, default `SIMULATION_20261012_205659`).
Outputs per run: `logs/<id>/`, `figures/<id>/`. Methods are those of `../sim_comparison` (empirical part only).

| Run | Schedule | Report | W1 mean (pax) | BC ≥ 0.97 | Mean signed error (pax) |
|---|---|---|---|---|---|
| `SIMULATION_20260930_105744` | 163 trips (as the GAMA runs) | `REPORT_20260930_105744.md` | 4.54 | 65.9 % | −3.2 |
| `SIMULATION_20261012_205659` | 167 trips | `REPORT_20261012_205659.md` | 4.87 | 57.3 % | −3.8 |
| AG (GAMA), for reference | 163 trips | `../sim_comparison/REPORT.md` | 6.98 | 36.2 % | −1.9 |
| IA (GAMA), for reference | 163 trips | `../sim_comparison/REPORT.md` | 6.91 | 37.9 % | −2.0 |
