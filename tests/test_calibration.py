"""Calibration fits never report a value Newton-Raphson did not reach."""

from __future__ import annotations

import math

import numpy as np
import pytest

from mavecal.calibration import (
    BIN_COLUMNS,
    NotConverged,
    calibration_stats,
    crossfit_probabilities,
    fit_logistic,
    reliability_bins,
)


def test_overlapping_classes_fit_a_finite_slope() -> None:
    rng = np.random.default_rng(1)
    x = np.concatenate([rng.normal(-1, 1, 200), rng.normal(1, 1, 200)])
    y = np.concatenate([np.zeros(200), np.ones(200)])
    a, b = fit_logistic(x, y, ridge=0.0)
    assert math.isfinite(a) and 1.0 < b < 3.0


def test_separated_classes_without_a_ridge_do_not_converge() -> None:
    x = np.array([-3.0, -2.0, -1.0, 1.0, 2.0, 3.0])
    y = np.array([0, 0, 0, 1, 1, 1])
    with pytest.raises((NotConverged, np.linalg.LinAlgError)):
        fit_logistic(x, y, ridge=0.0)


def test_separated_classes_with_the_default_ridge_converge() -> None:
    x = np.array([-3.0, -2.0, -1.0, 1.0, 2.0, 3.0])
    y = np.array([0, 0, 0, 1, 1, 1])
    a, b = fit_logistic(x, y)
    assert math.isfinite(a) and math.isfinite(b) and b > 0


def test_too_few_steps_is_not_converged() -> None:
    x = np.linspace(-2, 2, 50)
    y = (x + np.sin(7 * x) > 0).astype(float)
    with pytest.raises(NotConverged):
        fit_logistic(x, y, n_iter=1)


def test_separated_out_of_fold_probabilities_give_nan_calibration() -> None:
    prob = np.array([0.01, 0.02, 0.03, 0.97, 0.98, 0.99])
    y = np.array([0, 0, 0, 1, 1, 1])
    stats = calibration_stats(prob, y)
    assert math.isnan(stats["cal_slope"]) and math.isnan(stats["cal_intercept"])
    assert stats["brier"] == pytest.approx(np.mean((prob - y) ** 2))


def test_well_calibrated_probabilities_give_slope_near_one() -> None:
    rng = np.random.default_rng(2)
    prob = rng.uniform(0.05, 0.95, 4000)
    y = (rng.uniform(size=prob.size) < prob).astype(float)
    stats = calibration_stats(prob, y)
    assert stats["cal_slope"] == pytest.approx(1.0, abs=0.15)


def test_crossfit_runs_on_separated_scores() -> None:
    scores = np.concatenate([np.linspace(-3, -1, 20), np.linspace(1, 3, 20)])
    labels = np.concatenate([np.zeros(20, dtype=int), np.ones(20, dtype=int)])
    prob = crossfit_probabilities(scores, labels, n_folds=5, seed=7)
    assert np.all(np.isfinite(prob))
    assert prob[labels == 1].min() > prob[labels == 0].max()


def test_reliability_bins_count_and_wilson_interval() -> None:
    # 40 controls give 4 bins of 10; the top bin holds 7 pathogenic of 10.
    prob = np.linspace(0.01, 0.99, 40)
    y = np.r_[np.zeros(10), np.zeros(8), np.ones(2), np.zeros(5), np.ones(5), np.zeros(3), np.ones(7)]
    rows = reliability_bins(prob, y)
    assert [r["n"] for r in rows] == [10, 10, 10, 10]
    assert all(tuple(r) == BIN_COLUMNS for r in rows)
    assert [r["observed"] for r in rows] == [0.0, 0.2, 0.5, 0.7]
    # Wilson 95% interval for 5 of 10, worked by hand: 0.2366 to 0.7634.
    assert rows[2]["obs_lo"] == pytest.approx(0.2366, abs=1e-4)
    assert rows[2]["obs_hi"] == pytest.approx(0.7634, abs=1e-4)


def test_reliability_bins_all_probabilities_tied() -> None:
    rows = reliability_bins(np.full(30, 0.5), np.r_[np.ones(15), np.zeros(15)])
    assert len(rows) == 1
    assert rows[0]["n"] == 30 and rows[0]["observed"] == 0.5
    # Wilson 95% interval for 15 of 30: 0.3315 to 0.6685.
    assert rows[0]["obs_lo"] == pytest.approx(0.3315, abs=1e-4)
