"""Write the synthetic fixtures used by the tests and the integration run.

The variants, labels and scores below are invented for testing. They are not ClinVar
or MaveDB records. Run from the repository root: python tests/data/make_fixtures.py
"""

from __future__ import annotations

import gzip
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).parent
AA = ["Ala", "Cys", "Asp", "Glu", "Phe", "Gly", "His", "Ile", "Lys", "Leu", "Met", "Asn"]
VS_HEADER = [
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


def main() -> None:
    rng = np.random.default_rng(7)
    vs_rows: list[list[str]] = []
    sub_rows: list[list[str]] = []
    score_rows: list[list[str]] = []
    vid = 1000
    # Protein-level toy assay on TP53: 14 pathogenic and 14 benign missense controls.
    for i in range(28):
        pos = 100 + i
        alt = AA[i % len(AA)]
        change = f"p.Arg{pos}{alt}"
        is_path = i % 2 == 0
        score = rng.normal(1.0 if is_path else -0.5, 0.6)
        score_rows.append(
            [
                f"urn:mavedb:00000000-a-1#{i}",
                "NA",
                "NA",
                change,
                f"{score:.4f}",
                "NA",
                f"NP_000537.3:{change}",
                "NA",
                f"NP_000537.3:{change}",
                "NA",
            ]
        )
        vid += 1
        stars_status = (
            "criteria provided, multiple submitters, no conflicts" if i < 24 else "criteria provided, single submitter"
        )
        sig = "Pathogenic" if is_path else "Benign"
        for assembly in ("GRCh38", "GRCh37"):
            vs_rows.append(
                [
                    str(vid),
                    "single nucleotide variant",
                    f"NM_000546.6(TP53):c.{3 * pos - 1}G>A ({change})",
                    "TP53",
                    sig,
                    stars_status,
                    assembly,
                    "17",
                    str(7670000 + i),
                    "G",
                    "A",
                    str(vid),
                    str(7670000 + i),
                    "G",
                    "A",
                ]
            )
        date = "Mar 01, 2017" if i % 3 else "Mar 01, 2022"
        for k in range(2 if i < 24 else 1):
            sub_rows.append(
                [
                    str(vid),
                    sig,
                    date,
                    "-",
                    "-",
                    "-",
                    "criteria provided, single submitter",
                    "clinical testing",
                    "germline:na",
                    f"Lab {k}",
                    f"SCV{vid:09d}.{k + 1}",
                    "TP53",
                    "-",
                    "-",
                    "-",
                    "yes",
                ]
            )
    # A protein change with discordant labels, which must be dropped.
    vs_rows.append(
        [
            "2001",
            "single nucleotide variant",
            "NM_000546.6(TP53):c.999G>A (p.Arg200His)",
            "TP53",
            "Pathogenic",
            "criteria provided, multiple submitters, no conflicts",
            "GRCh38",
            "17",
            "7671000",
            "G",
            "A",
            "2001",
            "7671000",
            "G",
            "A",
        ]
    )
    vs_rows.append(
        [
            "2002",
            "single nucleotide variant",
            "NM_000546.6(TP53):c.998C>A (p.Arg200His)",
            "TP53",
            "Benign",
            "criteria provided, multiple submitters, no conflicts",
            "GRCh38",
            "17",
            "7671001",
            "C",
            "A",
            "2002",
            "7671001",
            "C",
            "A",
        ]
    )
    score_rows.append(
        [
            "urn:mavedb:00000000-a-1#99",
            "NA",
            "NA",
            "p.Arg200His",
            "0.1",
            "NA",
            "NP_000537.3:p.Arg200His",
            "NA",
            "NA",
            "NA",
        ]
    )

    # PTEN: a gene with pathogenic controls only, so AUC and OddsPath cannot be estimated.
    pten_scores: list[list[str]] = []
    for i in range(6):
        change = f"p.Leu{50 + i}Pro"
        vid += 1
        vs_rows.append(
            [
                str(vid),
                "single nucleotide variant",
                f"NM_000314.8(PTEN):c.{150 + 3 * i}T>C ({change})",
                "PTEN",
                "Pathogenic",
                "criteria provided, multiple submitters, no conflicts",
                "GRCh38",
                "10",
                str(87900000 + i),
                "T",
                "C",
                str(vid),
                str(87900000 + i),
                "T",
                "C",
            ]
        )
        pten_scores.append(
            [
                f"urn:mavedb:00000000-b-1#{i}",
                "NA",
                "NA",
                change,
                f"{-1.5 - 0.1 * i:.2f}",
                "NA",
                f"NP_000305.3:{change}",
                "NA",
                "NA",
                "NA",
            ]
        )
    # Rows the key builder must drop or merge: a missing score, malformed and multi-variant
    # HGVS, a nonsense change, another protein, and a second row for one change (averaged).
    pten_scores += [
        [
            "urn:mavedb:00000000-b-1#90",
            "NA",
            "NA",
            "p.Leu60Pro",
            "NA",
            "NA",
            "NP_000305.3:p.Leu60Pro",
            "NA",
            "NA",
            "NA",
        ],
        ["urn:mavedb:00000000-b-1#91", "NA", "NA", "p.Leu61", "-1.0", "NA", "NP_000305.3:p.Leu61", "NA", "NA", "NA"],
        [
            "urn:mavedb:00000000-b-1#92",
            "NA",
            "NA",
            "p.[Leu62Pro;Leu63Pro]",
            "-1.0",
            "NA",
            "NP_000305.3:p.[Leu62Pro;Leu63Pro]",
            "NA",
            "NA",
            "NA",
        ],
        [
            "urn:mavedb:00000000-b-1#93",
            "NA",
            "NA",
            "p.Leu64Ter",
            "-3.0",
            "NA",
            "NP_000305.3:p.Leu64Ter",
            "NA",
            "NA",
            "NA",
        ],
        [
            "urn:mavedb:00000000-b-1#94",
            "NA",
            "NA",
            "p.Leu65Pro",
            "-1.0",
            "NA",
            "NP_999999.1:p.Leu65Pro",
            "NA",
            "NA",
            "NA",
        ],
        [
            "urn:mavedb:00000000-b-1#95",
            "NA",
            "NA",
            "p.Leu50Pro",
            "-1.7",
            "NA",
            "NP_000305.3:p.Leu50Pro",
            "NA",
            "NA",
            "NA",
        ],
    ]

    header = (
        "accession,hgvs_nt,hgvs_splice,hgvs_pro,scores.score,mavedb.post_mapped_hgvs_g,"
        "mavedb.post_mapped_hgvs_p,mavedb.post_mapped_hgvs_c,mavedb.post_mapped_hgvs_at_assay_level,"
        "mavedb.post_mapped_vrs_id"
    )
    out = HERE / "mavedb" / "toy_tp53"
    out.mkdir(parents=True, exist_ok=True)
    (out / "scores.csv").write_text(header + "\n" + "\n".join(",".join(r) for r in score_rows) + "\n")
    (out / "metadata.json").write_text(
        json.dumps({"urn": "urn:mavedb:00000000-a-1", "note": "synthetic test fixture"}, indent=1)
    )
    out = HERE / "mavedb" / "toy_pten_one_class"
    out.mkdir(parents=True, exist_ok=True)
    (out / "scores.csv").write_text(header + "\n" + "\n".join(",".join(r) for r in pten_scores) + "\n")
    (out / "metadata.json").write_text(
        json.dumps({"urn": "urn:mavedb:00000000-b-1", "note": "synthetic test fixture"}, indent=1)
    )

    with gzip.open(HERE / "variant_summary_tiny.txt.gz", "wt") as fh:
        fh.write("\t".join(VS_HEADER) + "\n")
        for r in vs_rows:
            fh.write("\t".join(r) + "\n")
    sub_header = [
        "#VariationID",
        "ClinicalSignificance",
        "DateLastEvaluated",
        "Description",
        "SubmittedPhenotypeInfo",
        "ReportedPhenotypeInfo",
        "ReviewStatus",
        "CollectionMethod",
        "OriginCounts",
        "Submitter",
        "SCV",
        "SubmittedGeneSymbol",
        "ExplanationOfInterpretation",
        "SomaticClinicalImpact",
        "Oncogenicity",
        "ContributesToAggregateClassification",
    ]
    with gzip.open(HERE / "submission_summary_tiny.txt.gz", "wt") as fh:
        fh.write("##Synthetic submission summary for tests\n#VariationID:   column note\n")
        fh.write("\t".join(sub_header) + "\n")
        for r in sub_rows:
            fh.write("\t".join(r) + "\n")


if __name__ == "__main__":
    main()
