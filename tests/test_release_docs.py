"""The README says how the Snakemake HTML report reaches a release, and it matches the release workflow."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_readme_says_how_the_report_reaches_the_release() -> None:
    readme = (ROOT / "README.md").read_text()
    workflow = (ROOT / ".github" / "workflows" / "release.yml").read_text()
    if "snakemake_report" in workflow:
        return  # the workflow attaches the report itself
    # The workflow publishes dist/* only, so the README must not imply the report arrives with
    # it, and must give the manual step.
    assert "is attached to the release, not kept in git" not in readme
    assert "make report" in readme and "gh release upload" in readme
