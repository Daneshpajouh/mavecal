"""Run manifests written by the workflow's onstart and onsuccess/onerror handlers."""

from __future__ import annotations

import hashlib
import json
import os
import platform
import subprocess
import time
from datetime import UTC, datetime
from importlib import metadata
from pathlib import Path
from typing import Any

PACKAGES = ("snakemake", "numpy", "pandas", "scipy", "matplotlib", "requests", "mavecal")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def _file_record(path: Path, base: Path) -> dict[str, Any]:
    # Paths are stored relative to base so a manifest names no machine-specific directory.
    resolved = path.resolve()
    rel = os.path.relpath(path, base)
    return {"path": rel, "bytes": resolved.stat().st_size, "sha256": sha256(resolved)}


def _git(*args: str) -> str:
    try:
        res = subprocess.run(["git", *args], capture_output=True, text=True, check=False)
    except FileNotFoundError:
        # The container image has no git and no .git directory.
        return "unavailable"
    return res.stdout.strip()


def _versions() -> dict[str, str]:
    out = {"python": platform.python_version(), "platform": platform.platform()}
    for name in PACKAGES:
        try:
            out[name] = metadata.version(name)
        except metadata.PackageNotFoundError:
            out[name] = "not installed"
    return out


def write_start(out: Path, config: dict[str, Any], inputs: list[Path], plan: Path, data_dir: Path) -> None:
    """Record what the run is about to read, before any rule executes; inputs relative to data_dir."""
    out.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "started_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "started_epoch": time.time(),
        "git_commit": _git("rev-parse", "HEAD"),
        "git_uncommitted_changes": _git("status", "--porcelain", "--untracked-files=no") not in ("", "unavailable"),
        "analysis_plan": _file_record(plan, Path.cwd()),
        "versions": _versions(),
        "config": config,
        "inputs": [_file_record(p, data_dir) for p in inputs if p.exists()],
        "inputs_missing": [os.path.relpath(p, data_dir) for p in inputs if not p.exists()],
    }
    out.write_text(json.dumps(record, indent=1, default=str))


def write_end(out: Path, start: Path, status: str, results_dir: Path) -> None:
    """Record the outcome and hash every table and figure the run left in results_dir."""
    begun = json.loads(start.read_text()) if start.exists() else {}
    outputs = sorted(p for sub in ("tables", "figures") for p in (results_dir / sub).glob("*") if p.is_file())
    summary = results_dir / "tables" / "summary.tsv"
    record = {
        "status": status,
        "finished_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "duration_seconds": round(time.time() - begun["started_epoch"], 1) if "started_epoch" in begun else None,
        "git_commit": begun.get("git_commit"),
        "summary_table_sha256": sha256(summary) if summary.exists() else None,
        "outputs": [_file_record(p, Path.cwd()) for p in outputs],
    }
    out.write_text(json.dumps(record, indent=1))
