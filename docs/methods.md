# Methods

The choices below were fixed in [analysis_plan.md](analysis_plan.md) before any assay score was
joined to a ClinVar label. Where the code had to settle a detail the plan left open, it is
marked "implementation detail".

## Data

MaveDB score sets were downloaded with `GET /api/v1/score-sets/{urn}/variants/data` and the
`scores` and `mavedb` namespaces, which add MaveDB's post-mapped HGVS on the RefSeq protein
(`NP_...:p.`) and on GRCh38 (`NC_...:g.`). ClinVar `variant_summary` releases were filtered to
GRCh38 rows of type "single nucleotide variant" in BRCA1, TP53, PTEN and MSH2. The 2018-01
release has no VariationID or VCF-style columns; there the AlleleID stands in for the ID and
`Start`, `ReferenceAllele` and `AlternateAllele` give the allele, which is exact for SNVs.

## Labels and matching

Pathogenic means a `ClinicalSignificance` of Pathogenic, Likely pathogenic or
Pathogenic/Likely pathogenic, benign the three benign equivalents; anything with an extra term
(for example "; risk factor") is excluded. Stars follow ClinVar's review-status table. Only
missense changes on the gene's reference transcript count, read from the protein change in the
`Name` column. Changes at the initiator Met1 are left out: they remove the start codon rather
than substitute one residue in the protein the assay measures.

Protein-level score sets are joined on the protein change. When several SNVs encode the same
amino acid change, the change is pathogenic if at least one eligible SNV is pathogenic and none
is benign, and the reverse; changes with both are dropped (none occurred in the real data).
Rows of a score set that map to the same change are averaged. The BRCA1 SGE score set is joined
on the GRCh38 allele; its 1,039 rows without a post-mapped genomic HGVS fall back to the transcript c.
HGVS, and none of them matched a missense control. Implementation detail: score rows that
carry the same allele are averaged, as for protein changes.

Labels for S4 come from `submission_summary`: submissions with assertion criteria whose
`DateLastEvaluated` is before the assay's first online date. A variant keeps a label only if
all such submissions agree; uncertain significance among them removes it.
Two stars need two or more distinct submitters among them, not two submissions from one
submitter (amendment 4).

## Statistics

Scores are oriented by each assay's documented direction, never by the data, so an AUC below
0.5 would mean the assay disagrees with ClinVar.

- AUC is the Mann-Whitney statistic with ties counted as one half. Intervals are percentile
  intervals from 2,000 stratified bootstrap replicates (seed 20261019). The six main analyses
  also get Bonferroni-simultaneous intervals (level 1 - 0.05/6) and one-sided Mann-Whitney
  p-values, Holm adjusted.
- T1 thresholds: five stratified folds. Each fold is called with the Youden-optimal threshold of
  the other four, so no control is called by a threshold fit on its own label. Implementation
  detail: candidates are midpoints between adjacent distinct scores, and among tied maxima the
  highest threshold is kept, which calls the fewest variants abnormal.
- T2 thresholds: the class boundaries the assay authors published, as recorded on MaveDB. The
  MaveDB record for PTEN phosphatase gives the upper bound of the wild-type-like class as 89.0;
  the record's method text gives 0.89, which is used here.
- OddsPath follows Brnich et al. (2019): P1 is the pathogenic fraction of all controls, indeterminate
  readouts included, P2 the pathogenic fraction among abnormal (or normal) readouts, and
  OddsPath = P2(1 - P1) / ((1 - P2) P1). One misclassified control is added to each readout set
  before the estimate, as Brnich et al. (2019) did: "To circumvent posterior probabilities of
  zero or infinity, and to account for the possibility that the next variant tested in the assay
  might have a discordant result, we added exactly one misclassified variant to each set"
  (Methods; the sets are the groups with abnormal and with normal readouts; Genome Medicine 12:3,
  doi:10.1186/s13073-019-0690-2, CC BY 4.0, full text read through Europe PMC, PMC6938631, on
  2026-10-19). The paper applied it to modelled control sets; here it is applied to the observed
  ones. With 1 benign control in an abnormal set this halves the estimate, so the raw value is in
  the tables too.
  Intervals resample the readouts (2,000 replicates) with the thresholds held fixed.
- Evidence strength uses Brnich et al. Table 3. The quoted strength comes from the interval
  bound nearer to 1. No strength is quoted when either class has fewer than 10 controls.
- Calibration: logistic regression of the label on the standardised oriented score, fit on four
  folds and applied to the fifth. Out-of-fold probabilities give the Brier score, a logistic
  recalibration intercept and slope, and reliability bins (quantile bins, Wilson intervals). Implementation detail: 10 bins when there
  are at least 100 controls, otherwise one bin per 10 controls and at least 2 (amendment 3).
  Implementation detail: a ridge of 0.001 on the slope keeps the fit finite when the training
  folds separate perfectly.
