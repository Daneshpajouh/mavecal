# Amendments to the analysis plan

The plan in `analysis_plan.md` was committed on 2026-10-19 at 11:19 PT (commit 61bc081), before the first workflow run, and its SHA-256 is recorded in `analysis_plan.md.sha256`. The plan text is not edited after registration; clarifications are recorded here with their date and their effect on results.

## 1. P1 in OddsPath (2026-10-19)

The plan defines P1 as the proportion pathogenic among all controls with a readout. The code (`src/mavecal/oddspath.py`) has counted every control in P1 since v1.0.0, indeterminate readouts included. This amendment records the code's definition as the one used: P1 is the proportion pathogenic among all controls, indeterminate readouts included. It matters only for the score set with an indeterminate class (T2); no published number changes, because the code was not changed.

## 2. The added misclassified control (2026-10-19)

The plan says one misclassified control is added to each readout set, as Brnich et al. (2019) did to avoid zero and infinite odds. Checked against the paper on 2026-10-19 (full text through Europe PMC, PMC6938631, CC BY 4.0): its Methods say "To circumvent posterior probabilities of zero or infinity, and to account for the possibility that the next variant tested in the assay might have a discordant result, we added exactly one misclassified variant to each set", where the sets are the groups with abnormal and with normal readouts. The paper did this for modelled control sets; this analysis does it for the observed ones, as `src/mavecal/oddspath.py` implements.

## 3. Number of reliability bins (2026-10-19)

Plan item 6 asks for a reliability plot with 10 quantile bins. Since the package was first committed (58bbb7d) the code (`reliability_bins` in `src/mavecal/calibration.py`) has used 10 bins only when a control set has at least 100 controls, and otherwise one bin per 10 controls, with at least 2. This amendment records the code's rule as the one used. For the main analysis that means 4 bins for BRCA1 HDR (47 controls), 10 for BRCA1 SGE, TP53, MSH2 and PTEN abundance, and none for PTEN phosphatase, which is not cross-fitted. No published number changes, because the code was not changed.
