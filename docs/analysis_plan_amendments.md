# Amendments to the analysis plan

The plan in `analysis_plan.md` was committed on 2026-10-19 at 11:19 PT (commit 61bc081), before the first workflow run, and its SHA-256 is recorded in `analysis_plan.md.sha256`. The plan text is not edited after registration; clarifications are recorded here with their date and their effect on results.

## 1. P1 in OddsPath (2026-10-19)

The plan defines P1 as the proportion pathogenic among all controls with a readout. The code (`src/mavecal/oddspath.py`) has counted every control in P1 since v1.0.0, indeterminate readouts included. This amendment records the code's definition as the one used: P1 is the proportion pathogenic among all controls, indeterminate readouts included. It matters only for the score set with an indeterminate class (T2); no published number changes, because the code was not changed.

## 2. The added misclassified control (2026-10-19)

The plan says one misclassified control is added to each readout set, as Brnich et al. (2019) did to avoid zero and infinite odds. That description has not yet been checked against the paper's text; until it is, read it as the method the code implements (`src/mavecal/oddspath.py`), not as a quotation of the paper.
