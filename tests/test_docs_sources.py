"""Statements about outside sources in the docs are checked, not left as open notes."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = [ROOT / "README.md", *sorted((ROOT / "docs").glob("*.md"))]


def test_no_source_statement_is_left_unchecked() -> None:
    open_notes = [
        f"{path.relative_to(ROOT)}:{number}"
        for path in DOCS
        for number, line in enumerate(path.read_text().splitlines(), 1)
        if "not yet checked" in line or "has not yet been checked" in line
    ]
    assert open_notes == []


def test_the_brnich_quote_and_the_record_links_are_given() -> None:
    methods = (ROOT / "docs" / "methods.md").read_text()
    report = (ROOT / "docs" / "report.md").read_text()
    assert "we added exactly one misclassified variant to each set" in " ".join(methods.split())
    assert "urn:mavedb:00000097-0-2/calibrations" in report
    assert "urn:mavedb:00000050-a-1/calibrations" in report
