"""AUC, stratified bootstrap, Holm adjustment and cross-fitted Youden thresholds."""

from __future__ import annotations

from collections.abc import Callable, Sequence

import numpy as np
from numpy.typing import ArrayLike, NDArray
from scipy.stats import mannwhitneyu, rankdata

FloatArray = NDArray[np.float64]
IntArray = NDArray[np.int64]


def auc(pos: ArrayLike, neg: ArrayLike) -> float:
    """Probability that a random positive outscores a random negative; ties count one half."""
    p = np.asarray(pos, dtype=float)
    n = np.asarray(neg, dtype=float)
    if p.size == 0 or n.size == 0:
        raise ValueError("AUC needs at least one positive and one negative")
    ranks = rankdata(np.concatenate([p, n]))
    u = ranks[: p.size].sum() - p.size * (p.size + 1) / 2.0
    return float(u / (p.size * n.size))


def mann_whitney_greater(pos: ArrayLike, neg: ArrayLike) -> float:
    """One-sided p-value for AUC > 0.5."""
    return float(mannwhitneyu(np.asarray(pos, float), np.asarray(neg, float), alternative="greater").pvalue)


def stratified_bootstrap(
    pos: ArrayLike,
    neg: ArrayLike,
    statistic: Callable[[NDArray[np.generic], NDArray[np.generic]], float],
    n_boot: int,
    seed: int,
) -> FloatArray:
    """Resample positives and negatives separately so class counts stay fixed."""
    p = np.asarray(pos)
    n = np.asarray(neg)
    rng = np.random.default_rng(seed)
    out = np.empty(n_boot, dtype=float)
    for i in range(n_boot):
        out[i] = statistic(p[rng.integers(0, p.size, p.size)], n[rng.integers(0, n.size, n.size)])
    return out


def percentile_interval(reps: FloatArray, level: float = 0.95) -> tuple[float, float]:
    finite = reps[np.isfinite(reps)] if np.any(np.isinf(reps)) else reps
    alpha = (1.0 - level) / 2.0
    if finite.size < reps.size:
        # Infinite odds sit at the top of the distribution; keep them in the ranking.
        return float(np.quantile(reps, alpha, method="lower")), float(np.quantile(reps, 1 - alpha, method="higher"))
    return float(np.quantile(reps, alpha)), float(np.quantile(reps, 1 - alpha))


def holm(pvalues: Sequence[float]) -> list[float]:
    """Holm step-down adjusted p-values, returned in the input order."""
    p = np.asarray(pvalues, dtype=float)
    m = p.size
    order = np.argsort(p)
    adjusted = np.empty(m)
    running = 0.0
    for rank, idx in enumerate(order):
        running = max(running, min(1.0, (m - rank) * p[idx]))
        adjusted[idx] = running
    return adjusted.tolist()


def youden_threshold(scores: ArrayLike, labels: ArrayLike) -> float:
    """Threshold maximising sensitivity + specificity - 1 for 'abnormal if score > t'.

    Candidates are midpoints between adjacent distinct scores. Among tied maxima the
    highest threshold is kept, which calls the fewest variants abnormal.
    """
    s = np.asarray(scores, dtype=float)
    y = np.asarray(labels, dtype=int)
    n_pos = int(y.sum())
    n_neg = int(y.size - n_pos)
    if n_pos == 0 or n_neg == 0:
        raise ValueError("Youden threshold needs both classes")
    order = np.argsort(-s, kind="mergesort")
    s_sorted = s[order]
    y_sorted = y[order]
    tp = np.cumsum(y_sorted)
    fp = np.cumsum(1 - y_sorted)
    last_of_value = np.r_[s_sorted[1:] != s_sorted[:-1], True]
    idx = np.flatnonzero(last_of_value)
    j = tp[idx] / n_pos - fp[idx] / n_neg
    best = int(idx[int(np.argmax(j))])
    upper = s_sorted[best]
    lower = s_sorted[best + 1] if best + 1 < s_sorted.size else upper - 1.0
    return float((upper + lower) / 2.0)


def stratified_folds(labels: ArrayLike, n_folds: int, seed: int) -> IntArray:
    """Assign each item a fold so that both classes are spread evenly."""
    y = np.asarray(labels, dtype=int)
    rng = np.random.default_rng(seed)
    folds = np.empty(y.size, dtype=np.int64)
    for cls in (0, 1):
        members = np.flatnonzero(y == cls)
        members = members[rng.permutation(members.size)]
        folds[members] = np.arange(members.size) % n_folds
    return folds


def crossfit_youden(
    scores: ArrayLike, labels: ArrayLike, n_folds: int, seed: int
) -> tuple[NDArray[np.bool_], FloatArray]:
    """Out-of-fold abnormal calls: each fold is called with a threshold fit on the others."""
    s = np.asarray(scores, dtype=float)
    y = np.asarray(labels, dtype=int)
    folds = stratified_folds(y, n_folds, seed)
    abnormal = np.zeros(s.size, dtype=bool)
    thresholds = np.empty(n_folds)
    for k in range(n_folds):
        train = folds != k
        thresholds[k] = youden_threshold(s[train], y[train])
        abnormal[~train] = s[~train] > thresholds[k]
    return abnormal, thresholds
