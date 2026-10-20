"""The README says how the Snakemake HTML report reaches a release, and it matches the release workflow."""

from __future__ import annotations

import re
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


def upload_recipe(readme: str) -> str:
    blocks: list[str] = re.findall(r"```console\n(.*?)```", readme, re.S)
    recipe = [b for b in blocks if "gh release upload" in b]
    assert len(recipe) == 1
    return recipe[0]


def fixed_versions(recipe: str) -> list[str]:
    return re.findall(r"\bv?\d+\.\d+\.\d+\b", recipe)


def test_the_upload_recipe_names_no_fixed_version() -> None:
    assert fixed_versions(upload_recipe((ROOT / "README.md").read_text())) == []


def test_a_recipe_with_a_fixed_tag_fails() -> None:
    old = "```console\n$ make report\n$ gh release upload v2.0.0 report.html\n```\n"
    assert fixed_versions(upload_recipe(old)) == ["v2.0.0"]
