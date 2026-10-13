"""
Occupancy strata shared by analyses C, D and F.

Stratum = direction x stop x trip-departure slot (non-terminal visits only), the level of
known_data. Per model the per-replica occupancy histogram of every stratum is built once:

    counts  float32 (n_replicas, n_strata, CAPACITY + 1)

so that replica bootstraps of any distribution-based statistic reduce to a matrix product
(weights @ counts) followed by vectorised arithmetic on the pooled histogram.

W1 against N(mu, sigma) is computed from the CDFs, W1 = integral |F(x) - G(x)| dx, with F the
step CDF of the (integer) simulated occupancy and G the normal CDF, on a fixed grid. This is
the exact 1-D identity and is vectorisable for bootstrap resamples; it differs from the
sample-quantile version in metrics.w1_vs_normal only by the interpolation convention.
"""

import os
import pickle

import numpy as np
import pandas as pd
from scipy.stats import norm

from config import CACHE, CAPACITY, PEAK_SLOTS, TIMESLOTS
from kpis import prepared
from load import load_known

GRID = np.arange(-60.0, 180.0, 0.1) + 0.05            # mid-points, step 0.1 pax
GRID_IDX = np.clip(np.floor(GRID).astype(int), -1, CAPACITY)   # index of the step CDF value at x
GSTEP = 0.1


def strata_index(p) -> pd.DataFrame:
    v = p["visits"]
    rows = []
    for d in ("toA", "toB"):
        for s in p["order"][d][:-1]:
            for t in TIMESLOTS:
                rows.append((d, s, t))
    return pd.DataFrame(rows, columns=["dir", "stop", "dep_slot"])


def occ_hist(model: str, n_rep: int = 1000) -> dict:
    cache = os.path.join(CACHE, f"{model}_occhist.pkl")
    if os.path.exists(cache):
        with open(cache, "rb") as f:
            return pickle.load(f)
    p = prepared(model)
    idx = strata_index(p)
    idx["sid"] = np.arange(len(idx))
    v = p["visits"]
    v = v[~v["is_last"]].merge(idx, on=["dir", "stop", "dep_slot"], how="inner")
    S, K = len(idx), CAPACITY + 1
    flat = (v["replica"].to_numpy() * S + v["sid"].to_numpy()) * K + v["occ"].to_numpy()
    counts = np.bincount(flat, minlength=n_rep * S * K).reshape(n_rep, S, K).astype(np.float32)
    out = {"counts": counts, "index": idx.drop(columns="sid")}
    with open(cache, "wb") as f:
        pickle.dump(out, f, protocol=pickle.HIGHEST_PROTOCOL)
    return out


def known_aligned(index: pd.DataFrame) -> pd.DataFrame:
    k = load_known()["occ"].rename(columns={"slot": "dep_slot"})
    m = index.merge(k, on=["dir", "stop", "dep_slot"], how="left")
    assert m["mean"].notna().all() and (m["std"] > 0).all()
    m["peak"] = m["dep_slot"].isin(PEAK_SLOTS)
    t = m["mean"].quantile([1 / 3, 2 / 3]).to_numpy()
    m["demand"] = pd.cut(m["mean"], [-np.inf, t[0], t[1], np.inf], labels=["low", "medium", "high"])
    return m


def normal_cdf_grid(mu, sd) -> np.ndarray:
    """(n_strata, len(GRID)) normal CDF."""
    return norm.cdf((GRID[None, :] - mu[:, None]) / sd[:, None]).astype(np.float32)


def step_cdf_grid(pmf: np.ndarray) -> np.ndarray:
    """pmf (..., K) -> step CDF at GRID points (..., len(GRID)). F(x) = P(O <= x)."""
    cdf = np.cumsum(pmf, axis=-1)
    cdf = np.concatenate([np.zeros(cdf.shape[:-1] + (1,), cdf.dtype), cdf], axis=-1)   # index 0 -> x < 0
    return cdf[..., GRID_IDX + 1]


def w1_normal_from_counts(counts: np.ndarray, G: np.ndarray, chunk: int = 8) -> np.ndarray:
    """counts (B, S, K) pooled histograms -> (B, S) W1 against the normal CDFs G (S, grid)."""
    out = np.empty(counts.shape[:2], dtype=np.float64)
    for i in range(0, counts.shape[0], chunk):
        c = counts[i:i + chunk]
        n = c.sum(-1, keepdims=True)
        pmf = c / np.maximum(n, 1)
        F = step_cdf_grid(pmf)
        out[i:i + chunk] = np.abs(F - G[None]).sum(-1) * GSTEP
    return out


def w1_between_counts(ca: np.ndarray, cb: np.ndarray) -> np.ndarray:
    """W1 between two pooled histograms on the integer support (unit spacing). (..., K) -> (...,)"""
    pa = ca / np.maximum(ca.sum(-1, keepdims=True), 1)
    pb = cb / np.maximum(cb.sum(-1, keepdims=True), 1)
    return np.abs(np.cumsum(pa - pb, axis=-1))[..., :-1].sum(-1)


def pmf_stats(pmf: np.ndarray) -> dict:
    """mean, sd, median, p90 and P(O >= c) of pooled pmfs (S, K)."""
    k = np.arange(pmf.shape[-1])
    mean = pmf @ k
    sd = np.sqrt(np.maximum(pmf @ (k ** 2) - mean ** 2, 0))
    cdf = np.cumsum(pmf, -1)
    med = (cdf < 0.5).sum(-1)
    p90 = (cdf < 0.9).sum(-1)
    return {"mean": mean, "sd": sd, "median": med, "p90": p90, "cdf": cdf}
