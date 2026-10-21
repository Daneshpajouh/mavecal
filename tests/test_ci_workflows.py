"""GitHub Actions workflows run third-party actions only at a fixed commit."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PINNED = re.compile(r"[\w.-]+/[\w.-]+@[0-9a-f]{40} # v\d+\.\d+\.\d+")


def workflow_files(root: Path) -> list[Path]:
    # GitHub runs both extensions.
    folder = root / ".github" / "workflows"
    return sorted([*folder.glob("*.yml"), *folder.glob("*.yaml")])


def unpinned(paths: list[Path]) -> list[tuple[str, str]]:
    uses = [
        (path.name, line.split("uses:", 1)[1].strip())
        for path in paths
        for line in path.read_text().splitlines()
        if line.strip().startswith(("uses:", "- uses:"))
    ]
    return [u for u in uses if not PINNED.fullmatch(u[1])]


def test_every_action_is_pinned_to_a_commit_with_its_version() -> None:
    paths = workflow_files(ROOT)
    assert paths
    assert unpinned(paths) == []


def test_a_yaml_workflow_with_a_moving_tag_fails(tmp_path: Path) -> None:
    folder = tmp_path / ".github" / "workflows"
    folder.mkdir(parents=True)
    (folder / "ci.yml").write_text(
        "steps:\n  - uses: actions/checkout@0123456789abcdef0123456789abcdef01234567 # v4.3.0\n"
    )
    (folder / "docs.yaml").write_text("steps:\n  - uses: actions/checkout@v4\n")
    assert unpinned(workflow_files(tmp_path)) == [("docs.yaml", "actions/checkout@v4")]
