# Changelog

Versions follow semantic versioning: a major version changes the analysis or the format of the
result tables, a minor version adds score sets or analyses, a patch fixes code without changing
results.

## Unreleased

No committed result changes. Checked on the 2026-10-19 downloads: no allele in the BRCA1 SGE
score set has two score rows, and the nucleotide join returns the same variants, scores and
labels as 2.0.0 for the 2018-01, 2025-10 and 2026-10 releases at 0, 1 and 2 stars; no main
analysis table has a repeated score, so the ROC figures are unchanged. The other cases do not
occur in the 2026-10-19 run.

- An abnormal readout is never quoted as BS3 evidence, nor a normal readout as PS3; an OddsPath
  on the wrong side of 1 for its readout is indeterminate.
- The nucleotide join averages score rows that share an allele instead of keeping the first.
- Genomic keys on NC_000023 and NC_000024 use ClinVar's X and Y.
- A header-only score set gives no keys instead of a KeyError.
- Tied out-of-fold probabilities give one reliability bin instead of none.
- ROC curves step diagonally through tied scores, so their area is the reported AUC.
- Plan amendment 3 records the reliability bin rule; validation.md names the plan copy the
  committed run read.
- A tagged release also runs the Snakemake rule tests before it publishes anything.
- The README shows the AUC figure from the committed run and starts the quick start with the
  clone. The tables say "interval not quoted" for classes under 10 controls, since the figure
  and summary.tsv do carry those intervals.
- A cross-fitting test now uses overlapping classes and fails if a fold's threshold is fit on
  all rows or on the fold itself; the old test passed on both.

## 2.0.0 (2026-10-19)

Renamed from mave-clinvar-calibration to mavecal.

Leaving out start-loss controls changes the control sets, so under the rule above this is a
major version. The rerun of 2026-10-19 regenerated the tables, figures and report numbers; only
the BRCA1 SGE and PTEN abundance results changed.

- Start-loss changes at Met1 no longer count as missense (ClinVar and MaveDB keys). In the 1.0.0
  run this removes 5 pathogenic BRCA1 SGE controls and 1 pathogenic PTEN abundance control.
- The logistic fit raises when Newton-Raphson does not converge, and the calibration slope and
  intercept are then reported as missing instead of the last iterate.
- The end-of-run manifest records Snakemake's last progress line (steps done and total).
- Python 3.13 declared throughout (requires-python and ruff target), as tested.
- The Snakemake HTML report (4 MB) is attached to the release instead of kept in git.
- Report and README: BRCA1 HDR strength moves both ways on 2018 labels; 2018 AUCs given with
  intervals beside the S4 rebuild; no interval where a class has fewer than 10 controls; P1
  counts indeterminate readouts; the misclassified-control wording and the MaveDB OddsPath
  values are marked as not yet checked at source.

## 1.0.0 (2026-10-19)

First release.

- Six MaveDB score sets (BRCA1 SGE and HDR, TP53 nutlin-3, PTEN phosphatase and abundance,
  MSH2) calibrated against ClinVar 2026-10 missense labels, with four sensitivity analyses on
  star level, release and label dates.
- Cross-fitted Youden thresholds and published class boundaries, OddsPath with the Brnich et al.
  misclassified-control adjustment, bootstrap intervals, Holm and Bonferroni adjustment,
  out-of-fold logistic calibration.
- Snakemake 9 workflow with schema-validated config, per-rule logs and benchmarks, run
  manifests, local and Slurm profiles, and a container pinned by digest.
- 63 pytest tests and 8 Snakemake rule tests on synthetic data.
- A results report (docs/report.md) and a ten-slide offline deck (docs/slides/slides.html).
