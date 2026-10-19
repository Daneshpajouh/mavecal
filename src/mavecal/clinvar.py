"""Read ClinVar tab-delimited releases and derive labels and review stars."""

from __future__ import annotations

import re
from collections.abc import Iterable
from datetime import date, datetime
from pathlib import Path

import pandas as pd

PATHOGENIC = frozenset({"Pathogenic", "Likely pathogenic", "Pathogenic/Likely pathogenic"})
BENIGN = frozenset({"Benign", "Likely benign", "Benign/Likely benign"})

STARS = {
    "practice guideline": 4,
    "reviewed by expert panel": 3,
    "criteria provided, multiple submitters, no conflicts": 2,
    "criteria provided, single submitter": 1,
    "criteria provided, conflicting classifications": 1,
    "criteria provided, conflicting interpretations": 1,
}

NAME = re.compile(r"^(N[MR]_\d+)\.\d+\([^)]*\):(c\.\S+)(?: \((p\.[^)]+)\))?")
MISSENSE = re.compile(r"^p\.([A-Z][a-z]{2})(\d+)([A-Z][a-z]{2})$")

VS_COLUMNS = [
    "#AlleleID",
    "Type",
    "Name",
    "GeneSymbol",
    "ClinicalSignificance",
    "ReviewStatus",
    "Assembly",
    "Chromosome",
    "Start",
    "ReferenceAllele",
    "AlternateAllele",
    "VariationID",
    "PositionVCF",
    "ReferenceAlleleVCF",
    "AlternateAlleleVCF",
]


def review_stars(status: str) -> int:
    """Map a ClinVar review status string to the star count shown on the website."""
    return STARS.get(str(status).strip(), 0)


def label(significance: str) -> str | None:
    """Return 'P', 'B' or None for a ClinVar germline classification string."""
    s = str(significance).strip()
    if s in PATHOGENIC:
        return "P"
    if s in BENIGN:
        return "B"
    return None


def parse_name(name: str) -> tuple[str | None, str | None, str | None]:
    """Split 'NM_007294.4(BRCA1):c.5096G>A (p.Arg1699Gln)' into accession, c. and p."""
    m = NAME.match(str(name))
    if m is None:
        return None, None, None
    return m.group(1), m.group(2), m.group(3)


def is_missense(hgvs_p: object) -> bool:
    """True for a single amino acid substitution other than at the initiator Met1.

    A change at position 1 removes the start codon; it does not substitute one
    residue in the protein the assay measures, so it is not counted as missense.
    """
    if not isinstance(hgvs_p, str):
        return False
    m = MISSENSE.match(hgvs_p)
    return m is not None and m.group(2) != "1" and m.group(3) not in (m.group(1), "Ter")


def load_variant_summary(path: Path, genes: Iterable[str], chunksize: int = 400_000) -> pd.DataFrame:
    """Read GRCh38 single nucleotide variants for the given genes from variant_summary.

    Older releases (for example 2018-01) lack the VCF-style columns; for SNVs the
    Start, ReferenceAllele and AlternateAllele columns carry the same information.
    """
    wanted = set(genes)
    header = pd.read_csv(path, sep="\t", nrows=0).columns
    missing = sorted(set(VS_COLUMNS[:9]) - set(header))
    if missing:
        raise ValueError(f"{path}: not a ClinVar variant_summary file, missing columns {missing}")
    usecols = [c for c in VS_COLUMNS if c in header]
    parts: list[pd.DataFrame] = []
    for chunk in pd.read_csv(path, sep="\t", usecols=usecols, dtype=str, chunksize=chunksize, low_memory=False):
        chunk = chunk[(chunk["Assembly"] == "GRCh38") & (chunk["Type"] == "single nucleotide variant")]
        gene_hit = chunk["GeneSymbol"].fillna("").str.split(";").map(lambda gs: bool(wanted & set(gs)))
        parts.append(chunk[gene_hit])
    df = pd.concat(parts, ignore_index=True)
    if "VariationID" not in df.columns:
        # Releases before mid-2018 carry no VariationID; AlleleID is unique per SNV there.
        df["VariationID"] = "allele:" + df["#AlleleID"].astype(str)
    if "PositionVCF" not in df.columns:
        df["PositionVCF"] = df["Start"]
        df["ReferenceAlleleVCF"] = df["ReferenceAllele"]
        df["AlternateAlleleVCF"] = df["AlternateAllele"]
    parsed = df["Name"].map(parse_name)
    out = pd.DataFrame(
        {
            "variation_id": df["VariationID"].astype(str),
            "gene": df["GeneSymbol"],
            "name": df["Name"],
            "transcript": [p[0] for p in parsed],
            "hgvs_c": [p[1] for p in parsed],
            "hgvs_p": [p[2] for p in parsed],
            "chrom": df["Chromosome"].astype(str),
            "pos": pd.to_numeric(df["PositionVCF"], errors="coerce").astype("Int64"),
            "ref": df["ReferenceAlleleVCF"],
            "alt": df["AlternateAlleleVCF"],
            "significance": df["ClinicalSignificance"],
            "review_status": df["ReviewStatus"],
        }
    )
    out["label"] = out["significance"].map(label)
    out["stars"] = out["review_status"].map(review_stars).astype(int)
    out["missense"] = out["hgvs_p"].map(is_missense)
    return out.drop_duplicates(subset=["variation_id"]).reset_index(drop=True)


def parse_clinvar_date(text: str) -> date | None:
    """Parse 'Jun 25, 2024'; ClinVar writes '-' when the date is missing."""
    try:
        return datetime.strptime(str(text).strip(), "%b %d, %Y").date()
    except ValueError:
        return None


def load_submissions(path: Path, variation_ids: Iterable[str], chunksize: int = 400_000) -> pd.DataFrame:
    """Read submission (SCV) rows for the given VariationIDs from submission_summary."""
    ids = set(variation_ids)
    cols = ["#VariationID", "ClinicalSignificance", "DateLastEvaluated", "ReviewStatus", "Submitter", "SCV"]
    parts = []
    for chunk in pd.read_csv(
        path, sep="\t", comment=None, skiprows=_header_skip(path), usecols=cols, dtype=str, chunksize=chunksize
    ):
        parts.append(chunk[chunk["#VariationID"].isin(ids)])
    df = pd.concat(parts, ignore_index=True).rename(columns={"#VariationID": "variation_id"})
    return df


def _header_skip(path: Path) -> int:
    """submission_summary starts with '##' comment lines and '#' column notes before the header."""
    import gzip

    opener = gzip.open if str(path).endswith(".gz") else open
    with opener(path, "rt") as fh:
        for i, line in enumerate(fh):
            if line.startswith("#VariationID\t"):
                return i
    raise ValueError(f"no header line found in {path}")


def labels_before(submissions: pd.DataFrame, cutoff: date) -> pd.DataFrame:
    """Rebuild a label and approximate stars from submissions evaluated before cutoff.

    Only submissions with assertion criteria count. A variant keeps a label only if
    every such submission agrees on P/LP or on B/LB; any other class among them
    (for example uncertain significance) removes the label, as ClinVar would report
    a conflict.
    """
    sub = submissions.copy()
    sub["date"] = sub["DateLastEvaluated"].map(parse_clinvar_date)
    sub = sub[sub["date"].map(lambda d: d is not None and d < cutoff)]
    status = sub["ReviewStatus"].fillna("")
    sub = sub[
        status.str.startswith("criteria provided") | status.isin(["reviewed by expert panel", "practice guideline"])
    ]
    rows = []
    for vid, grp in sub.groupby("variation_id"):
        labs = {label(s) for s in grp["ClinicalSignificance"]}
        if len(labs) != 1 or None in labs:
            continue
        statuses = set(grp["ReviewStatus"])
        if "practice guideline" in statuses:
            stars = 4
        elif "reviewed by expert panel" in statuses:
            stars = 3
        elif len(grp) >= 2:
            stars = 2
        else:
            stars = 1
        rows.append({"variation_id": vid, "label": labs.pop(), "stars": stars, "n_submissions": len(grp)})
    return pd.DataFrame(rows, columns=["variation_id", "label", "stars", "n_submissions"])
