"""Known-answer tests for OddsPath and the Brnich et al. (2019) Table 3 mapping."""

from __future__ import annotations

import math

import pytest

from mavecal.oddspath import (
    Readouts,
    evidence_strength,
    oddspath,
    oddspath_abnormal,
    oddspath_normal,
    readout_strength,
)


def test_formula_balanced_controls() -> None:
    r = Readouts(p_abnormal=9, b_abnormal=1, p_normal=1, b_normal=9)
    assert oddspath_abnormal(r) == pytest.approx(9.0)
    assert oddspath_normal(r) == pytest.approx(1 / 9)


def test_formula_unbalanced_prior() -> None:
    # P1 = 30/40, P2 = 27/28: OddsPath = (27/28 * 0.25) / (1/28 * 0.75) = 9.
    assert oddspath(27, 1, 30, 10) == pytest.approx(9.0)


def test_zero_and_empty_cells() -> None:
    assert oddspath(5, 0, 5, 5) == math.inf
    assert oddspath(0, 5, 5, 5) == 0.0
    assert math.isnan(oddspath(0, 0, 5, 5))
    assert math.isnan(oddspath(1, 1, 0, 5))


def test_misclassified_control_device() -> None:
    adj = Readouts(10, 0, 0, 10).with_misclassified_control()
    assert adj == Readouts(10, 1, 1, 10)
    assert oddspath_abnormal(adj) == pytest.approx(10.0)
    assert oddspath_normal(adj) == pytest.approx(0.1)


def test_brnich_worked_example_reaches_moderate() -> None:
    # Brnich et al. (2019): 5 pathogenic and 6 benign controls, one benign control with an
    # indeterminate readout, the rest concordant, supports PS3_moderate.
    r = Readouts(p_abnormal=5, b_abnormal=0, p_normal=0, b_normal=5, b_indeterminate=1)
    odds = oddspath_abnormal(r.with_misclassified_control())
    assert odds == pytest.approx(35 / 6)
    assert evidence_strength(odds) == "PS3_moderate"


@pytest.mark.parametrize(
    ("odds", "level"),
    [
        (350.01, "PS3_very_strong"),
        (350.0, "PS3"),
        (18.71, "PS3"),
        (18.7, "PS3_moderate"),
        (4.31, "PS3_moderate"),
        (4.3, "PS3_supporting"),
        (2.11, "PS3_supporting"),
        (2.1, "indeterminate"),
        (1.0, "indeterminate"),
        (0.48, "indeterminate"),
        (0.479, "BS3_supporting"),
        (0.23, "BS3_supporting"),
        (0.229, "BS3_moderate"),
        (0.053, "BS3_moderate"),
        (0.0529, "BS3"),
        (math.inf, "PS3_very_strong"),
        (math.nan, "not_estimated"),
    ],
)
def test_evidence_strength_boundaries(odds: float, level: str) -> None:
    assert evidence_strength(odds) == level


@pytest.mark.parametrize(
    ("odds", "readout", "level"),
    [
        (0.0, "abnormal", "indeterminate"),
        (0.3, "abnormal", "indeterminate"),
        (5.0, "abnormal", "PS3_moderate"),
        (math.inf, "normal", "indeterminate"),
        (3.0, "normal", "indeterminate"),
        (0.1, "normal", "BS3_moderate"),
        (math.nan, "normal", "not_estimated"),
    ],
)
def test_readout_strength_keeps_the_readout_direction(odds: float, readout: str, level: str) -> None:
    assert readout_strength(odds, readout) == level
