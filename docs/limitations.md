# Limitations

- Score-to-label agreement is all this measures. ClinGen also requires the disease mechanism to
  be defined and the assay's validity for that mechanism to be judged (Brnich et al. 2019,
  steps 1 to 3). Neither is done here, and no output is fit for classifying a patient's variant.
- Benign controls are few. PTEN has 3 (phosphatase) and 5 (abundance) at 2 stars, so its
  OddsPath is not estimated or not quoted; BRCA1 HDR has 16 and BRCA1 SGE 22.
- Circularity is checked, not removed. The 2018-01 labels predate the assay papers but not
  preprints or data shared with expert panels before publication, and they differ from current
  labels in size and review level. The submission-date rebuild uses `DateLastEvaluated`, which
  moves forward whenever a lab re-evaluates, so it drops old submissions that were re-reviewed.
- Protein-level joins assume every SNV that encodes a change has the assay's effect. A missense
  SNV that is pathogenic through splicing counts against a protein-level assay.
- T1 is a single cut, so assays with an intermediate class lose that information there; T2 keeps
  it only for the four assays with published classes.
- OddsPath intervals hold the threshold fixed; threshold-selection variance is not included.
- Missense only. Nonsense and splice variants, where SGE is strongest, are not scored.
- One run, one random seed. The fold split varies the T1 thresholds by up to 0.29 score units
  for MSH2 (fold thresholds -0.774 to -0.484); results with other seeds were not computed.
- ClinVar access used NCBI's FTP service because the HTTPS mirror's robots.txt disallows
  automated clients; see data_sources.md.
- `workflow/envs/analysis.yaml` pins the same versions as `pyproject.toml` for `--use-conda`, but
  it was not solved with conda for this release. The tested environments are the Python 3.13
  virtual environment on macOS and the Docker image (Linux, Python 3.13.16).
