"""Workflow-level checks: lint, dry-run, schema validation and an offline end-to-end run."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
VENV_SMK = ROOT / ".venv" / "bin" / "snakemake"
SNAKEMAKE = str(VENV_SMK) if VENV_SMK.exists() else (shutil.which("snakemake") or "")
TEST_CONFIG = ".tests/integration/config/config.yaml"

pytestmark = pytest.mark.skipif(not SNAKEMAKE, reason="snakemake not installed")


def run(*args: str) -> subprocess.CompletedProcess[str]:
    # A data directory set for real runs would override the test configuration's.
    env = {k: v for k, v in os.environ.items() if k != "MAVECAL_DATA_DIR"}
    return subprocess.run([SNAKEMAKE, *args], cwd=ROOT, capture_output=True, text=True, check=False, env=env)


def test_lint_is_clean() -> None:
    res = run("--lint", "--configfile", TEST_CONFIG)
    assert res.returncode == 0, res.stdout + res.stderr
    assert "Congratulations" in res.stdout + res.stderr


def test_dry_run_plans_every_rule() -> None:
    res = run("-n", "--forceall", "--quiet", "rules", "--configfile", TEST_CONFIG)
    assert res.returncode == 0, res.stderr
    for rule in ("fetch_mavedb", "filter_clinvar", "filter_submissions", "match_controls", "evaluate", "aggregate"):
        assert rule in res.stdout + res.stderr


def test_schema_rejects_bad_config(tmp_path: Path) -> None:
    bad = tmp_path / "bad.yaml"
    bad.write_text("statistics: {n_boot: 5, seed: 1, n_folds: 5, min_per_class_threshold: 5, small_class: 10}\n")
    res = run("-n", "--configfile", TEST_CONFIG, str(bad))
    assert res.returncode != 0
    assert "n_boot" in res.stdout + res.stderr


def test_offline_run_end_to_end() -> None:
    for d in (".tests/integration/data", ".tests/integration/results"):
        shutil.rmtree(ROOT / d, ignore_errors=True)
    res = run("--cores", "2", "--retries", "2", "--configfile", TEST_CONFIG)
    assert res.returncode == 0, res.stderr[-3000:]
    summary = pd.read_csv(ROOT / ".tests/integration/results/tables/summary.tsv", sep="\t")
    assert len(summary) == 10  # two score sets times five analyses
    one_class = summary[summary["scoreset"] == "toy_pten_one_class"]
    assert (one_class["status"] == "one class missing").all()
    toy = summary[(summary["scoreset"] == "toy_tp53") & (summary["analysis"] == "main")].iloc[0]
    assert toy["n_pathogenic"] == 12 and toy["n_benign"] == 12
    assert (ROOT / ".tests/integration/results/figures/toy_tp53.svg").exists()
