# Formal Statistical Analysis Plan: Passenger-Agent Granularity in Bus Simulation

## 1. Objective and research questions

The study compares two implementations of the same bus-route simulation:

- **Individual-agent model (IA):** each passenger is represented as an agent.
- **Aggregate model (AG):** passenger quantities are represented through counts and associated timestamps where needed.

Both models are evaluated over 1,000 Monte Carlo replicas using the same route, schedule, capacity assumptions, calibrated input distributions and output definitions.

The primary objective is to determine whether the individual representation provides a meaningful improvement in empirical fidelity or operationally relevant outputs that justifies its additional computational cost.

### RQ1 — Agreement between implementations

Do IA and AG produce equivalent distributions of occupancy, waiting time, travel time, boarding, alighting, denied boarding and service-level indicators?

### RQ2 — Empirical validity

How accurately does each implementation reproduce the distributions observed in the operator's operational records, at both route-wide and stop/time-slot levels?

### RQ3 — Operational consequences

Do discrepancies between implementations or between simulated and observed data change conclusions about crowding, capacity exceedance, denied boarding, waiting time or service regularity?

### RQ4 — Computational efficiency

What computational cost is associated with the individual-agent representation, and how does that cost relate to passenger population, interaction volume and output fidelity?

### RQ5 — Robustness and heterogeneity

Are the conclusions consistent across directions, stops, time slots, demand levels and other relevant operating conditions?

---

## 2. Data structure and unit of analysis

### 2.1. Required identifiers

Retain, where available:

- `model`: IA or AG.
- `replica_id`: Monte Carlo replication identifier.
- `service_date` or the corresponding empirical day/type.
- `bus_id`: physical bus identifier.
- `trip_id`: scheduled trip identifier.
- `direction`.
- `stop_id` and the stop sequence within the direction.
- `time_slot`.
- `scheduled_time`, `arrival_time` and/or `departure_time`.
- `seed` or random-stream identifier, if recorded.

The primary observational unit for stop-level analysis is a **bus visit to a stop within a particular replica**. A replica is the natural unit for uncertainty estimation when the objective is to quantify variation between complete simulated service days.

The individual passengers who board during a visit are nested within that visit. They must not be treated as independent replications of the entire simulation.

### 2.2. Principal outcome variables

Use the variables available in the CSV files, with consistent definitions across IA, AG and empirical data.

| Domain | Variables |
|---|---|
| Passenger flows | Boardings, alightings, denied boardings |
| Bus load | Occupancy after each stop; occupancy before the stop if available |
| Passenger experience | Waiting time for each passenger who boards |
| Bus operation | Travel time between consecutive stops; stop dwell time if available |
| Schedule performance | Departure delay, headway regularity, trip duration |
| Computational performance | Wall-clock runtime, peak memory, CPU time if recorded |
| Diagnostics | Invalid occupancy, capacity violations, missing values, inconsistent passenger-flow balances |

Before analysis, document units, timing conventions, missing-value handling, whether occupancy is measured before or after stop operations, and whether terminal stops follow the same definitions as intermediate stops.

### 2.3. Empirical reference data

Distinguish the following datasets:

1. **Empirical reference:** observed operational records.
2. **IA simulation:** output from the individual-agent implementation.
3. **AG simulation:** output from the aggregate implementation.

Do not treat simulated records as independent empirical observations. The 1,000 replicas estimate the stochastic behaviour of each model; they do not increase the number of real operating days observed.

If the simulation inputs are calibrated from the same operational period used for validation, explicitly describe the evaluation as **in-sample or calibration-period validation**, not independent out-of-sample validation.

---

## 3. Primary estimands and hypotheses

### 3.1. Primary estimand

The primary estimand is the difference in empirical fidelity between IA and AG for the distribution of occupancy at bus-stop visits, stratified by stop and time slot.

For each stratum \(s\), define:

\[
D_{m,s}=d\!\left(F_{m,s},F_{\mathrm{emp},s}\right),
\qquad m\in\{\mathrm{IA},\mathrm{AG}\},
\]

where \(F_{m,s}\) is the simulated occupancy distribution for model \(m\), \(F_{\mathrm{emp},s}\) is the empirical distribution, and \(d\) is a prespecified distributional distance.

The primary comparative quantity is:

\[
\Delta_s=D_{\mathrm{IA},s}-D_{\mathrm{AG},s}.
\]

Negative values favour IA; positive values favour AG. Aggregate results should summarise the distribution of \(\Delta_s\) across relevant strata, without allowing high-volume stops to conceal poor performance elsewhere.

Use a prespecified primary distance, such as the Wasserstein-1 distance, and report the Bhattacharyya coefficient as a complementary measure consistent with the existing manuscript. The empirical support, discretisation and estimation procedure must be identical across models.

### 3.2. Hypotheses

**H1 — Distributional equivalence of implementations.** IA and AG produce sufficiently similar occupancy distributions and operational KPIs within prespecified practical tolerances.

**H2 — Empirical fidelity.** At least one implementation reproduces observed occupancy distributions adequately, including important peak-demand strata.

**H3 — Operational equivalence.** The implementations lead to equivalent estimates of operationally relevant outcomes, such as the probability of a full bus or denied boarding.

**H4 — Computational advantage.** AG requires less runtime and memory than IA under comparable execution conditions.

**H5 — Conditional differences.** Any differences between implementations depend on demand intensity, stop, direction, time slot or passenger population.

Equivalence must not be inferred merely because a conventional difference test is nonsignificant. Define practical equivalence margins before examining the final comparison, and use confidence intervals or an appropriate equivalence procedure.

---

## 4. Analysis A — Data integrity and simulation invariants

This analysis is mandatory before comparing performance.

### A1. Completeness and coverage

For each model and replica, calculate:

- Number of trips completed.
- Number of expected and observed bus-stop visits.
- Missingness rates by variable, stop, direction and time slot.
- Duplicate keys for replica/trip/stop records.
- Distribution of records per replica.
- Whether the two implementations cover exactly the same scheduled service.

Report all systematic differences in coverage. Do not silently discard failed or incomplete replicas.

### A2. Passenger-flow conservation

For every bus-stop visit, verify the appropriate identity:

\[
O_{i}=O_{i-1}+B_i-A_i,
\]

where \(O_i\) is occupancy after the stop, \(B_i\) is the number boarding and \(A_i\) is the number alighting.

If occupancy is defined before or after a different event in the CSV, adjust the identity to match the actual event order.

Check:

- Occupancy is nonnegative.
- Occupancy does not exceed vehicle capacity, unless an explicitly documented data or modelling convention permits otherwise.
- Alightings do not exceed the number on board before alighting.
- Boardings, alightings and denied boardings are nonnegative integers where applicable.
- Occupancy transitions are consistent between consecutive stops.
- The terminal-stop rules are satisfied.

Report the number and proportion of violated records by model and replica. These are model-validity checks, not observations to remove merely because they disagree with expectations.

### A3. Waiting-time consistency

Where passenger-level boarding records exist, verify that each waiting time is nonnegative and consistent with the recorded passenger arrival and boarding times, if both timestamps are available.

Compare passenger-level waiting-time summaries with independently reconstructed summaries from the aggregate implementation. Check whether passengers who cannot board remain in the queue and retain their accumulated waiting time.

### A4. Time and schedule consistency

Verify that travel times, dwell times, trip duration and schedule delays use consistent definitions and time units. Check for negative durations, missing transitions, impossible timestamp orderings and discontinuities around time-slot boundaries.

**Output:** a data-quality table by model, including completeness, invariant violations and excluded records with explicit reasons.

---

## 5. Analysis B — Controlled comparison between IA and AG

This analysis isolates the effect of passenger representation.

### B1. Global KPI comparison

For each replica, calculate the same KPIs for IA and AG:

- Mean and median occupancy.
- Occupancy standard deviation and selected quantiles.
- Mean and median waiting time.
- Waiting-time quantiles and upper-tail measures.
- Mean travel time and trip duration.
- Mean departure delay and headway regularity.
- Total boardings, alightings and denied boardings.
- Proportion of bus-stop visits at capacity or above operational crowding thresholds.
- Number of completed trips and bus-stop visits.

For every KPI, report:

1. The mean or median across replicas.
2. A 95% confidence interval.
3. The absolute IA–AG difference.
4. The relative difference, where meaningful and numerically stable.
5. A standardised effect size where appropriate.
6. A prespecified equivalence assessment.

Avoid relying exclusively on relative differences when the reference value is near zero.

### B2. Distributional comparison

Compare IA and AG distributions of:

- Occupancy.
- Passenger waiting time.
- Travel time.
- Departure delay.
- Denied boarding counts.
- Boardings and alightings per visit.

Recommended measures:

- **Wasserstein-1 distance:** interpretable in the original measurement units.
- **Bhattacharyya coefficient:** overlap between distributions, reported with its estimation method.
- **Quantile differences:** particularly the median, 90th, 95th and 99th percentiles where sample size supports them.
- **Tail-probability differences:** probabilities of exceeding operational thresholds.

Do not calculate distributional similarity only after pooling every stop and time slot. Report stratified results to prevent opposite errors from cancelling each other out.

### B3. Matched-replica comparison

If the two models share random seeds or can be run with genuinely matched random streams, calculate paired differences for each replica:

\[
\delta_r=Y_{\mathrm{IA},r}-Y_{\mathrm{AG},r}.
\]

Report the mean paired difference and its confidence interval. Use a paired bootstrap over replica pairs or a suitable paired statistical procedure.

A shared numerical seed does not guarantee matched stochastic inputs if the implementations consume random numbers in different orders. Document whether the streams are genuinely aligned. If not, treat replicas as independent samples.

### B4. Heterogeneity of implementation differences

Repeat the comparison by:

- Direction.
- Stop.
- Time slot.
- Peak versus off-peak periods, defined in advance.
- Low, medium and high demand strata.
- Low and high occupancy strata.
- Trips with and without denied boardings.

Use heatmaps or compact distribution plots to show where the models diverge. Summarise both the average discrepancy and the worst-performing operationally important strata.

**Output:** a KPI comparison table, distributional-distance table, and stop/time-slot heterogeneity figure.

---

## 6. Analysis C — Empirical validation

Evaluate each implementation independently against the observed operational records. Do not infer empirical validity from IA–AG agreement.

### C1. Occupancy distributions

For each stop, direction and relevant time slot, compare the simulated occupancy distribution with the empirical distribution.

Report:

- Empirical and simulated means.
- Standard deviations.
- Median and upper quantiles.
- Wasserstein-1 distance.
- Bhattacharyya coefficient.
- Empirical and simulated probabilities of exceeding selected occupancy thresholds.
- Number of observed records and simulated records contributing to each estimate.

Where occupancy is discrete, document the support and binning used to calculate distributional overlap. Apply the same procedure to all datasets.

### C2. Boarding and alighting distributions

Compare observed and simulated distributions of boardings and alightings per bus-stop visit, stratified by stop and time slot.

Assess:

- Mean and variance.
- Zero counts and other frequent low counts.
- Upper-tail behaviour.
- Distributional distance.
- Calibration of extreme counts.
- Systematic overprediction or underprediction.

Because the model's alighting distributions are explicitly calibrated from observed operations, distinguish goodness of fit to the calibration data from generalisation to independent days.

### C3. Travel-time distributions

Compare simulated and empirical segment travel times by segment, direction and time slot.

Report:

- Mean error and mean absolute error.
- Median and selected quantile differences.
- Wasserstein-1 distance.
- Coverage of empirical travel-time intervals by simulated prediction intervals, if constructed.
- Residual patterns across the route and day.

If travel times are sampled directly from fitted distributions, state that validation evaluates the sampling and calibration procedure rather than an independently learned traffic model.

### C4. Waiting-time validation

Compare simulated waiting times with observed waiting times only if the operational dataset contains an appropriate empirical reference at the same level of measurement.

If passenger-level observed waiting times are unavailable, waiting time is a derived simulation output rather than an independently validated quantity. It can still be compared between IA and AG and assessed for internal consistency, but should not be described as empirically validated.

### C5. Validation aggregation

Provide three levels of reporting:

1. **Global:** pooled summary measures for the route.
2. **Stratified:** stop, direction and time-slot results.
3. **Operational extremes:** peak periods, high-demand stops and high-occupancy events.

Report both the proportion of strata meeting the prespecified acceptance criterion and the magnitude of error in strata that fail it.

**Output:** separate empirical-validation tables for occupancy, passenger flows and travel times, plus a spatial/temporal error map.

---

## 7. Analysis D — Capacity adequacy and operational risk

This analysis translates model behaviour into transport-management consequences.

### D1. Occupancy exceedance probabilities

For a set of operationally meaningful thresholds \(c\), estimate:

\[
P(O\ge c)
\]

for empirical data, IA and AG, stratified by stop and time slot. Candidate thresholds include the vehicle's nominal capacity and any operational crowding thresholds used by the operator.

Report absolute probability differences, relative differences where stable, and confidence intervals. Distinguish the probability of a bus reaching capacity from the probability that demand exceeds capacity.

### D2. Full buses and denied boarding

For each replica, calculate:

- Number of visits with at least one denied boarding.
- Number of denied passengers.
- Proportion of visits with denied boarding.
- Mean and upper quantiles of denied passengers per affected visit.
- Locations and time slots with the greatest denied-boarding risk.
- Total denied boardings per simulated service day.

Compare IA and AG directly. Compare with empirical records only if the corresponding observed quantity is recorded reliably.

### D3. Queue accumulation

Where the CSVs preserve queue counts or passenger arrival timestamps, calculate:

- Queue size by stop and time.
- Maximum queue size per replica.
- Queue duration and persistence across successive buses.
- Number of consecutive buses unable to serve all waiting passengers.
- Passenger waiting-time tail measures.

Do not infer a queue trajectory from boarding counts alone if the required state transitions cannot be reconstructed.

### D4. Tail-risk measures

For occupancy, waiting time and denied boardings, consider:

- 90th, 95th and 99th percentiles.
- Conditional mean above a selected percentile (conditional value at risk, where appropriate).
- Probability of exceeding a predefined operational limit.
- Worst observed stop/time-slot combinations, accompanied by uncertainty estimates.

Extreme quantiles should be reported only where the number of independent replica-level observations is adequate. Do not treat every bus-stop record as an independent observation when constructing uncertainty intervals.

### D5. Decision agreement

For each stop/time slot, classify whether each model flags an operational issue under the same threshold rule. Compare:

- Agreement in issue/no-issue classification.
- False-negative and false-positive classifications relative to the empirical reference, where suitable.
- Whether model choice changes the ranking of the most critical stops or periods.

This identifies whether computational simplification changes decisions, not merely numerical averages.

**Output:** threshold-exceedance curves, denied-boarding summaries and a ranking of operationally critical stops and time slots.

---

## 8. Analysis E — Computational efficiency

### E1. Runtime comparison

For each implementation, report:

- Total wall-clock runtime for all replicas.
- Runtime per replica.
- Median, interquartile range and upper quantiles of runtime if individual replica times are available.
- Throughput in completed replicas per unit time.
- Speedup and percentage runtime reduction.

Define the speedup as:

\[
S=\frac{T_{\mathrm{IA}}}{T_{\mathrm{AG}}},
\]

and the runtime reduction as:

\[
R=1-\frac{T_{\mathrm{AG}}}{T_{\mathrm{IA}}}.
\]

Run both implementations under equivalent hardware, parallelism, logging, output and execution conditions. State whether the measurements include startup and file-writing costs.

### E2. Memory and output costs

If recorded, compare:

- Peak resident memory.
- CPU time and utilisation.
- Output size per replica and for the complete experiment.
- Number of generated passenger entities.
- Number of agent messages or protocol exchanges.
- Number of state updates or stop-visit operations.

If memory or CPU metrics were not collected, report them as unmeasured rather than estimating them from wall-clock time.

### E3. Scaling with passenger population

If the existing experiments include different demand levels, route sizes, passenger counts or replica counts, estimate how runtime changes with each. Otherwise, treat a controlled scaling experiment as an additional experiment rather than inferring scaling from one operating point.

Possible analyses include runtime against mean passenger population, maximum onboard population, total passenger creations, and total protocol messages.

### E4. Efficiency–fidelity trade-off

Plot computational cost against empirical distributional error for IA and AG, both globally and by important strata.

The key question is whether the additional cost of IA yields a practically meaningful improvement in fidelity or operational decisions.

**Output:** runtime and resource table, speedup estimate, and efficiency–fidelity comparison.

---

## 9. Analysis F — Sensitivity and robustness

Use the existing CSVs to investigate observed heterogeneity first. Run additional simulations only where the existing data cannot identify the question.

### F1. Time-slot and demand sensitivity

Assess whether IA–AG differences increase during peak demand or at stops with high passenger turnover. Use demand and occupancy strata defined independently of the observed comparison outcomes wherever possible.

### F2. Stop and direction sensitivity

Identify whether the relative performance of the two implementations differs between directions, terminal-adjacent stops, high-demand boarding stops and high-demand alighting stops.

Terminal stops should be treated consistently with the paper's stated data-quality limitations.

### F3. Distributional sensitivity

Re-evaluate the main conclusions under reasonable alternative distributional distances or acceptance thresholds. The purpose is to determine whether conclusions depend on one arbitrary cutoff.

### F4. Input-calibration sensitivity

If additional simulations can be run, perturb uncertain input-distribution parameters within empirically justified ranges and examine the stability of:

- Occupancy exceedance probabilities.
- Denied boarding.
- Waiting-time quantiles.
- IA–AG differences.
- Runtime.

Do not interpret variation across the 1,000 replicas as uncertainty in the fitted input parameters unless those parameters were themselves re-estimated or sampled across runs.

### F5. External validity

Because the case study concerns a single route and a restricted operating regime, distinguish demonstrated findings from hypotheses about other routes, holidays, unusual demand, changed frequencies or changed capacities.

**Output:** stratified robustness tables and, where new experiments are conducted, sensitivity plots.

---

## 10. Statistical inference and uncertainty

### 10.1. Independent units

The principal independent unit for simulation uncertainty is the replica, not the individual passenger or every bus-stop record. Records within a replica share schedules, demand realisations and evolving system state.

For empirical uncertainty, the independent unit is generally the observed operating day, if date-level data are available. Repeated trips and stops from the same day are not independent empirical days.

### 10.2. Confidence intervals

Prefer replica-level confidence intervals or bootstrap procedures that resample complete replicas. For empirical validation, use day-level resampling when enough independent days exist, preserving the within-day structure.

Where both empirical-day variability and simulation variability are relevant, consider a two-stage bootstrap that resamples empirical days and simulated replicas separately.

### 10.3. Multiple comparisons

Stop-by-time-slot analysis may involve many comparisons. Report effect sizes and uncertainty, and control the false discovery rate if conducting large families of formal significance tests. Do not use statistical significance alone to define operational importance.

### 10.4. Equivalence margins

Define practical margins before the final analysis for key KPIs and distributional errors. Margins should be justified by measurement resolution, operational requirements or domain expertise.

Use confidence intervals to assess whether differences lie within those margins. A nonsignificant difference is not evidence of equivalence.

### 10.5. Statistical versus operational significance

For every principal result, discuss both:

- Whether the discrepancy is statistically distinguishable from zero.
- Whether its magnitude could change a capacity, scheduling or passenger-service conclusion.

---

## 11. Recommended figures and tables

### Figures

1. **Figure 1 — Occupancy distributions:** empirical, IA and AG distributions for representative peak and off-peak strata.
2. **Figure 2 — Distributional validation map:** stop/time-slot error or overlap for each model.
3. **Figure 3 — Occupancy exceedance curves:** probability of exceeding a range of occupancy thresholds.
4. **Figure 4 — Waiting-time distributions:** median and upper-tail comparisons between IA and AG.
5. **Figure 5 — IA–AG difference by stop and time slot:** heatmap of a prespecified metric.
6. **Figure 6 — Efficiency–fidelity trade-off:** runtime against empirical error.
7. **Figure 7 — Replica uncertainty and convergence:** confidence intervals for selected KPIs as the number of replicas increases.

Only include a figure if its data support a clear conclusion. Representative plots should not replace summary statistics across all relevant strata.

### Tables

1. **Table 1 — Dataset coverage and quality:** records, replicas, trips, stops, missingness and invariant violations.
2. **Table 2 — Global KPI comparison:** IA, AG, difference, confidence interval and equivalence assessment.
3. **Table 3 — Empirical validation:** distributional errors for occupancy, boardings, alightings and travel times.
4. **Table 4 — Operational risk:** threshold exceedance, full-bus events and denied boarding.
5. **Table 5 — Computational performance:** runtime, speedup, memory and output size where available.
6. **Table 6 — Robustness:** results stratified by direction, demand level and time slot.

---

## 12. Minimum analysis set for the paper

If space or time is limited, prioritise the following analyses.

1. **Integrity checks:** passenger-flow conservation, capacity consistency, complete service coverage and comparable output definitions.
2. **Primary controlled comparison:** replica-level global KPIs and occupancy-distribution differences between IA and AG.
3. **Empirical validation:** occupancy distributions by stop and time slot, plus boarding, alighting and travel-time validation.
4. **Operational relevance:** occupancy-threshold exceedance and denied boarding, including upper-tail behaviour.
5. **Efficiency:** runtime comparison under matched execution conditions, accompanied by the measured fidelity differences.
6. **Uncertainty:** confidence intervals at the replica level and, where possible, empirical-day-level uncertainty.
7. **Robustness:** identify whether the conclusion holds during peak periods and at the most critical stops.

These analyses provide a coherent answer to the central question: whether individual passenger agents produce sufficient gains in empirical fidelity or operational decision quality to justify their computational cost.

---

## 13. Interpretation framework

The final conclusion should distinguish among the following possible outcomes.

### Outcome A — Similar fidelity, substantially lower aggregate-model cost

If IA and AG are practically equivalent on prespecified fidelity and operational measures, while AG is materially cheaper, the evidence supports aggregate passenger representation for the studied objectives and operating regime.

### Outcome B — Similar global means, different tails or critical stops

If average KPIs agree but occupancy exceedance, denied boarding or peak-stop distributions differ, the models are not operationally interchangeable for capacity analysis. The paper should identify the affected conditions and their consequences.

### Outcome C — Individual agents improve empirical fidelity

If IA consistently reduces empirical distributional error by a practically meaningful amount, the paper should identify which variables and conditions benefit from passenger-level representation, and whether the gain justifies the extra runtime.

### Outcome D — Both models fit poorly

If both implementations disagree materially with empirical observations, the main finding is a limitation of the current model structure, calibration or data-generating assumptions. Similarity between IA and AG would not establish that either is reliable.

### Outcome E — Results depend on the operating regime

If the preferred representation changes with demand, stop, direction or time slot, recommend a conditional modelling strategy and state the boundaries of each conclusion.

---

## 14. Reporting principles

- Report effect sizes and uncertainty, not only p-values.
- Separate implementation agreement from empirical validation.
- Do not call a quantity empirically validated unless a suitable independent reference exists.
- Do not treat 1,000 simulated replicas as 1,000 independent real operating days.
- Do not infer the benefit of autonomous passenger decision-making from a model in which alighting is externally imposed.
- Distinguish the validation of the calibrated operating regime from predictions under changed service frequency, capacity or demand.
- State all exclusions, thresholds, distributional metrics and equivalence margins explicitly.
- Preserve failed runs and diagnostic evidence in the analysis log; do not exclude inconvenient outcomes without a documented rule.
- Make the analysis reproducible through scripts, configuration files, software versions and explicit random-seed handling.
- Prioritise conclusions that change the modelling decision or an operational decision over large collections of descriptive KPIs.
