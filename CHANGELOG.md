# Changelog

Versions follow semantic versioning: a major version changes the analysis or the format of the
result tables, a minor version adds score sets or analyses, a patch fixes code without changing
results.

## Unreleased

Leaving out start-loss controls changes the control sets, so under the rule above this is a
major version. The tables, figures and report numbers are still those of 1.0.0 and need a rerun.

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
