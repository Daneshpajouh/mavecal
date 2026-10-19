"""Join assay scores to ClinVar labels at protein or nucleotide level."""

from __future__ import annotations

import pandas as pd


def eligible(clinvar: pd.DataFrame, transcript: str, min_stars: int) -> pd.DataFrame:
    """Missense SNVs on the reference transcript with a P or B label at the star threshold."""
    keep = (
        (clinvar["transcript"] == transcript)
        & clinvar["missense"]
        & clinvar["label"].notna()
        & (clinvar["stars"] >= min_stars)
    )
    return clinvar[keep]


def match_protein(
    keys: pd.DataFrame, clinvar: pd.DataFrame, transcript: str, min_stars: int
) -> tuple[pd.DataFrame, int]:
    """Label each assayed protein change; return the table and the number of discordant changes."""
    elig = eligible(clinvar, transcript, min_stars)
    per_change = elig.groupby("hgvs_p").agg(
        labels=("label", lambda s: "".join(sorted(set(s)))),
        stars=("stars", "max"),
        n_clinvar=("variation_id", "size"),
        variation_ids=("variation_id", lambda s: ";".join(sorted(s))),
    )
    discordant = int((per_change["labels"] == "BP").sum())
    per_change = per_change[per_change["labels"].isin(["P", "B"])].rename(columns={"labels": "label"})
    out = keys.merge(per_change, left_on="protein_change", right_index=True, how="inner")
    out = out.rename(columns={"protein_change": "variant"})
    return out[["variant", "score", "label", "stars", "n_clinvar", "variation_ids", "match_method"]], discordant


def match_nucleotide(keys: pd.DataFrame, clinvar: pd.DataFrame, transcript: str, min_stars: int) -> pd.DataFrame:
    """Label each assayed SNV by GRCh38 allele, or by transcript c. HGVS when unmapped."""
    elig = eligible(clinvar, transcript, min_stars).copy()
    elig["pos"] = elig["pos"].astype("Int64")
    genomic = keys[keys["match_method"] == "post_mapped_genomic"].copy()
    genomic["pos"] = genomic["pos"].astype("Int64")
    g = genomic.merge(elig, on=["chrom", "pos", "ref", "alt"], how="inner", suffixes=("", "_cv"))
    by_c = keys[keys["match_method"] == "transcript_hgvs_c"].merge(
        elig, on=["transcript", "hgvs_c"], how="inner", suffixes=("", "_cv")
    )
    both = pd.concat([g, by_c], ignore_index=True)
    both["variant"] = both["name"]
    both["n_clinvar"] = 1
    both["variation_ids"] = both["variation_id"]
    both = both.drop_duplicates(subset=["variation_id"])
    return both[["variant", "score", "label", "stars", "n_clinvar", "variation_ids", "match_method"]].reset_index(
        drop=True
    )
