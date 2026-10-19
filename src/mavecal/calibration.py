"""Cross-fitted logistic calibration of assay scores against labels."""

from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike, NDArray

from .stats import stratified_folds

FloatArray = NDArray[np.float64]


class NotConverged(ArithmeticError):
    """Newton-Raphson did not reach a finite optimum within n_iter steps."""


def fit_logistic(x: ArrayLike, y: ArrayLike, ridge: float = 1e-3, n_iter: int = 100) -> tuple[float, float]:
    """Newton-Raphson for P(y=1) = 1 / (1 + exp(-(a + b x))).

    The small ridge on b keeps the slope finite when the classes separate perfectly,
    which happens in the smaller score sets. Without a ridge, separated data have no
    finite optimum: the slope grows each step. Raises NotConverged when the steps
    have not settled after n_iter iterations or the estimate is not finite, so a
    caller never reads the last iterate as a fitted value.
    """
    xv = np.asarray(x, dtype=float)
    yv = np.asarray(y, dtype=float)
    design = np.column_stack([np.ones_like(xv), xv])
    beta = np.zeros(2)
    penalty = np.diag([0.0, ridge])
    converged = False
    with np.errstate(over="ignore", invalid="ignore"):
        for _ in range(n_iter):
            p = 1.0 / (1.0 + np.exp(-(design @ beta)))
            grad = design.T @ (yv - p) - penalty @ beta
            hess = design.T @ (design * (p * (1 - p))[:, None]) + penalty
            step = np.linalg.solve(hess, grad)
            beta = beta + step
            if not np.all(np.isfinite(beta)):
                break
            if float(np.max(np.abs(step))) < 1e-10:
                converged = True
                break
    if not converged:
        raise NotConverged(f"no finite optimum after {n_iter} Newton steps")
    return float(beta[0]), float(beta[1])


def crossfit_probabilities(scores: ArrayLike, labels: ArrayLike, n_folds: int, seed: int) -> FloatArray:
    """Out-of-fold P(pathogenic label | score) using the same folds as the thresholds."""
    s = np.asarray(scores, dtype=float)
    y = np.asarray(labels, dtype=int)
    folds = stratified_folds(y, n_folds, seed)
    prob = np.empty(s.size)
    for k in range(n_folds):
        train = folds != k
        mu = s[train].mean()
        sd = s[train].std() or 1.0
        a, b = fit_logistic((s[train] - mu) / sd, y[train])
        prob[~train] = 1.0 / (1.0 + np.exp(-(a + b * (s[~train] - mu) / sd)))
    return prob


def calibration_stats(prob: ArrayLike, labels: ArrayLike) -> dict[str, float]:
    """Brier score, and intercept and slope of a logistic recalibration on logit(p)."""
    p = np.clip(np.asarray(prob, dtype=float), 1e-6, 1 - 1e-6)
    y = np.asarray(labels, dtype=float)
    brier = float(np.mean((p - y) ** 2))
    try:
        a, b = fit_logistic(np.log(p / (1 - p)), y, ridge=0.0)
    except (np.linalg.LinAlgError, NotConverged):
        # Perfectly separated out-of-fold probabilities have no finite recalibration slope.
        return {"brier": brier, "cal_intercept": float("nan"), "cal_slope": float("nan")}
    return {"brier": brier, "cal_intercept": a, "cal_slope": b}


def reliability_bins(prob: ArrayLike, labels: ArrayLike, n_bins: int = 10) -> list[dict[str, float]]:
    """Quantile bins of predicted probability with observed fraction and Wilson 95% interval."""
    p = np.asarray(prob, dtype=float)
    y = np.asarray(labels, dtype=float)
    bins = max(2, min(n_bins, p.size // 10))
    edges = np.unique(np.quantile(p, np.linspace(0, 1, bins + 1)))
    which = np.clip(np.searchsorted(edges, p, side="right") - 1, 0, edges.size - 2)
    rows = []
    for k in range(edges.size - 1):
        m = which == k
        n = int(m.sum())
        if n == 0:
            continue
        obs = float(y[m].mean())
        lo, hi = wilson(obs, n)
        rows.append(
            {"bin": k, "n": n, "mean_predicted": float(p[m].mean()), "observed": obs, "obs_lo": lo, "obs_hi": hi}
        )
    return rows


def wilson(phat: float, n: int, z: float = 1.959963984540054) -> tuple[float, float]:
    denom = 1 + z * z / n
    centre = (phat + z * z / (2 * n)) / denom
    half = z * np.sqrt(phat * (1 - phat) / n + z * z / (4 * n * n)) / denom
    return float(centre - half), float(centre + half)
