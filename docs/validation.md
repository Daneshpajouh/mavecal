# Validation

## The plan came first

`docs/analysis_plan.md` was committed as 61bc081 at 11:19 Pacific on 2026-10-19, before the
first workflow run (11:27). Its SHA-256 is
`30246cf38de8f2acfcea9dc5ab54dd85f73c6dcf03d48680e71ad055ca7c87b6`; the file has not changed
since, and every run manifest records the hash it saw. Before writing it I had read MaveDB
score set records and method text (to fix directions and published class boundaries) and the
ClinVar column headers, but no join of scores to labels.

Details the plan did not fix, settled during implementation and listed here instead of editing
the plan: the Youden tie rule (highest threshold), the ridge of 0.001 in the calibration fit,
and the PTEN phosphatase normal-class bound (0.89 from the method text, where the MaveDB record
reads 89.0; the plan already gave 0.89). No analysis in the plan was dropped or added.

## Checks on the code

- AUC equals scikit-learn's `roc_auc_score` on 500 tied scores to 1e-12, and the bootstrap
  interval covers the binormal AUC Phi(1/sqrt 2) = 0.760 with 400 + 400 draws.
- OddsPath reproduces the worked example in Brnich et al. (2019): 5 pathogenic and 6 benign
  controls, one benign indeterminate, gives 35/6 = 5.83, PS3_moderate, as the paper states.
- Every boundary of the Table 3 mapping is tested on both sides.
- The 63 pytest tests and 8 rule tests are described in [testing.md](testing.md).

## Checks on the data and joins

- ClinVar files: `gzip -t` and server length match (see data_sources.md).
- Joins (`results/tables/matching.tsv`): all six score sets mapped to the expected RefSeq
  protein or to GRCh38; no protein change had discordant ClinVar SNVs in any analysis; the 1,039
  BRCA1 SGE rows without a genomic mapping matched no missense control.
- Matching counts were identical in the runs of 11:41 and 11:58 Pacific, and the summary table
  had the same SHA-256 (`c327f52a...`) after the 12:06 aggregation and after two full reruns at
  12:08 and 12:09 that re-downloaded every MaveDB score set.

## Against published calibrations

The OddsPath estimates are compared with calibrations recorded on MaveDB (IGVF Coding Variant
Focus Group, Fayer et al. 2021, Scott et al. 2022) in [report.md](report.md). Normal-side
strength agrees for BRCA1 SGE and is one level lower here for MSH2; abnormal-side estimates are
lower here, mainly because of the added misclassified control and the small benign sets.
