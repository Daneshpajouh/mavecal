# Calibrating six MAVE score sets against ClinVar missense labels

Amir Daneshpajouh. Run of 2026-10-19 (Pacific), ClinVar monthly releases 2026-10, 2025-10 and
2018-01, MaveDB score sets downloaded the same day. Research use only.

## Question and design

Multiplexed assays of variant effect (MAVEs) measure the functional effect of thousands of
variants at once, and ClinGen allows such data as evidence for or against pathogenicity (PS3
and BS3) once the assay is calibrated against variants of known effect (Brnich et al. 2019).
Calibration against ClinVar has a known weakness: an expert panel may already have used the
assay to classify the very variants that serve as controls. This report calibrates six score
sets (BRCA1 saturation genome editing and HDR reporter, TP53 growth under nutlin-3, PTEN
phosphatase and abundance, MSH2 6-thioguanine resistance) and measures how far the results move
when the labels cannot have used the assay.

The plan ([analysis_plan.md](analysis_plan.md)) was committed before any score was joined to a
label. Thresholds were cross-fitted, so every control was called by a threshold that did not
see its label. Methods are in [methods.md](methods.md).

The analysis tests agreement between assay scores and ClinVar labels. It does not establish
that an assay models the disease mechanism, nor that its readout is valid for clinical use; in
ClinGen's framework both are separate judgements made before any calibration counts.

## Controls

Missense SNVs with 2 or more stars in release 2026-10 (main analysis). P/B: pathogenic and
benign controls.

| score set | MaveDB URN | P | B |
|---|---|---|---|
| brca1_sge | urn:mavedb:00000097-0-2 | 146 | 22 |
| brca1_hdr | urn:mavedb:00000081-a-2 | 31 | 16 |
| tp53_nutlin | urn:mavedb:00000068-b-1 | 202 | 74 |
| pten_phosphatase | urn:mavedb:00000054-a-1 | 142 | 3 |
| pten_abundance | urn:mavedb:00000013-a-1 | 107 | 5 |
| msh2_lof | urn:mavedb:00000050-a-1 | 112 | 54 |

Benign controls are scarce everywhere except TP53 and MSH2, and PTEN has almost none. The
PTEN numbers below rest on 3 and 5 benign variants and should be read that way.

## Separation

| score set | AUC (95% CI) | Bonferroni-simultaneous CI | Holm-adjusted p (AUC > 0.5) |
|---|---|---|---|
| brca1_sge | 0.983 (0.953 to 1.000) | 0.940 to 1.000 | 6e-13 |
| brca1_hdr | 0.861 (0.736 to 0.968) | 0.691 to 0.995 | 9e-05 |
| tp53_nutlin | 0.960 (0.935 to 0.982) | 0.925 to 0.986 | 3e-31 |
| pten_phosphatase | 0.965 (3 benign, interval not quoted) | not quoted | 0.0007 |
| pten_abundance | 0.824 (5 benign, interval not quoted) | not quoted | 0.006 |
| msh2_lof | 0.924 (0.871 to 0.967) | 0.844 to 0.976 | 3e-18 |

The simultaneous intervals of the four score sets with at least 10 controls per class all
exclude 0.5. No interval is quoted where a class has fewer than 10 controls (PTEN: 3 and 5
benign), the same rule the plan uses for evidence strength (analysis_plan.md item 7): a
percentile bootstrap from 3 to 8 controls says little. The intervals are still computed: they
are in `results/tables/summary.tsv` and drawn in `results/figures/auc_forest.png`.

## OddsPath and evidence strength

Cross-fitted thresholds (T1). Counts are pathogenic/benign controls with that readout. The
strength column is read from the interval bound nearer to 1.

| score set | abnormal P/B | OddsPath abnormal (95% CI) | strength | normal P/B | OddsPath normal (95% CI) | strength |
|---|---|---|---|---|---|---|
| brca1_sge | 145/1 | 11.3 (5.63 to 22.8) | PS3_moderate | 1/21 | 0.0149 (0.00711 to 0.0313) | BS3 |
| brca1_hdr | 24/1 | 6.38 (2.79 to 14.9) | PS3_supporting | 7/15 | 0.283 (0.133 to 0.46) | BS3_supporting |
| tp53_nutlin | 184/5 | 11.3 (6.41 to 33.6) | PS3_moderate | 18/69 | 0.102 (0.0616 to 0.146) | BS3_moderate |
| pten_phosphatase | not estimated (3 benign controls; cross-fitting needs 5) | | | | | |
| pten_abundance | 76/1 | 2.11 (1.03 to 4.56) | not quoted | 31/4 | 0.444 (0.278 to 0.944) | not quoted |
| msh2_lof | 98/1 | 23.8 (11.3 to 50.1) | PS3_moderate | 14/53 | 0.138 (0.0811 to 0.206) | BS3_moderate |

With the authors' published class boundaries (T2) the results are close for BRCA1 SGE (abnormal
11.2, normal 0.0149) and MSH2 (23.6 and 0.147). For PTEN, T2 puts no benign control in the
abnormal class (86/0 phosphatase, 59/0 abundance), so the raw OddsPath is infinite and the
adjusted value (2.41 and 3.28) is set almost entirely by the one added misclassified control.
That is what 3 to 5 benign controls can support, not a property of the assays.

The added misclassified control weighs most on the abnormal side, where 1 to 5 benign controls
were observed. The raw estimates are 21.8 (BRCA1 SGE), 12.4 (BRCA1 HDR),
13.5 (TP53) and 47.3 (MSH2), against 11.3, 6.38, 11.3 and 23.8 after adjustment.

## Calibration

Out-of-fold logistic probabilities (reliability plots in `results/figures/`):

| score set | Brier | calibration intercept | calibration slope |
|---|---|---|---|
| brca1_sge | 0.014 | 0.07 | 0.87 |
| brca1_hdr | 0.158 | 0.17 | 0.75 |
| tp53_nutlin | 0.062 | 0.00 | 0.97 |
| pten_abundance | 0.041 | 0.15 | 0.94 |
| msh2_lof | 0.083 | 0.01 | 0.93 |

Slopes below 1 mean the out-of-fold probabilities are too extreme; BRCA1 HDR (slope 0.75, 47
controls) is the clearest case. These probabilities describe the ClinVar control set, whose
pathogenic fraction (66% to 96% in the five calibrated sets) is far above any clinical prior, so they are not posterior
probabilities of pathogenicity. PTEN phosphatase has no calibration because cross-fitting
needs 5 benign controls.

## Label independence

AUC (95% CI; P/B) by label source. S3 uses the January 2018 release, published before every
assay here (earliest assay paper online 2018-04-26), at 1 or more stars as fixed in the plan. S4 keeps only submissions last evaluated before the assay's publication.

| score set | main | S1 one star | S2 2025-10 | S3 2018-01 | S4 before publication |
|---|---|---|---|---|---|
| brca1_sge | 0.983 (0.95 to 1.00; 146/22) | 0.994 (0.98 to 1.00; 201/111) | 0.980 (0.94 to 1.00; 127/19) | 0.944 (0.86 to 1.00; 38/14) | 0.984 (0.95 to 1.00; 39/16) |
| brca1_hdr | 0.861 (0.74 to 0.97; 31/16) | 0.879 (0.78 to 0.97; 39/34) | 0.846 (0.69 to 0.96; 26/16) | 0.735 (0.45 to 1.00; 11/12) | 0.818 (interval not quoted; 11/6) |
| tp53_nutlin | 0.960 (0.94 to 0.98; 202/74) | 0.935 (0.91 to 0.96; 224/149) | 0.962 (0.93 to 0.98; 175/71) | 0.912 (0.78 to 0.99; 108/11) | 1.000 (interval not quoted; 12/3) |
| pten_phosphatase | 0.965 (interval not quoted; 142/3) | 0.946 (interval not quoted; 197/5) | 0.971 (interval not quoted; 116/3) | no benign (69/0) | no benign (5/0) |
| pten_abundance | 0.824 (interval not quoted; 107/5) | 0.703 (interval not quoted; 150/8) | 0.826 (interval not quoted; 85/5) | no benign (50/0) | no benign (2/0) |
| msh2_lof | 0.924 (0.87 to 0.97; 112/54) | 0.943 (0.91 to 0.97; 139/287) | 0.913 (0.85 to 0.96; 100/50) | 0.807 (0.69 to 0.91; 58/20) | 0.839 (interval not quoted; 49/8) |

Cells read AUC (95% interval; pathogenic/benign). No interval is quoted where a class has fewer
than 10 controls; the computed intervals are in `results/tables/summary.tsv` and the AUC figure.

Every score set that can be scored on 2018 labels has a lower point AUC on them, though each
2018 interval overlaps the main one. The conservative evidence strength drops for three of the
four: BRCA1 SGE abnormal from PS3_moderate to PS3_supporting and normal from BS3 to
BS3_moderate; TP53 abnormal from PS3_moderate to indeterminate and normal from BS3_moderate
to BS3_supporting; MSH2 from moderate to
supporting on both sides. BRCA1 HDR moves both ways: its abnormal side rises from
PS3_supporting to PS3_moderate (11 pathogenic and 12 benign controls) and its normal side drops
from BS3_supporting to indeterminate. The S4 rebuild shows no drop for
BRCA1 SGE (0.984) and a drop for MSH2 (0.839, 8 benign controls); it leaves TP53 with 3 benign
controls and PTEN with none.

S4 was rerun on 2026-10-21 under amendment 4, which counts distinct submitters, not submissions, for
two stars. On these submissions no variant changes its label or its stars at any cutoff, so every
S4 number is unchanged. Cells read AUC (pathogenic/benign).

| score set | S4 before amendment 4 (1d7daf3) | S4 after amendment 4 | variants with two stars at the cutoff (before, after) |
|---|---|---|---|
| brca1_sge | 0.984 (39/16) | 0.984 (39/16) | 2230, 2230 (cutoff 2018-09-12; labels changed: 0) |
| brca1_hdr | 0.818 (11/6) | 0.818 (11/6) | 2230, 2230 (cutoff 2018-09-12; labels changed: 0) |
| tp53_nutlin | 1.000 (12/3) | 1.000 (12/3) | 2232, 2232 (cutoff 2018-09-17; labels changed: 0) |
| pten_phosphatase | no AUC (5/0) | no AUC (5/0) | 2146, 2146 (cutoff 2018-04-26; labels changed: 0) |
| pten_abundance | no AUC (2/0) | no AUC (2/0) | 2162, 2162 (cutoff 2018-05-21; labels changed: 0) |
| msh2_lof | 0.839 (49/8) | 0.839 (49/8) | 2781, 2781 (cutoff 2020-12-23; labels changed: 0) |

Two explanations fit and this design cannot separate them. Some current labels may rest on the
assays (ClinGen expert panels for these genes use functional data), which inflates the main
analysis. The 2018 label sets are also smaller, older and include 1-star records, which adds
noise of its own. A one-year shift in release (S2) moves no AUC by more than 0.015.

## Published calibrations of the same assays

MaveDB records OddsPath values from earlier calibrations for some of these score sets. The values
below are as each record's calibrations page shows them, rounded to two decimals there, read on
2026-10-19: [BRCA1 SGE](https://www.mavedb.org/score-sets/urn:mavedb:00000097-0-2/calibrations)
and [MSH2](https://www.mavedb.org/score-sets/urn:mavedb:00000050-a-1/calibrations). For BRCA1 SGE
with the same class boundaries, the IGVF Coding Variant Focus Group calibration with missense
controls only records OddsPath 74.59 (abnormal) and 0.02 (normal), and Fayer et al. (2021)
record 52.40 and 0.02. For MSH2, the IGVF missense calibration records 71.11 and 0.05, and Scott
et al. (2022) 24.90 and 0.04 (with an abnormal class from 0.40 up, not from 0). All four record
PS3 strong on the abnormal side and BS3 strong on the normal side. The
raw T2 estimates here are 21.5 and 0.0072 (BRCA1 SGE) and 46.8 and 0.136 (MSH2). On the normal side the
strength agrees for BRCA1 SGE (BS3) but not for MSH2 (moderate here, strong in both earlier
calibrations). The abnormal-side estimates here are lower because the control set
holds 1 benign variant called abnormal among few benign controls, and the adjustment for a
misclassified control is applied on top. The published calibrations used different control
sets and dates, which this report did not reconstruct. Zeiberg et al. (2025, preprint) fit
gene-level calibrations for many MaveDB score sets, also recorded on MaveDB as ExCALIBR; their
thresholds are not compared here because their method differs from Brnich's two-class OddsPath.

## Limitations

The main ones: few benign controls (PTEN unusable, BRCA1 HDR and BRCA1 SGE thin), the
circularity analysis is confounded by changes in label quality, one-sided thresholds ignore
intermediate scores in T1, and the bootstrap holds thresholds fixed. The full list is in
[limitations.md](limitations.md).

## References

- Brnich SE et al. Genome Med 2019;12:3. doi:10.1186/s13073-019-0690-2
- Richards S et al. Genet Med 2015;17:405-424. doi:10.1038/gim.2015.30
- Tavtigian SV et al. Genet Med 2018;20:1054-1060. doi:10.1038/gim.2017.210
- Pejaver V et al. Am J Hum Genet 2022;109:2163-2177. doi:10.1016/j.ajhg.2022.10.013
- Landrum MJ et al. Nucleic Acids Res 2018;46:D1062-D1067. doi:10.1093/nar/gkx1153
- Esposito D et al. Genome Biol 2019;20:223. doi:10.1186/s13059-019-1845-6
- Fayer S et al. Am J Hum Genet 2021. doi:10.1016/j.ajhg.2021.11.001
- Scott A et al. Genome Biol 2022. doi:10.1186/s13059-022-02839-z
- Zeiberg D et al. bioRxiv 2025. doi:10.1101/2025.04.29.651326
- Findlay GM et al. Nature 2018;562:217-222. doi:10.1038/s41586-018-0461-z
- Starita LM et al. Am J Hum Genet 2018;103:498-508. doi:10.1016/j.ajhg.2018.07.016
- Giacomelli AO et al. Nat Genet 2018;50:1381-1387. doi:10.1038/s41588-018-0204-y
- Mighell TL et al. Am J Hum Genet 2018;102:943-955. doi:10.1016/j.ajhg.2018.03.018
- Matreyek KA et al. Nat Genet 2018;50:874-882. doi:10.1038/s41588-018-0122-z
- Jia X et al. Am J Hum Genet 2021;108:163-175. doi:10.1016/j.ajhg.2020.12.003

All DOIs above returned a registered handle from the doi.org API on 2026-10-19.
