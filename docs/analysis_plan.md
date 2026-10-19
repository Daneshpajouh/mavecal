# Analysis plan

Written and committed on 2026-10-19 before any assay score was joined to a ClinVar label.
Changes after this commit are listed at the end of this file with a date and a reason.

## Question

For six published multiplexed assays of variant effect (MAVE) in four genes, how well do the
assay scores separate ClinVar pathogenic from benign missense variants, and what strength of
functional evidence (ACMG/AMP criteria PS3 and BS3) would the assay's abnormal and normal
readouts support under the OddsPath method of Brnich et al. (2019)?

This is research software. Nothing here is a clinical classification.

## Score sets

All six are on MaveDB with a CC0 licence (checked on each score set record on 2026-10-19).
The direction column is taken from each score set's method text, not from the data.

| id | MaveDB URN | gene | assay | publication (first online) | abnormal readout |
|---|---|---|---|---|---|
| brca1_sge | urn:mavedb:00000097-0-2 | BRCA1 | saturation genome editing, HAP1 fitness | Findlay 2018, 2018-09-12 | lower score |
| brca1_hdr | urn:mavedb:00000081-a-2 | BRCA1 | homology-directed repair reporter | Starita 2018, 2018-09-12 | lower score |
| tp53_nutlin | urn:mavedb:00000068-b-1 | TP53 | A549 p53-null cells under nutlin-3 | Giacomelli 2018, 2018-09-17 | higher score |
| pten_phosphatase | urn:mavedb:00000054-a-1 | PTEN | yeast lipid phosphatase growth | Mighell 2018, 2018-04-26 | lower score |
| pten_abundance | urn:mavedb:00000013-a-1 | PTEN | VAMP-seq protein abundance | Matreyek 2018, 2018-05-21 | lower score |
| msh2_lof | urn:mavedb:00000050-a-1 | MSH2 | HAP1 6-thioguanine resistance | Jia 2021, 2020-12-23 | higher score |

If a score set cannot be mapped to the reference protein or genome, it is dropped and the
reason is recorded in docs/limitations.md.

## Reference labels

- Main release: ClinVar monthly archive `variant_summary_2026-10.txt.gz`, GRCh38 rows,
  `Type == "single nucleotide variant"`, `GeneSymbol` equal to the score set's gene.
- Pathogenic: `ClinicalSignificance` exactly one of Pathogenic, Likely pathogenic,
  Pathogenic/Likely pathogenic. Benign: Benign, Likely benign, Benign/Likely benign.
  Everything else (uncertain, conflicting, combinations with risk factor) is excluded.
- Review stars from `ReviewStatus`: practice guideline 4; reviewed by expert panel 3;
  criteria provided, multiple submitters, no conflicts 2; criteria provided, single submitter 1;
  criteria provided, conflicting classifications (or interpretations) 1; anything else 0.
- Main analysis: 2 or more stars. Missense variants only, identified from the protein change
  in the ClinVar `Name` field on the gene's reference transcript (BRCA1 NM_007294, TP53
  NM_000546, PTEN NM_000314, MSH2 NM_000251; accession version ignored). Missense only so that
  assays are compared on the same variant class and nonsense variants do not inflate the AUC.

## Matching

- Protein-level score sets (all except brca1_sge): MaveDB post-mapped protein HGVS on the
  RefSeq protein, joined to the ClinVar protein change. Several SNVs can encode the same
  amino acid change, so the unit is the protein change. It is labelled pathogenic if at least
  one eligible ClinVar SNV is pathogenic and none is benign at the star threshold, and the
  reverse for benign. Discordant protein changes are excluded and counted. Duplicate score rows
  for one protein change are averaged.
- brca1_sge is nucleotide level: MaveDB post-mapped GRCh38 genomic HGVS joined on chromosome,
  position, reference and alternate allele. Variants without a post-mapped HGVS are joined on
  the transcript c. HGVS instead; the method used is recorded per variant.

## Metrics

1. ROC AUC (Mann-Whitney form, ties count one half), with scores oriented so that higher
   means more abnormal. A 95% percentile interval from a stratified bootstrap (pathogenic and
   benign resampled separately, 2000 replicates, seed 20261019).
2. Test of AUC = 0.5 against AUC > 0.5 with the one-sided Mann-Whitney U test for each of the
   six main analyses, Holm adjusted across the six. Simultaneous intervals: Bonferroni
   (alpha 0.05/6) bootstrap percentile intervals for the same six AUCs.
3. Thresholds, fixed here before results:
   - T1, cross-fitted Youden threshold (all score sets): five stratified folds (seed 20261019).
     For each fold, the threshold that maximises Youden's J on the other four folds is applied
     to the held-out fold, so every variant's readout comes from a threshold that never saw its
     label. Needs at least 5 pathogenic and 5 benign controls.
   - T2, published assay classes recorded on MaveDB (brca1_sge: abnormal at or below -1.328,
     normal at or above -0.748; pten_phosphatase: abnormal at or below -2.13, normal from -1.11
     to 0.89; pten_abundance: abnormal below 0.56294, normal at or above 0.66565; msh2_lof:
     abnormal above 0, normal below 0). Scores between classes are indeterminate. brca1_hdr and
     tp53_nutlin have no published classes on MaveDB, so T2 is not estimated for them.
4. OddsPath (Brnich et al. 2019): with P1 the proportion pathogenic among all controls with a
   readout and P2 the proportion pathogenic among controls with an abnormal (or normal) readout,
   OddsPath = P2(1 - P1) / ((1 - P2) P1). The reported estimate adds one misclassified control
   to each readout set, the device Brnich et al. used to avoid zero and infinite odds; the raw
   value is reported beside it. Bootstrap 95% interval from 2000 stratified resamples of the
   readouts (threshold held fixed, so the interval ignores threshold-selection variance).
5. Evidence strength from Brnich et al. Table 3: above 350 PS3_very_strong, above 18.7 PS3,
   above 4.3 PS3_moderate, above 2.1 PS3_supporting, 0.48 to 2.1 indeterminate, below 0.48
   BS3_supporting, below 0.23 BS3_moderate, below 0.053 BS3. Two strengths are reported: one
   from the point estimate and one from the interval bound closer to 1 (lower bound for
   abnormal, upper bound for normal). The second is the one this project quotes.
6. Calibration: cross-fitted logistic regression of the label on the oriented score (same
   folds), out-of-fold probabilities in a reliability plot with 10 quantile bins, Brier score,
   calibration intercept and slope. These probabilities are relative to the class balance of
   the ClinVar control set, not to any clinical prior.
7. Any estimate with fewer than 10 pathogenic or fewer than 10 benign controls is flagged as
   small. Its numbers are shown, but no evidence strength is quoted for it.

## Sensitivity analyses (descriptive, no p-values)

- S1: 1 or more stars, main release.
- S2: ClinVar release 2025-10 (one year earlier), 2 or more stars.
- S3: ClinVar release 2018-01, which predates the publication of all six assays, at 1 or more
  stars. Labels in this release cannot rest on the published assay data, though they could rest
  on preprints or data shared before publication.
- S4: labels rebuilt from the submission summary, keeping only submissions whose
  DateLastEvaluated is before the assay's first online publication date. A variant keeps a
  label only if all such submissions with assertion criteria agree; stars are approximated as
  2 for two or more agreeing criteria-provided submissions and 3 if one is an expert panel.

## Circularity

ClinGen expert panels for these genes use functional data, which can include these assays, when
they classify variants. A label that rests on the same assay inflates every metric above. S3 and
S4 are the checks, and the report states how far each metric moves.

## Outputs

Per score set and analysis: counts, AUC with intervals, thresholds, 2x2 tables, OddsPath with
intervals, evidence strengths and calibration statistics (TSV). Figures: ROC curves, score
distributions with thresholds, reliability plots and an AUC forest plot across analyses (PNG
and SVG). A Markdown and HTML report.

## Changes after the first commit

None yet.
