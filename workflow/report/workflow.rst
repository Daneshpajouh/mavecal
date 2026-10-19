Calibration of six MaveDB score sets (BRCA1, TP53, PTEN, MSH2) against ClinVar missense labels.
Scores are joined to ClinVar GRCh38 single nucleotide variants, then evaluated by ROC AUC with
stratified bootstrap intervals, cross-fitted Youden thresholds, OddsPath (Brnich et al. 2019)
and out-of-fold logistic calibration. The analysis plan in docs/analysis_plan.md was committed
before any score was joined to a label. Research use only.
