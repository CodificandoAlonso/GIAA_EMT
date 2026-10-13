"""
Configuration of the empirical-only analysis of a C-engine run (default SIMULATION_20261012_205659, or SIM_RUN=<folder>;
1000 replicas in one results.csv). Same pre-specified margins and acceptance rules as
AAA_TEST/sim_comparison (fixed before any comparison was computed); only the empirical part
(plan section 6, empirical sides of sections 7 and 9) is repeated. There is no IA/AG pair here.
"""

import os
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.abspath(os.path.join(HERE, ".."))
REPO = os.path.abspath(os.path.join(BASE, "..", ".."))
SIM = os.environ.get("SIM_RUN", "SIMULATION_20261012_205659")    # run to analyse (folder name under WEB_DEVEL/data/logs)
RUN_ID = SIM.replace("SIMULATION_", "")
LOGS = os.path.join(BASE, "logs", RUN_ID)
FIGS = os.path.join(BASE, "figures", RUN_ID)
CACHE = os.path.join(BASE, "cache", RUN_ID)
for _d in (LOGS, FIGS, CACHE):
    os.makedirs(_d, exist_ok=True)


def _find_sim_root() -> str:
    """The run may live in another worktree of the same repository: look in all of them."""
    cands = [os.path.join(REPO, "WEB_DEVEL", "data", "logs")]
    try:
        out = subprocess.run(["git", "-C", REPO, "worktree", "list", "--porcelain"], capture_output=True, text=True).stdout
        cands += [os.path.join(l.split(" ", 1)[1], "WEB_DEVEL", "data", "logs") for l in out.splitlines() if l.startswith("worktree ")]
    except OSError:
        pass
    for c in cands:
        if os.path.exists(os.path.join(c, SIM, "RESULTS", "results.csv")):
            return c
    raise FileNotFoundError(f"{SIM} not found in {cands}")


SIM_ROOT = _find_sim_root()
KNOWN = os.path.join(REPO, "WEB_DEVEL", "data", "known_data")
INPUTS = os.path.join(SIM_ROOT, SIM, "includes")
REF_LOGS = os.path.join(REPO, "AAA_TEST", "sim_comparison", "logs")   # GAMA IA/AG results, context only

CAPACITY = 80
TIMESLOTS = list(range(5, 24))
PEAK_SLOTS = (7, 8, 9, 17, 18, 19)
BC_ACCEPT = 0.97
W1_ACCEPT_PAX = 2.0
CROWDING = 60
THRESHOLDS = (40, 60, 70, 80)
ISSUE_PROB = 0.10
BOOTSTRAP = 1000
SEED = 20261013
MARGINS = {"occupancy_pax": 2.0, "travel_time_s": 10.0, "prob_pp": 2.0}
COLOR = {"C": "#2a78d6", "EMP": "#0b0b0b", "AG": "#eb6834", "IA": "#1baf7a"}
INK = {"primary": "#0b0b0b", "secondary": "#52514e", "grid": "#e4e3df"}
SEQ_BLUE = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]


def margins_header() -> str:
    return "\n".join([
        f"Run: {SIM} (C engine, model key c_engine). Reference: WEB_DEVEL/data/known_data, used as is.",
        "Pre-specified definitions (the same as AAA_TEST/sim_comparison, fixed before any comparison):",
        f"  empirical acceptance: Bhattacharyya coefficient >= {BC_ACCEPT} (project rule, data_extractor.py)",
        f"  empirical W1 tolerance: {W1_ACCEPT_PAX} passengers",
        f"  operational issue rule: P(O >= {CROWDING}) >= {ISSUE_PROB}; crowding threshold {CROWDING} of capacity {CAPACITY}",
        f"  peak slots: {PEAK_SLOTS}; bootstrap: resamples of complete replicas, seed {SEED}",
    ])


def setup_matplotlib():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({
        "figure.dpi": 110, "savefig.dpi": 150, "savefig.bbox": "tight", "font.size": 10, "axes.titlesize": 11,
        "axes.edgecolor": INK["secondary"], "axes.labelcolor": INK["primary"], "axes.spines.top": False,
        "axes.spines.right": False, "axes.grid": True, "grid.color": INK["grid"], "grid.linewidth": 0.8,
        "xtick.color": INK["secondary"], "ytick.color": INK["secondary"], "legend.frameon": False, "lines.linewidth": 2})
    return plt


def seq_cmap():
    from matplotlib.colors import LinearSegmentedColormap
    return LinearSegmentedColormap.from_list("seq_blue", SEQ_BLUE)
