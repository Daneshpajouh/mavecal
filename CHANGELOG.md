# Changelog

Versions follow semantic versioning: a major version changes the analysis or the format of the
result tables, a minor version adds score sets or analyses, a patch fixes code without changing
results.

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
