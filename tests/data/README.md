# Test data

Everything here is synthetic and written by `make_fixtures.py` (seeded, so it is reproducible).
None of it is a ClinVar or MaveDB record; the HGVS strings only have the right shape.

| file | what it holds | what it tests |
|---|---|---|
| `variant_summary_tiny.txt.gz` | 64 rows in the ClinVar `variant_summary` layout: 28 TP53 missense SNVs (14 Pathogenic, 14 Benign) on GRCh38 and GRCh37, a discordant pair (one Pathogenic and one Benign SNV that both encode p.Arg200His), and 6 PTEN Pathogenic SNVs | GRCh38 filter, star mapping (24 TP53 controls at 2 stars, 4 at 1 star), discordant protein changes, a gene with one class only |
| `submission_summary_tiny.txt.gz` | submission rows for the 28 TP53 variants, with `##` and `#` header lines as in the real file; two thirds dated 2017-03-01, one third 2022-03-01 | header detection, date parsing, labels rebuilt before a cut-off date |
| `mavedb/toy_tp53/scores.csv` | 29 rows in the MaveDB `variants/data` layout, scores drawn from N(1.0, 0.6) for the pathogenic set and N(-0.5, 0.6) for the benign set, plus p.Arg200His | protein-level join, AUC, cross-fitted thresholds, OddsPath, calibration |
| `mavedb/toy_pten_one_class/scores.csv` | 6 clean PTEN missense rows and 6 rows that must be dropped or merged: missing score, truncated HGVS (`p.Leu61`), a multi-variant allele, a nonsense change, a change on another protein, and a duplicate of p.Leu50Pro | malformed HGVS, missing scores, duplicate averaging, one-class handling through the whole workflow |

Hand-computed cases (two-by-two tables, tied scores, empty input) are written inline in the tests
that use them, so the expected answer sits next to the arithmetic.

Regenerate with `python tests/data/make_fixtures.py` from the repository root.
