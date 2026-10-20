"""GitHub Actions workflows run third-party actions only at a fixed commit."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = sorted((ROOT / ".github" / "workflows").glob("*.yml"))
PINNED = re.compile(r"[\w.-]+/[\w.-]+@[0-9a-f]{40} # v\d+\.\d+\.\d+")


def test_every_action_is_pinned_to_a_commit_with_its_version() -> None:
    uses = [
        (path.name, line.split("uses:", 1)[1].strip())
        for path in WORKFLOWS
        for line in path.read_text().splitlines()
        if line.strip().startswith(("uses:", "- uses:"))
    ]
    assert uses
    assert [u for u in uses if not PINNED.fullmatch(u[1])] == []
