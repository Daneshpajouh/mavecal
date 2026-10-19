"""Download MaveDB score sets and turn post-mapped HGVS into join keys."""

from __future__ import annotations

import io
import json
import re
import time
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import requests

API = "https://api.mavedb.org/api/v1"
# MaveDB has no published rate limit; one request per second keeps the load negligible.
PAUSE_SECONDS = 1.0
TIMEOUT_SECONDS = 300

THREE_LETTER = re.compile(r"^p\.([A-Z][a-z]{2})(\d+)([A-Z][a-z]{2})$")
GENOMIC_SNV = re.compile(r"^(NC_0000(\d{2}))\.\d+:g\.(\d+)([ACGT])>([ACGT])$")
TRANSCRIPT_C = re.compile(r"^(N[MR]_\d+)\.\d+:(c\.\S+)$")


@dataclass(frozen=True)
class FetchResult:
    metadata_path: Path
    scores_path: Path
    n_rows: int


def fetch_score_set(urn: str, out_dir: Path, session: requests.Session | None = None) -> FetchResult:
    """Save the score set record and its scores with post-mapped HGVS columns."""
    out_dir.mkdir(parents=True, exist_ok=True)
    http = session or requests.Session()
    meta = http.get(f"{API}/score-sets/{urn}", timeout=TIMEOUT_SECONDS)
    meta.raise_for_status()
    metadata_path = out_dir / "metadata.json"
    metadata_path.write_text(json.dumps(meta.json(), indent=1, sort_keys=True))
    time.sleep(PAUSE_SECONDS)
    data = http.get(
        f"{API}/score-sets/{urn}/variants/data",
        params=[("namespaces", "scores"), ("namespaces", "mavedb")],
        timeout=TIMEOUT_SECONDS,
    )
    data.raise_for_status()
    scores_path = out_dir / "scores.csv"
    scores_path.write_text(data.text)
    n_rows = len(pd.read_csv(io.StringIO(data.text)))
    time.sleep(PAUSE_SECONDS)
    return FetchResult(metadata_path, scores_path, n_rows)


def missense_change(hgvs_p: str) -> str | None:
    """Return 'p.Arg175His' for a single missense substitution, else None.

    Changes at position 1 (start loss) are not missense; see clinvar.is_missense.
    """
    m = THREE_LETTER.match(hgvs_p)
    if m is None:
        return None
    ref, pos, alt = m.groups()
    if alt == ref or alt == "Ter" or pos == "1":
        return None
    return hgvs_p


def protein_keys(scores: pd.DataFrame, protein_accession: str) -> pd.DataFrame:
    """Key protein-level scores by missense change on the expected RefSeq protein.

    Rows that are unmapped, mapped to another protein, or not a single missense
    substitution are dropped. Duplicate rows for one change are averaged.
    """
    base = protein_accession.split(".")[0]
    mapped = scores["mavedb.post_mapped_hgvs_p"].fillna("")
    parts = mapped.str.split(":", n=1, expand=True)
    if parts.shape[1] < 2:
        parts[1] = ""
    acc = parts[0].str.split(".").str[0]
    change = parts[1].fillna("").map(missense_change)
    keep = (acc == base) & change.notna() & scores["scores.score"].notna()
    out = pd.DataFrame({"protein_change": change[keep], "score": scores.loc[keep, "scores.score"]})
    agg = out.groupby("protein_change", as_index=False).agg(score=("score", "mean"), n_score_rows=("score", "size"))
    agg["match_method"] = "post_mapped_protein"
    return agg


def nucleotide_keys(scores: pd.DataFrame) -> pd.DataFrame:
    """Key nucleotide-level scores by GRCh38 SNV, falling back to transcript c. HGVS."""
    rows: list[dict[str, object]] = []
    for g, c, score in zip(
        scores["mavedb.post_mapped_hgvs_g"].fillna(""),
        scores["hgvs_nt"].fillna(""),
        scores["scores.score"],
        strict=True,
    ):
        if pd.isna(score):
            continue
        gm = GENOMIC_SNV.match(g)
        if gm is not None:
            _, chrom, pos, ref, alt = gm.groups()
            rows.append(
                {
                    "chrom": str(int(chrom)),
                    "pos": int(pos),
                    "ref": ref,
                    "alt": alt,
                    "transcript": None,
                    "hgvs_c": None,
                    "score": float(score),
                    "match_method": "post_mapped_genomic",
                }
            )
            continue
        cm = TRANSCRIPT_C.match(c)
        if cm is not None:
            rows.append(
                {
                    "chrom": None,
                    "pos": None,
                    "ref": None,
                    "alt": None,
                    "transcript": cm.group(1),
                    "hgvs_c": cm.group(2),
                    "score": float(score),
                    "match_method": "transcript_hgvs_c",
                }
            )
    return pd.DataFrame(
        rows,
        columns=["chrom", "pos", "ref", "alt", "transcript", "hgvs_c", "score", "match_method"],
    )
