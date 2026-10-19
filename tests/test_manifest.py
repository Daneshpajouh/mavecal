"""Run manifests: hashes, relative paths and the start-to-end link."""

from __future__ import annotations

import json
from pathlib import Path

from mavecal import manifest

ABC_SHA256 = "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"  # FIPS 180-2 test vector


def test_sha256_known_vector(tmp_path: Path) -> None:
    f = tmp_path / "abc.txt"
    f.write_bytes(b"abc")
    assert manifest.sha256(f) == ABC_SHA256


def test_start_and_end_records(tmp_path: Path) -> None:
    data = tmp_path / "data"
    (data / "clinvar_releases").mkdir(parents=True)
    vs = data / "clinvar_releases" / "variant_summary_2026-10.txt.gz"
    vs.write_bytes(b"abc")
    plan = tmp_path / "plan.md"
    plan.write_text("plan")
    results = tmp_path / "results"
    (results / "tables").mkdir(parents=True)
    (results / "tables" / "summary.tsv").write_bytes(b"abc")
    start, end = tmp_path / "start.json", tmp_path / "end.json"

    manifest.write_start(start, {"n_boot": 2000}, [vs, data / "missing.gz"], plan, data)
    s = json.loads(start.read_text())
    assert s["inputs"] == [
        {"path": "clinvar_releases/variant_summary_2026-10.txt.gz", "bytes": 3, "sha256": ABC_SHA256}
    ]
    assert s["inputs_missing"] == ["missing.gz"]
    assert s["config"] == {"n_boot": 2000}

    manifest.write_end(end, start, "success", results)
    e = json.loads(end.read_text())
    assert e["status"] == "success"
    assert e["summary_table_sha256"] == ABC_SHA256
    assert e["duration_seconds"] >= 0
