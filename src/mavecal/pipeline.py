"""Functions behind each workflow rule, kept here so they can be tested without Snakemake."""

from __future__ import annotations

import json
import logging
import shutil
from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd

from . import clinvar, matching, mavedb
from .analysis import Settings, evaluate
from .calibration import BIN_COLUMNS
from .stats import holm

log = logging.getLogger("mavecal")


def fetch(urn: str, out_dir: Path, offline_dir: str = "") -> None:
    """Download a score set, or copy it from a local directory for offline test runs."""
    if offline_dir:
        src = Path(offline_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        for name in ("scores.csv", "metadata.json"):
            shutil.copyfile(src / name, out_dir / name)
        log.info("copied %s from %s", urn, src)
        return
    res = mavedb.fetch_score_set(urn, out_dir)
    log.info("fetched %s: %d rows", urn, res.n_rows)


def filter_clinvar(variant_summary: Path, genes: list[str], out: Path) -> None:
    df = clinvar.load_variant_summary(variant_summary, genes)
    log.info("%s: %d GRCh38 SNV rows for %s", variant_summary.name, len(df), ",".join(genes))
    log.info("label counts: %s", df["label"].value_counts(dropna=False).to_dict())
    df.to_csv(out, sep="\t", index=False)


def filter_submissions(submission_summary: Path, variants: Path, out: Path) -> None:
    ids = pd.read_csv(variants, sep="\t", dtype=str)["variation_id"]
    sub = clinvar.load_submissions(submission_summary, ids)
    log.info("%d submissions for %d variants", len(sub), sub["variation_id"].nunique())
    sub.to_csv(out, sep="\t", index=False)


def labelled_variants(variants: Path, labels_source: str, published: str, submissions: Path | None) -> pd.DataFrame:
    """ClinVar variants with labels from the aggregate record or rebuilt before publication."""
    cv = pd.read_csv(variants, sep="\t", dtype={"variation_id": str, "chrom": str})
    cv["pos"] = cv["pos"].astype("Int64")
    if labels_source == "aggregate":
        return cv
    if submissions is None:
        raise ValueError("before_publication labels need a submission summary")
    sub = pd.read_csv(submissions, sep="\t", dtype=str)
    rebuilt = clinvar.labels_before(sub, date.fromisoformat(published))
    cv = cv.drop(columns=["label", "stars"]).merge(
        rebuilt[["variation_id", "label", "stars"]], on="variation_id", how="left"
    )
    cv["stars"] = cv["stars"].fillna(0).astype(int)
    return cv


def match(
    scores: Path,
    variants: Path,
    row: dict[str, str],
    analysis: dict[str, Any],
    submissions: Path | None,
    out_table: Path,
    out_stats: Path,
) -> None:
    raw = pd.read_csv(scores)
    needed = {"scores.score", "hgvs_nt", "mavedb.post_mapped_hgvs_g", "mavedb.post_mapped_hgvs_p"}
    if missing := sorted(needed - set(raw.columns)):
        raise ValueError(f"{scores}: MaveDB export lacks columns {missing}; was it fetched with the mavedb namespace?")
    cv = labelled_variants(variants, analysis["labels"], row["published"], submissions)
    stats: dict[str, Any] = {"scoreset": row["id"], "score_rows": len(raw)}
    if row["level"] == "protein":
        keys = mavedb.protein_keys(raw, row["protein"])
        table, discordant = matching.match_protein(keys, cv, row["transcript"], int(analysis["min_stars"]))
        stats["discordant_protein_changes"] = discordant
    else:
        keys = mavedb.nucleotide_keys(raw)
        table = matching.match_nucleotide(keys, cv, row["transcript"], int(analysis["min_stars"]))
    stats["assay_keys"] = len(keys)
    stats["matched"] = len(table)
    stats["by_method"] = table["match_method"].value_counts().to_dict()
    stats["by_label"] = table["label"].value_counts().to_dict()
    log.info("%s: %s", row["id"], stats)
    table.to_csv(out_table, sep="\t", index=False)
    out_stats.write_text(json.dumps(stats, indent=1, sort_keys=True))


def run_evaluate(
    matched: Path, row: dict[str, str], st: Settings, out_summary: Path, out_variants: Path, out_bins: Path
) -> None:
    table = pd.read_csv(matched, sep="\t")
    summary, per_variant, bins = evaluate(table, st, row.get("t2_abnormal") or None, row.get("t2_normal") or None)
    log.info("summary: %s", summary)
    out_summary.write_text(json.dumps(summary, indent=1, sort_keys=True, default=str))
    per_variant.to_csv(out_variants, sep="\t", index=False)
    # Without cross-fitting there are no bins; the header still says what the file holds.
    pd.DataFrame(bins, columns=list(BIN_COLUMNS)).to_csv(out_bins, sep="\t", index=False)


def aggregate(summaries: list[Path], match_stats: list[Path], out_summary: Path, out_matching: Path) -> None:
    """Combine per-analysis summaries; Holm-adjust the primary AUC tests across score sets."""
    rows = []
    for path in summaries:
        scoreset, analysis = path.parent.name, path.stem
        rows.append({"scoreset": scoreset, "analysis": analysis, **json.loads(path.read_text())})
    df = pd.DataFrame(rows)
    df["p_holm_primary"] = float("nan")
    if "p_one_sided" in df:
        primary = (df["analysis"] == "main") & df["p_one_sided"].notna()
    else:
        primary = pd.Series(False, index=df.index)
    if primary.any():
        df.loc[primary, "p_holm_primary"] = holm(df.loc[primary, "p_one_sided"].astype(float).tolist())
    df.sort_values(["scoreset", "analysis"]).to_csv(out_summary, sep="\t", index=False)
    ms = []
    for path in match_stats:
        d = json.loads(path.read_text())
        ms.append(
            {
                "scoreset": path.parent.name,
                "analysis": path.stem.replace(".match", ""),
                "score_rows": d["score_rows"],
                "assay_keys": d["assay_keys"],
                "matched": d["matched"],
                "pathogenic": d["by_label"].get("P", 0),
                "benign": d["by_label"].get("B", 0),
                "discordant_protein_changes": d.get("discordant_protein_changes", ""),
                "by_method": ";".join(f"{k}={v}" for k, v in sorted(d["by_method"].items())),
            }
        )
    pd.DataFrame(ms).sort_values(["scoreset", "analysis"]).to_csv(out_matching, sep="\t", index=False)
