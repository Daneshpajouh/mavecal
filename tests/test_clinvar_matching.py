"""ClinVar parsing, label rebuilding and score-to-label joins."""

from __future__ import annotations

import io
from datetime import date
from pathlib import Path

import pandas as pd

from mavecal import clinvar, matching, mavedb

FIX = Path(__file__).parent / "data"


def test_stars_and_labels() -> None:
    assert clinvar.review_stars("reviewed by expert panel") == 3
    assert clinvar.review_stars("criteria provided, multiple submitters, no conflicts") == 2
    assert clinvar.review_stars("criteria provided, conflicting interpretations") == 1
    assert clinvar.review_stars("no assertion criteria provided") == 0
    assert clinvar.label("Pathogenic/Likely pathogenic") == "P"
    assert clinvar.label("Likely benign") == "B"
    assert clinvar.label("Pathogenic; risk factor") is None
    assert clinvar.label("Uncertain significance") is None


def test_parse_name_and_missense() -> None:
    acc, c, p = clinvar.parse_name("NM_007294.4(BRCA1):c.5096G>A (p.Arg1699Gln)")
    assert (acc, c, p) == ("NM_007294", "c.5096G>A", "p.Arg1699Gln")
    assert clinvar.parse_name("NM_007294.4(BRCA1):c.5467+18A>T") == ("NM_007294", "c.5467+18A>T", None)
    assert clinvar.is_missense("p.Arg1699Gln")
    assert not clinvar.is_missense("p.Arg1699Ter")
    assert not clinvar.is_missense("p.Arg1699=")
    assert not clinvar.is_missense(float("nan"))
    # Start loss at the initiator Met1 is not a missense substitution.
    assert not clinvar.is_missense("p.Met1Val")
    assert not clinvar.is_missense("p.Met1Ile")
    assert clinvar.is_missense("p.Met10Val")
    assert clinvar.is_missense("p.Met11Val")


def test_load_variant_summary_keeps_grch38_snvs() -> None:
    df = clinvar.load_variant_summary(FIX / "variant_summary_tiny.txt.gz", ["TP53"])
    assert len(df) == 30  # 28 controls plus the discordant pair, GRCh37 copies dropped
    assert df["missense"].all()
    assert set(df["label"]) == {"P", "B"}


def test_load_variant_summary_without_variation_id(tmp_path: Path) -> None:
    # Releases before mid-2018 have no VariationID or VCF-style columns.
    old = pd.read_csv(FIX / "variant_summary_tiny.txt.gz", sep="\t", dtype=str)
    old = old.drop(columns=["VariationID", "PositionVCF", "ReferenceAlleleVCF", "AlternateAlleleVCF"])
    path = tmp_path / "old.txt.gz"
    old.to_csv(path, sep="\t", index=False)
    df = clinvar.load_variant_summary(path, ["TP53"])
    assert df["variation_id"].str.startswith("allele:").all()
    assert df["pos"].notna().all()


def test_labels_before_cutoff() -> None:
    sub = pd.DataFrame(
        {
            "variation_id": ["1", "1", "2", "2", "3", "4"],
            "ClinicalSignificance": [
                "Pathogenic",
                "Likely pathogenic",
                "Benign",
                "Uncertain significance",
                "Benign",
                "Benign",
            ],
            "DateLastEvaluated": ["Jan 01, 2017", "Feb 01, 2017", "Jan 01, 2017", "Jan 01, 2017", "Jan 01, 2020", "-"],
            "ReviewStatus": ["criteria provided, single submitter"] * 4 + ["reviewed by expert panel"] * 2,
            "Submitter": ["Lab A", "Lab B", "Lab A", "Lab B", "Panel", "Panel"],
        }
    )
    out = clinvar.labels_before(sub, date(2018, 1, 1)).set_index("variation_id")
    assert out.loc["1", "label"] == "P" and out.loc["1", "stars"] == 2
    assert "2" not in out.index  # benign and uncertain before the cutoff conflict
    assert "3" not in out.index  # evaluated after the cutoff
    assert "4" not in out.index  # no date


def test_labels_before_counts_submitters_not_submissions() -> None:
    # ClinVar gives two stars for agreeing criteria-provided assertions from two or more submitters.
    sub = pd.DataFrame(
        {
            "variation_id": ["1", "1", "2", "2"],
            "ClinicalSignificance": ["Pathogenic", "Pathogenic", "Pathogenic", "Likely pathogenic"],
            "DateLastEvaluated": ["Jan 01, 2017", "Mar 01, 2017", "Jan 01, 2017", "Mar 01, 2017"],
            "ReviewStatus": ["criteria provided, single submitter"] * 4,
            "Submitter": ["Lab A", "Lab A", "Lab A", "Lab B"],
        }
    )
    out = clinvar.labels_before(sub, date(2018, 1, 1)).set_index("variation_id")
    assert out.loc["1", "stars"] == 1  # one lab, two submissions
    assert out.loc["2", "stars"] == 2
    assert out["n_submitters"].tolist() == [1, 2]


def test_protein_keys_average_duplicates_and_filter_accession() -> None:
    scores = pd.DataFrame(
        {
            "scores.score": [1.0, 3.0, 5.0, 7.0, None],
            "mavedb.post_mapped_hgvs_p": [
                "NP_000537.3:p.Arg175His",
                "NP_000537.3:p.Arg175His",
                "NP_999999.1:p.Arg175His",
                "NP_000537.3:p.Arg175Ter",
                "NP_000537.3:p.Arg176His",
            ],
        }
    )
    keys = mavedb.protein_keys(scores, "NP_000537.3")
    assert keys.to_dict("records") == [
        {"protein_change": "p.Arg175His", "score": 2.0, "n_score_rows": 2, "match_method": "post_mapped_protein"}
    ]


def test_match_protein_drops_discordant_changes() -> None:
    cv = clinvar.load_variant_summary(FIX / "variant_summary_tiny.txt.gz", ["TP53"])
    keys = mavedb.protein_keys(pd.read_csv(FIX / "mavedb" / "toy_tp53" / "scores.csv"), "NP_000537.3")
    table, discordant = matching.match_protein(keys, cv, "NM_000546", min_stars=2)
    assert discordant == 1
    assert "p.Arg200His" not in set(table["variant"])
    assert (table["label"] == "P").sum() == 12 and (table["label"] == "B").sum() == 12


def test_nucleotide_keys_and_match() -> None:
    scores = pd.DataFrame(
        {
            "scores.score": [-2.0, 0.1],
            "hgvs_nt": ["NM_000546.5:c.10G>A", "NM_000546.5:c.11+3A>G"],
            "mavedb.post_mapped_hgvs_g": ["NC_000017.11:g.7670000G>A", None],
        }
    )
    keys = mavedb.nucleotide_keys(scores)
    assert list(keys["match_method"]) == ["post_mapped_genomic", "transcript_hgvs_c"]
    cv = clinvar.load_variant_summary(FIX / "variant_summary_tiny.txt.gz", ["TP53"])
    out = matching.match_nucleotide(keys, cv, "NM_000546", min_stars=2)
    assert len(out) == 1
    assert out.loc[0, "label"] == "P"


def test_mavedb_missense_change_excludes_start_loss() -> None:
    assert mavedb.missense_change("p.Met1Val") is None
    assert mavedb.missense_change("p.Met1Thr") is None
    assert mavedb.missense_change("p.Arg175His") == "p.Arg175His"
    assert mavedb.missense_change("p.Met100Val") == "p.Met100Val"


def test_match_nucleotide_averages_rows_for_one_allele() -> None:
    # Two score rows for c.299G>A (p.Arg100Ala, pathogenic in the fixture): one keyed by the
    # GRCh38 allele, one by the transcript c. HGVS. Both count, as duplicate protein rows do.
    scores = pd.DataFrame(
        {
            "scores.score": [-2.0, 0.0],
            "hgvs_nt": ["NM_000546.5:c.299G>A", "NM_000546.5:c.299G>A"],
            "mavedb.post_mapped_hgvs_g": ["NC_000017.11:g.7670000G>A", None],
        }
    )
    cv = clinvar.load_variant_summary(FIX / "variant_summary_tiny.txt.gz", ["TP53"])
    out = matching.match_nucleotide(mavedb.nucleotide_keys(scores), cv, "NM_000546", min_stars=2)
    assert len(out) == 1
    assert out.loc[0, "score"] == -1.0
    assert out.loc[0, "label"] == "P"


def test_nucleotide_keys_name_sex_chromosomes_as_clinvar_does() -> None:
    scores = pd.DataFrame(
        {
            "scores.score": [0.5, 0.7, 0.9],
            "hgvs_nt": [None, None, None],
            "mavedb.post_mapped_hgvs_g": [
                "NC_000023.11:g.154030912G>A",
                "NC_000024.10:g.2787000C>T",
                "NC_000002.12:g.47403000G>A",
            ],
        }
    )
    assert list(mavedb.nucleotide_keys(scores)["chrom"]) == ["X", "Y", "2"]


def test_protein_keys_header_only_score_set() -> None:
    header = "accession,hgvs_nt,hgvs_pro,scores.score,mavedb.post_mapped_hgvs_g,mavedb.post_mapped_hgvs_p\n"
    keys = mavedb.protein_keys(pd.read_csv(io.StringIO(header)), "NP_000537.3")
    assert keys.empty
    assert list(keys.columns) == ["protein_change", "score", "n_score_rows", "match_method"]
