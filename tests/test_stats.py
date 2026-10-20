"""Known-answer tests for AUC, bootstrap, Holm and the Youden threshold."""

from __future__ import annotations

import numpy as np
import pytest
from scipy.stats import norm
from sklearn.metrics import roc_auc_score

from mavecal.stats import (
    auc,
    crossfit_youden,
    holm,
    mann_whitney_greater,
    percentile_interval,
    stratified_bootstrap,
    stratified_folds,
    youden_threshold,
)


def test_auc_perfect_reverse_and_ties() -> None:
    assert auc([3, 4], [1, 2]) == 1.0
    assert auc([1, 2], [3, 4]) == 0.0
    assert auc([1], [1]) == 0.5
    assert auc([1, 3], [2]) == 0.5


def test_auc_matches_sklearn_with_ties() -> None:
    rng = np.random.default_rng(1)
    pos = np.round(rng.normal(1, 1, 300), 1)
    neg = np.round(rng.normal(0, 1, 200), 1)
    y = np.r_[np.ones(300), np.zeros(200)]
    assert auc(pos, neg) == pytest.approx(roc_auc_score(y, np.r_[pos, neg]), abs=1e-12)


def test_auc_needs_both_classes() -> None:
    with pytest.raises(ValueError):
        auc([], [1.0])


def test_one_sided_test_direction() -> None:
    assert mann_whitney_greater([5, 6, 7, 8], [1, 2, 3, 4]) < 0.05
    assert mann_whitney_greater([1, 2, 3, 4], [5, 6, 7, 8]) > 0.95


def test_bootstrap_keeps_class_sizes_and_is_seeded() -> None:
    sizes: list[tuple[int, int]] = []

    def stat(p: np.ndarray, n: np.ndarray) -> float:
        sizes.append((p.size, n.size))
        return float(p.mean() - n.mean())

    a = stratified_bootstrap(np.arange(7.0), np.arange(3.0), stat, 50, seed=3)
    b = stratified_bootstrap(np.arange(7.0), np.arange(3.0), stat, 50, seed=3)
    assert set(sizes) == {(7, 3)}
    assert np.array_equal(a, b)


def test_bootstrap_degenerate_data_gives_point_interval() -> None:
    reps = stratified_bootstrap(np.ones(10), np.zeros(10), auc, 200, seed=1)
    assert percentile_interval(reps) == (1.0, 1.0)


def test_bootstrap_interval_covers_binormal_auc() -> None:
    # Binormal model with unit variances: AUC = Phi(d / sqrt(2)).
    d = 1.0
    truth = float(norm.cdf(d / np.sqrt(2)))
    rng = np.random.default_rng(11)
    pos, neg = rng.normal(d, 1, 400), rng.normal(0, 1, 400)
    lo, hi = percentile_interval(stratified_bootstrap(pos, neg, auc, 1000, seed=5))
    assert lo < truth < hi
    assert hi - lo < 0.1


def test_percentile_interval_with_infinite_values() -> None:
    reps = np.array([1.0, 2.0, 3.0, np.inf, np.inf])
    lo, hi = percentile_interval(reps, 0.5)
    assert lo == 2.0 and hi == np.inf


def test_holm_known_answer() -> None:
    assert holm([0.01, 0.04, 0.03]) == pytest.approx([0.03, 0.06, 0.06])
    assert holm([0.5, 0.9]) == pytest.approx([1.0, 1.0])


def test_youden_threshold_known_answer() -> None:
    assert youden_threshold([1, 2, 3, 4], [0, 0, 1, 1]) == 2.5
    # Ties at the maximum keep the highest threshold.
    assert youden_threshold([1, 2, 3, 4, 5], [0, 1, 0, 1, 1]) == 3.5


def test_folds_are_stratified() -> None:
    y = np.r_[np.ones(10, int), np.zeros(15, int)]
    folds = stratified_folds(y, 5, seed=2)
    for k in range(5):
        assert y[folds == k].sum() == 2
        assert (1 - y[folds == k]).sum() == 3


def test_crossfit_uses_only_the_other_folds() -> None:
    # Overlapping classes, so the threshold depends on which rows it is fit on.
    rng = np.random.default_rng(7)
    scores = np.r_[rng.normal(1.0, 1.0, 30), rng.normal(-1.0, 1.0, 30)]
    labels = np.r_[np.ones(30, int), np.zeros(30, int)]
    abnormal, thresholds = crossfit_youden(scores, labels, 5, seed=3)
    folds = stratified_folds(labels, 5, 3)
    for k in range(5):
        train = folds != k
        expected = youden_threshold(scores[train], labels[train])
        assert thresholds[k] == expected
        assert np.array_equal(abnormal[~train], scores[~train] > expected)
    # A threshold fit on all rows calls some rows differently, so code that
    # skips cross-fitting fails this test.
    assert not np.array_equal(abnormal, scores > youden_threshold(scores, labels))


def test_crossfit_separable_data_is_called_correctly() -> None:
    scores = np.r_[np.linspace(5, 10, 20), np.linspace(-10, -5, 20)]
    labels = np.r_[np.ones(20, int), np.zeros(20, int)]
    abnormal, thresholds = crossfit_youden(scores, labels, 5, seed=1)
    assert thresholds.size == 5
    assert np.array_equal(abnormal, labels.astype(bool))
