"""
Statistical helpers shared by the analyses.

Distances
    w1_samples(x, y)       Wasserstein-1 between two samples (exact, scipy)
    w1_vs_normal(x, m, s)  Wasserstein-1 between a sample and N(m, s), via the
                           quantile functions on K = 1000 mid-point probabilities
    ks_vs_normal(x, m, s)  Kolmogorov-Smirnov statistic sample vs N(m, s)
    bc_hist(x, y, edges)   Bhattacharyya coefficient of two samples on a common
                           discretisation (integer support for counts/occupancy)
    bc_project(x, m, s)    Bhattacharyya coefficient sample vs N(m, s) exactly as
                           WEB_DEVEL/bash_scripts/data_extractor.py: normal-normal
                           if the sample passes the project's simplified normality
                           test, otherwise gaussian KDE vs normal (trapezoid rule)

Uncertainty
    Replicas are the independent unit. Bootstrap resamples complete replicas
    (multinomial weights over the 1000 replica ids) with a fixed seed.
"""

import math
import os

import numpy as np
import pandas as pd
from scipy.stats import gaussian_kde, norm, wasserstein_distance

from config import BOOTSTRAP, LOGS, SEED, margins_header

K_QUANT = 1000
U = (np.arange(K_QUANT) + 0.5) / K_QUANT
Z_U = norm.ppf(U)


# --------------------------------------------------------------------------
# Distances
# --------------------------------------------------------------------------

def w1_samples(x, y) -> float:
    x, y = np.asarray(x, float), np.asarray(y, float)
    if x.size == 0 or y.size == 0:
        return np.nan
    return float(wasserstein_distance(x, y))


def w1_vs_normal(x, m, s) -> float:
    x = np.asarray(x, float)
    if x.size == 0 or not np.isfinite(m) or not np.isfinite(s) or s <= 0:
        return np.nan
    return float(np.mean(np.abs(np.quantile(x, U) - (m + s * Z_U))))


def ks_vs_normal(x, m, s) -> float:
    x = np.sort(np.asarray(x, float))
    if x.size == 0 or not np.isfinite(m) or not np.isfinite(s) or s <= 0:
        return np.nan
    cdf = norm.cdf(x, m, s)
    n = x.size
    return float(max(np.max(np.arange(1, n + 1) / n - cdf), np.max(cdf - np.arange(n) / n)))


def bc_hist(x, y, edges) -> float:
    x, y = np.asarray(x, float), np.asarray(y, float)
    if x.size == 0 or y.size == 0:
        return np.nan
    p = np.histogram(x, edges)[0].astype(float)
    q = np.histogram(y, edges)[0].astype(float)
    if p.sum() == 0 or q.sum() == 0:
        return np.nan
    return float(np.sum(np.sqrt(p / p.sum() * q / q.sum())))


def _project_normal(x) -> bool:
    """data_extractor.is_normal_simplified (vectorised moments)."""
    n = x.size
    if n == 0:
        return False
    z_crit = 1.96 if n < 50 else (3.29 if n < 300 else None)
    d = x - x.mean()
    m2, m3, m4 = (d ** 2).mean(), (d ** 3).mean(), (d ** 4).mean()
    if m2 <= 1e-12:
        return False
    skew, kurt = m3 / m2 ** 1.5, m4 / m2 ** 2 - 3
    if z_crit is not None:
        return abs(skew / math.sqrt(6 / n)) <= z_crit and abs(kurt / math.sqrt(24 / n)) <= z_crit
    return abs(skew) <= 2 and abs(kurt) + 3 <= 7


def bc_normal(m1, s1, m2, s2) -> float:
    return math.sqrt(2 * s1 * s2 / (s1 ** 2 + s2 ** 2)) * math.exp(-((m1 - m2) ** 2) / (4 * (s1 ** 2 + s2 ** 2)))


def bc_project(x, m, s, kde_max: int = 20000, rng=None):
    """Returns (coefficient, method). KDE on at most kde_max points (random subsample)."""
    x = np.asarray(x, float)
    x = x[np.isfinite(x)]
    if x.size < 2 or not np.isfinite(m) or not np.isfinite(s) or s <= 1e-9:
        return np.nan, "not evaluable"
    m1, s1 = x.mean(), x.std(ddof=1)
    if s1 <= 1e-9:
        return np.nan, "no simulated variance"
    if _project_normal(x):
        return bc_normal(m1, s1, m, s), "normal"
    if x.size > kde_max:
        rng = rng or np.random.default_rng(SEED)
        x = rng.choice(x, kde_max, replace=False)
    kde = gaussian_kde(x)
    grid = np.linspace(min(x.min() - 1, m - 4 * s), max(x.max() + 1, m + 4 * s), 500)
    bc = float(np.trapezoid(np.sqrt(kde(grid) * norm.pdf(grid, m, s)), grid))
    return min(bc, 1.0), "kde"


# --------------------------------------------------------------------------
# Replica bootstrap
# --------------------------------------------------------------------------

def boot_weights(n_rep: int, b: int = BOOTSTRAP, seed: int = SEED) -> np.ndarray:
    """(b x n_rep) multinomial resampling counts of complete replicas."""
    rng = np.random.default_rng(seed)
    return rng.multinomial(n_rep, np.full(n_rep, 1 / n_rep), size=b).astype(float)


def ci_mean(x, w) -> tuple:
    """Mean of replica-level values and its 95 % percentile CI."""
    x = np.asarray(x, float)
    boot = (w @ x) / w.sum(axis=1)
    return float(x.mean()), float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5)), boot


def ci_ratio(sums: np.ndarray, counts: np.ndarray, w) -> tuple:
    """Ratio estimator sum/count over replicas (e.g. pooled stratum mean) with CI.

    sums, counts: (n_rep,) or (n_rep, k). Returns point, low, high (arrays if k)."""
    point = sums.sum(axis=0) / counts.sum(axis=0)
    with np.errstate(invalid="ignore", divide="ignore"):
        boot = (w @ sums) / (w @ counts)
    return point, np.nanpercentile(boot, 2.5, axis=0), np.nanpercentile(boot, 97.5, axis=0), boot


def diff_ci(boot_a, boot_b) -> tuple:
    d = np.asarray(boot_a) - np.asarray(boot_b)
    return float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5))


def equivalence(lo, hi, margin) -> str:
    if margin is None or not np.isfinite(lo) or not np.isfinite(hi):
        return "no margin"
    if -margin <= lo and hi <= margin:
        return "EQUIVALENT"
    if hi < -margin or lo > margin:
        return "NOT EQUIVALENT"
    return "INCONCLUSIVE"


def cohen_d(a, b) -> float:
    a, b = np.asarray(a, float), np.asarray(b, float)
    sp = math.sqrt(((a.size - 1) * a.var(ddof=1) + (b.size - 1) * b.var(ddof=1)) / (a.size + b.size - 2))
    return float((a.mean() - b.mean()) / sp) if sp > 0 else np.nan


def wquantile(sorted_vals, weights_sorted, q) -> np.ndarray:
    """Weighted quantiles of a sample already sorted by value."""
    cw = np.cumsum(weights_sorted)
    if cw[-1] <= 0:
        return np.full(np.size(q), np.nan)
    cw = (cw - 0.5 * weights_sorted) / cw[-1]
    return np.interp(q, cw, sorted_vals)


# --------------------------------------------------------------------------
# Logs
# --------------------------------------------------------------------------

class Log:
    """Plain-text log with the pre-specified definitions at the top."""

    def __init__(self, name: str, title: str):
        self.path = os.path.join(LOGS, name)
        self.lines = [title, "=" * len(title), "", margins_header(), ""]

    def h(self, text: str):
        self.lines += ["", text, "-" * len(text)]

    def p(self, text: str = ""):
        self.lines.append(text)

    def table(self, df: pd.DataFrame, floatfmt: str = "{:.3f}", index: bool = False):
        fmt = df.copy()
        for c in fmt.columns:
            if pd.api.types.is_float_dtype(fmt[c]):
                fmt[c] = fmt[c].map(lambda v: "" if pd.isna(v) else floatfmt.format(v))
        self.lines.append(fmt.to_string(index=index))

    def save(self):
        with open(self.path, "w") as f:
            f.write("\n".join(self.lines) + "\n")
        print("wrote", self.path)


def save_csv(df: pd.DataFrame, name: str):
    df.to_csv(os.path.join(LOGS, name), index=False)
