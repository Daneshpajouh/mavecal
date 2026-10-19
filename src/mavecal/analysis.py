"""Evaluate one matched control set: AUC, thresholds, OddsPath, calibration."""

from __future__ import annotations

import math
import re
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
from numpy.typing import NDArray

from . import calibration as cal
from .oddspath import Readouts, evidence_strength, oddspath_abnormal, oddspath_normal
from .stats import (
    auc,
    crossfit_youden,
    mann_whitney_greater,
    percentile_interval,
    stratified_bootstrap,
    youden_threshold,
)

ABNORMAL, NORMAL, INDETERMINATE = 1, 0, -1
RULE = re.compile(r"^(<=|>=|<|>)(-?\d+(?:\.\d+)?)$")
RANGE = re.compile(r"^(-?\d+(?:\.\d+)?)\.\.(-?\d+(?:\.\d+)?)$")


@dataclass(frozen=True)
class Settings:
    direction: str
    n_boot: int
    seed: int
    n_folds: int
    min_per_class_threshold: int
    small_class: int
    n_primary: int


def parse_rule(text: str) -> Callable[[NDArray[np.float64]], NDArray[np.bool_]]:
    """Turn '<=-1.328', '>0' or '-1.11..0.89' into a vectorised predicate on raw scores."""
    t = str(text).strip()
    m = RANGE.match(t)
    if m:
        lo, hi = float(m.group(1)), float(m.group(2))
        return lambda s: (s >= lo) & (s <= hi)
    m = RULE.match(t)
    if not m:
        raise ValueError(f"cannot parse threshold rule {text!r}")
    op, v = m.group(1), float(m.group(2))
    ops: dict[str, Callable[[NDArray[np.float64]], NDArray[np.bool_]]] = {
        "<=": lambda s: s <= v,
        ">=": lambda s: s >= v,
        "<": lambda s: s < v,
        ">": lambda s: s > v,
    }
    return ops[op]


def readouts_from_codes(codes: NDArray[np.int64], is_path: NDArray[np.bool_]) -> Readouts:
    return Readouts(
        p_abnormal=int(np.sum(is_path & (codes == ABNORMAL))),
        b_abnormal=int(np.sum(~is_path & (codes == ABNORMAL))),
        p_normal=int(np.sum(is_path & (codes == NORMAL))),
        b_normal=int(np.sum(~is_path & (codes == NORMAL))),
        p_indeterminate=int(np.sum(is_path & (codes == INDETERMINATE))),
        b_indeterminate=int(np.sum(~is_path & (codes == INDETERMINATE))),
    )


def _odds_block(prefix: str, codes: NDArray[np.int64], y: NDArray[Any], st: Settings) -> dict[str, Any]:
    is_path = y == 1
    r = readouts_from_codes(codes, is_path)
    adj = r.with_misclassified_control()
    out: dict[str, Any] = {
        f"{prefix}_p_abnormal": r.p_abnormal,
        f"{prefix}_b_abnormal": r.b_abnormal,
        f"{prefix}_p_normal": r.p_normal,
        f"{prefix}_b_normal": r.b_normal,
        f"{prefix}_p_indeterminate": r.p_indeterminate,
        f"{prefix}_b_indeterminate": r.b_indeterminate,
        f"{prefix}_oddspath_abnormal_raw": oddspath_abnormal(r),
        f"{prefix}_oddspath_normal_raw": oddspath_normal(r),
        f"{prefix}_oddspath_abnormal": oddspath_abnormal(adj),
        f"{prefix}_oddspath_normal": oddspath_normal(adj),
    }
    pos, neg = codes[is_path], codes[~is_path]

    def stat_abn(p: NDArray[np.generic], n: NDArray[np.generic]) -> float:
        rr = readouts_from_codes(np.r_[p, n].astype(np.int64), np.r_[np.ones(p.size, bool), np.zeros(n.size, bool)])
        return oddspath_abnormal(rr.with_misclassified_control())

    def stat_norm(p: NDArray[np.generic], n: NDArray[np.generic]) -> float:
        rr = readouts_from_codes(np.r_[p, n].astype(np.int64), np.r_[np.ones(p.size, bool), np.zeros(n.size, bool)])
        return oddspath_normal(rr.with_misclassified_control())

    abn_lo, abn_hi = percentile_interval(stratified_bootstrap(pos, neg, stat_abn, st.n_boot, st.seed))
    nor_lo, nor_hi = percentile_interval(stratified_bootstrap(pos, neg, stat_norm, st.n_boot, st.seed))
    out.update(
        {
            f"{prefix}_oddspath_abnormal_lo": abn_lo,
            f"{prefix}_oddspath_abnormal_hi": abn_hi,
            f"{prefix}_oddspath_normal_lo": nor_lo,
            f"{prefix}_oddspath_normal_hi": nor_hi,
            f"{prefix}_strength_abnormal_point": evidence_strength(out[f"{prefix}_oddspath_abnormal"]),
            f"{prefix}_strength_normal_point": evidence_strength(out[f"{prefix}_oddspath_normal"]),
            f"{prefix}_strength_abnormal": evidence_strength(abn_lo),
            f"{prefix}_strength_normal": evidence_strength(nor_hi),
        }
    )
    return out


def evaluate(
    matched: pd.DataFrame, st: Settings, t2_abnormal: str | None, t2_normal: str | None
) -> tuple[dict[str, Any], pd.DataFrame, list[dict[str, float]]]:
    """Return the summary row, per-variant readouts and reliability bins for one control set."""
    raw = matched["score"].to_numpy(dtype=float)
    sign = 1.0 if st.direction == "higher_is_abnormal" else -1.0
    oriented = sign * raw
    y = (matched["label"] == "P").to_numpy(dtype=np.int64)
    n_p, n_b = int(y.sum()), int(y.size - y.sum())
    row: dict[str, Any] = {"n_pathogenic": n_p, "n_benign": n_b}
    row["small"] = n_p < st.small_class or n_b < st.small_class
    per_variant = matched.copy()
    bins: list[dict[str, float]] = []
    if n_p == 0 or n_b == 0:
        row["status"] = "one class missing"
        return row, per_variant, bins
    row["status"] = "ok"
    row["auc"] = auc(oriented[y == 1], oriented[y == 0])
    reps = stratified_bootstrap(oriented[y == 1], oriented[y == 0], auc, st.n_boot, st.seed)
    row["auc_lo"], row["auc_hi"] = percentile_interval(reps, 0.95)
    row["auc_lo_simultaneous"], row["auc_hi_simultaneous"] = percentile_interval(reps, 1 - 0.05 / st.n_primary)
    row["p_one_sided"] = mann_whitney_greater(oriented[y == 1], oriented[y == 0])

    if n_p >= st.min_per_class_threshold and n_b >= st.min_per_class_threshold:
        abnormal, thresholds = crossfit_youden(oriented, y, st.n_folds, st.seed)
        codes = np.where(abnormal, ABNORMAL, NORMAL).astype(np.int64)
        per_variant["t1_readout"] = np.where(abnormal, "abnormal", "normal")
        row["t1_fold_thresholds"] = ";".join(f"{sign * t:.4g}" for t in thresholds)
        row["t1_threshold_all_data"] = sign * youden_threshold(oriented, y)
        row.update(_odds_block("t1", codes, y, st))
        prob = cal.crossfit_probabilities(oriented, y, st.n_folds, st.seed)
        per_variant["p_label_pathogenic_oof"] = prob
        row.update(cal.calibration_stats(prob, y))
        bins = cal.reliability_bins(prob, y)
    else:
        row["t1_status"] = "too few controls for cross-fitting"

    if t2_abnormal and t2_normal:
        is_abn = parse_rule(t2_abnormal)(raw)
        is_norm = parse_rule(t2_normal)(raw) & ~is_abn
        codes2 = np.where(is_abn, ABNORMAL, np.where(is_norm, NORMAL, INDETERMINATE)).astype(np.int64)
        per_variant["t2_readout"] = pd.Series(codes2).map({1: "abnormal", 0: "normal", -1: "indeterminate"}).to_numpy()
        row.update(_odds_block("t2", codes2, y, st))
    if row["small"]:
        # Plan item 7: show the numbers, quote no evidence strength.
        for key in [k for k in row if "_strength_" in k]:
            row[key] = "not quoted (small)"
    for key, value in list(row.items()):
        if isinstance(value, float) and math.isinf(value):
            row[key] = "inf"
    return row, per_variant, bins
