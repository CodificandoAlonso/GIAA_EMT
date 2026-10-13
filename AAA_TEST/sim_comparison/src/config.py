"""
Shared configuration for the IA vs AG comparison (formal_analysis_plan.md).

    AG = aggregate model          SIMULATION_20261012_170524 (GAMA, without_agents)
    IA = individual-agent model   SIMULATION_20261012_172453 (GAMA, with_agents)

Empirical reference: WEB_DEVEL/data/known_data (normal parameters per stop and
time slot for occupancy, per segment and time slot for travel times), used as is.

The equivalence margins and acceptance rules below were fixed BEFORE any
IA/AG or simulation/empirical comparison was computed (plan, sections 3.2 and
10.4). They are written verbatim at the top of every log.
"""

import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
BASE = os.path.join(ROOT, "AAA_TEST", "sim_comparison")
LOGS = os.path.join(BASE, "logs")
FIGS = os.path.join(BASE, "figures")
CACHE = os.path.join(BASE, "cache")
for _d in (LOGS, FIGS, CACHE):
    os.makedirs(_d, exist_ok=True)

SIM_ROOT = os.path.join(ROOT, "WEB_DEVEL", "data", "logs")
SIMS = {
    "AG": "SIMULATION_20261012_170524",
    "IA": "SIMULATION_20261012_172453",
}
MODELS = ("IA", "AG")
KNOWN = os.path.join(ROOT, "WEB_DEVEL", "data", "known_data")

CAPACITY = 80                       # max_passengers in both GAMA models
TIMESLOTS = list(range(5, 24))
DIRS = ("toA", "toB")
HEADER = {"toA": 2646, "toB": 5727}  # first stop of each direction

# ---- Pre-specified definitions (fixed before looking at comparisons) ------

# Practical equivalence margins for IA - AG differences (absolute units)
MARGINS = {
    "occupancy_pax": 2.0,             # mean/median/quantiles of occupancy, and W1 (2.5 % of capacity)
    "travel_time_s": 10.0,            # mean segment travel time
    "trip_duration_s": 60.0,          # mean trip duration (~ 10 s x ~6 segments of drift)
    "flow_per_visit_pax": 0.5,        # boardings / alightings per bus-stop visit
    "wait_median_s": 30.0,            # median waiting time
    "wait_tail_s": 60.0,              # mean, p90, p95, p99 waiting time
    "prob_pp": 2.0,                   # P(O >= c), share of visits, in percentage points
    "denied_rel": 0.10,               # denied boardings per service day, relative (10 %)
    "headway_cv": 0.05,               # coefficient of variation of headways
}

# Empirical acceptance of a stratum (consistent with data_extractor.py)
BC_ACCEPT = 0.97                     # Bhattacharyya coefficient >= 0.97 ("fusionable")
W1_ACCEPT_PAX = MARGINS["occupancy_pax"]

# Operational thresholds
CROWDING = 60                        # 75 % of capacity
THRESHOLDS = (40, 60, 70, 80)
ISSUE_RULE = "P(O >= 60) >= 0.10"    # D5 classification of an operational issue
ISSUE_PROB = 0.10

# Peak periods (standard commuting peaks, fixed in advance)
PEAK_SLOTS = (7, 8, 9, 17, 18, 19)

BOOTSTRAP = 1000                     # replica-level bootstrap resamples
SEED = 20261013                      # seed of every bootstrap / random draw in this analysis

# ---- Plot style (validated categorical palette) ---------------------------
COLOR = {"IA": "#2a78d6", "AG": "#eb6834", "EMP": "#0b0b0b", "third": "#1baf7a"}
INK = {"primary": "#0b0b0b", "secondary": "#52514e", "grid": "#e4e3df"}
SEQ_BLUE = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]
DIVERGING = ["#c0392b", "#f0efec", "#2a78d6"]   # red = negative, blue = positive


def margins_header() -> str:
    lines = ["Pre-specified definitions (fixed before any comparison was computed):"]
    for k, v in MARGINS.items():
        lines.append(f"  margin {k:22s} = {v}")
    lines += [
        f"  empirical acceptance: Bhattacharyya coefficient >= {BC_ACCEPT} (project rule, data_extractor.py)",
        f"  empirical W1 tolerance: {W1_ACCEPT_PAX} passengers",
        f"  operational issue rule (D5): {ISSUE_RULE}",
        f"  crowding threshold: {CROWDING} passengers (75 % of capacity {CAPACITY})",
        f"  peak slots: {PEAK_SLOTS}",
        f"  bootstrap: {BOOTSTRAP} resamples of complete replicas, seed {SEED}",
        "  equivalence: 95 % CI of the IA-AG difference inside +-margin -> EQUIVALENT;",
        "               CI entirely outside -> NOT EQUIVALENT; otherwise INCONCLUSIVE",
    ]
    return "\n".join(lines)


def setup_matplotlib():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({
        "figure.dpi": 110, "savefig.dpi": 150, "savefig.bbox": "tight",
        "font.size": 10, "axes.titlesize": 11,
        "axes.edgecolor": INK["secondary"], "axes.labelcolor": INK["primary"],
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.grid": True, "grid.color": INK["grid"], "grid.linewidth": 0.8,
        "xtick.color": INK["secondary"], "ytick.color": INK["secondary"],
        "legend.frameon": False, "lines.linewidth": 2,
    })
    return plt


def seq_cmap():
    from matplotlib.colors import LinearSegmentedColormap
    return LinearSegmentedColormap.from_list("seq_blue", SEQ_BLUE)


def div_cmap():
    from matplotlib.colors import LinearSegmentedColormap
    return LinearSegmentedColormap.from_list("div", DIVERGING)
