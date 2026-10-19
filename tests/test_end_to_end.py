"""Run each pipeline step on the synthetic fixtures without Snakemake."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from mavecal import pipeline, plots
from mavecal.analysis import Settings
from mavecal.logs import setup_logging

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "tests" / "data"
ROW = {
    "id": "toy_tp53",
    "gene": "TP53",
    "published": "2020-01-01",
    "level": "protein",
    "transcript": "NM_000546",
    "protein": "NP_000537.3",
    "direction": "higher_is_abnormal",
    "t2_abnormal": ">0.5",
    "t2_normal": "<0",
}


def test_pipeline_functions(tmp_path: Path) -> None:
    variants = tmp_path / "variants.tsv.gz"
    pipeline.filter_clinvar(DATA / "variant_summary_tiny.txt.gz", ["TP53"], variants)
    subs = tmp_path / "subs.tsv.gz"
    pipeline.filter_submissions(DATA / "submission_summary_tiny.txt.gz", variants, subs)
    table, stats = tmp_path / "m.tsv", tmp_path / "m.json"
    pipeline.match(
        DATA / "mavedb" / "toy_tp53" / "scores.csv",
        variants,
        ROW,
        {"labels": "aggregate", "min_stars": 2},
        None,
        table,
        stats,
    )
    assert json.loads(stats.read_text())["matched"] == 24
    st = Settings("higher_is_abnormal", 200, 1, 5, 5, 10, 1)
    out = tmp_path / "s.json"
    pipeline.run_evaluate(table, ROW, st, out, tmp_path / "v.tsv", tmp_path / "b.tsv")
    s = json.loads(out.read_text())
    assert s["n_pathogenic"] == 12 and s["n_benign"] == 12
    assert 0.5 < s["auc"] <= 1.0
    assert s["auc_lo"] <= s["auc"] <= s["auc_hi"]
    assert s["t1_p_abnormal"] + s["t1_p_normal"] == 12
    per_variant = pd.read_csv(tmp_path / "v.tsv", sep="\t")
    assert per_variant["p_label_pathogenic_oof"].between(0, 1).all()


def test_aggregate_and_figures(tmp_path: Path) -> None:
    setup_logging(tmp_path / "log.txt")
    variants = tmp_path / "variants.tsv.gz"
    pipeline.filter_clinvar(DATA / "variant_summary_tiny.txt.gz", ["TP53"], variants)
    st = Settings("higher_is_abnormal", 200, 1, 5, 5, 10, 1)
    summaries, stats = [], []
    for analysis, stars in (("main", 2), ("s1_one_star", 1)):
        d = tmp_path / "toy_tp53"
        d.mkdir(exist_ok=True)
        pipeline.match(
            DATA / "mavedb" / "toy_tp53" / "scores.csv",
            variants,
            ROW,
            {"labels": "aggregate", "min_stars": stars},
            None,
            d / f"{analysis}.tsv",
            d / f"{analysis}.match.json",
        )
        pipeline.run_evaluate(
            d / f"{analysis}.tsv", ROW, st, d / f"{analysis}.json", d / f"{analysis}.v.tsv", d / f"{analysis}.b.tsv"
        )
        summaries.append(d / f"{analysis}.json")
        stats.append(d / f"{analysis}.match.json")
    pipeline.aggregate(summaries, stats, tmp_path / "summary.tsv", tmp_path / "matching.tsv")
    summary = pd.read_csv(tmp_path / "summary.tsv", sep="\t")
    assert summary.loc[summary["analysis"] == "main", "p_holm_primary"].notna().all()
    assert summary.loc[summary["analysis"] != "main", "p_holm_primary"].isna().all()
    d = tmp_path / "toy_tp53"
    plots.scoreset_figure(
        d / "main.v.tsv",
        d / "main.json",
        d / "main.b.tsv",
        "toy",
        "higher_is_abnormal",
        tmp_path / "f.png",
        tmp_path / "f.svg",
    )
    plots.forest_figure(tmp_path / "summary.tsv", tmp_path / "forest.png", tmp_path / "forest.svg")
    for name in ("f.png", "f.svg", "forest.png", "forest.svg"):
        assert (tmp_path / name).stat().st_size > 1000
    assert "INFO" in (tmp_path / "log.txt").read_text()
