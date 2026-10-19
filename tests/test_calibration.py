"""Calibration fits never report a value Newton-Raphson did not reach."""

from __future__ import annotations

import math

import numpy as np
import pytest

from mavecal.calibration import NotConverged, calibration_stats, crossfit_probabilities, fit_logistic


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
