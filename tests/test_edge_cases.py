"""Inputs that break naive implementations: one class, all ties, empty and malformed data."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from mavecal import mavedb
from mavecal.analysis import Settings, evaluate, parse_rule
from mavecal.stats import auc, percentile_interval, stratified_bootstrap, youden_threshold

DATA = Path(__file__).parent / "data"
ST = Settings("higher_is_abnormal", 200, 1, 5, 5, 10, 6)


def test_one_class_only_is_reported_not_estimated() -> None:
    table = pd.DataFrame({"score": [1.0, 2.0, 3.0], "label": ["P", "P", "P"]})
    row, _, bins = evaluate(table, ST, ">2", "<1")
    assert row["status"] == "one class missing"
    assert "auc" not in row and bins == []


def test_empty_table() -> None:
    row, _, _ = evaluate(pd.DataFrame({"score": [], "label": []}), ST, None, None)
    assert row["n_pathogenic"] == 0 and row["status"] == "one class missing"


def test_empty_input_to_auc_raises() -> None:
    with pytest.raises(ValueError):
        auc([], [])


def test_all_ties() -> None:
    assert auc([2.0, 2.0, 2.0], [2.0, 2.0]) == 0.5
    reps = stratified_bootstrap(np.full(5, 2.0), np.full(5, 2.0), auc, 100, seed=1)
    assert percentile_interval(reps) == (0.5, 0.5)
    # With one distinct score every candidate threshold has J = 0; the threshold sits below it.
    assert youden_threshold([2.0, 2.0, 2.0, 2.0], [1, 0, 1, 0]) == 1.5


def test_too_few_controls_skips_cross_fitting() -> None:
    table = pd.DataFrame({"score": [3.0, 2.5, 2.0, 1.0, 0.5], "label": ["P", "P", "P", "B", "B"]})
    row, _, _ = evaluate(table, ST, None, None)
    assert row["auc"] == 1.0
    assert row["t1_status"] == "too few controls for cross-fitting"
    assert row["small"] is True


def test_small_sets_get_no_quoted_strength() -> None:
    rng = np.random.default_rng(0)
    table = pd.DataFrame(
        {"score": np.r_[rng.normal(2, 0.5, 30), rng.normal(0, 0.5, 6)], "label": ["P"] * 30 + ["B"] * 6}
    )
    row, _, _ = evaluate(table, ST, ">1", "<1")
    assert row["small"] is True
    assert row["t1_strength_abnormal"] == "not quoted (small)"
    assert row["t2_strength_normal"] == "not quoted (small)"
    assert np.isfinite(float(row["t1_oddspath_normal"]))


def test_malformed_and_multi_variant_hgvs_are_dropped() -> None:
    scores = pd.read_csv(DATA / "mavedb" / "toy_pten_one_class" / "scores.csv")
    keys = mavedb.protein_keys(scores, "NP_000305.3").set_index("protein_change")
    # 12 rows: 6 clean changes; missing score, truncated HGVS, multi-variant, nonsense and
    # other-protein rows dropped; the second p.Leu50Pro row averaged in.
    assert len(keys) == 6
    assert keys.loc["p.Leu50Pro", "n_score_rows"] == 2
    assert keys.loc["p.Leu50Pro", "score"] == pytest.approx(-1.6)


def test_nucleotide_keys_skip_unparseable_rows() -> None:
    scores = pd.DataFrame(
        {
            "scores.score": [1.0, 2.0, None],
            "hgvs_nt": ["garbage", "NM_007294.3:c.5096G>A", "NM_007294.3:c.1A>G"],
            "mavedb.post_mapped_hgvs_g": ["NC_000017.11:g.1_2del", None, None],
        }
    )
    keys = mavedb.nucleotide_keys(scores)
    assert list(keys["hgvs_c"]) == ["c.5096G>A"]


@pytest.mark.parametrize(
    ("rule", "values", "expected"),
    [
        ("<=-1.328", [-2.0, -1.328, 0.0], [True, True, False]),
        (">0", [-1.0, 0.0, 1.0], [False, False, True]),
        ("-1.11..0.89", [-1.2, -1.11, 0.89, 1.0], [False, True, True, False]),
    ],
)
def test_threshold_rules(rule: str, values: list[float], expected: list[bool]) -> None:
    assert parse_rule(rule)(np.array(values)).tolist() == expected


def test_bad_threshold_rule_raises() -> None:
    with pytest.raises(ValueError):
        parse_rule("about 3")
