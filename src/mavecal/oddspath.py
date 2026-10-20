"""OddsPath and the evidence-strength table of Brnich et al. (2019), Table 3."""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class Readouts:
    """Counts of controls by label (P or B) and readout (abnormal, normal, indeterminate)."""

    p_abnormal: int
    b_abnormal: int
    p_normal: int
    b_normal: int
    p_indeterminate: int = 0
    b_indeterminate: int = 0

    @property
    def n_pathogenic(self) -> int:
        return self.p_abnormal + self.p_normal + self.p_indeterminate

    @property
    def n_benign(self) -> int:
        return self.b_abnormal + self.b_normal + self.b_indeterminate

    def with_misclassified_control(self) -> Readouts:
        """Add one benign control to the abnormal set and one pathogenic to the normal set."""
        return Readouts(
            self.p_abnormal,
            self.b_abnormal + 1,
            self.p_normal + 1,
            self.b_normal,
            self.p_indeterminate,
            self.b_indeterminate,
        )


def oddspath(p_in_set: int, b_in_set: int, n_pathogenic: int, n_benign: int) -> float:
    """OddsPath = P2 (1 - P1) / ((1 - P2) P1).

    P1 is the proportion pathogenic among all controls, P2 among controls in the
    readout set. Returns inf when the set holds no benign control and nan when the
    set is empty or a class is absent overall.
    """
    if p_in_set + b_in_set == 0 or n_pathogenic == 0 or n_benign == 0:
        return math.nan
    p1 = n_pathogenic / (n_pathogenic + n_benign)
    p2 = p_in_set / (p_in_set + b_in_set)
    if p2 == 1.0:
        return math.inf
    return (p2 * (1.0 - p1)) / ((1.0 - p2) * p1)


def oddspath_abnormal(r: Readouts) -> float:
    return oddspath(r.p_abnormal, r.b_abnormal, r.n_pathogenic, r.n_benign)


def oddspath_normal(r: Readouts) -> float:
    return oddspath(r.p_normal, r.b_normal, r.n_pathogenic, r.n_benign)


def evidence_strength(odds: float) -> str:
    """Map an OddsPath to the Brnich et al. (2019) Table 3 evidence level."""
    if math.isnan(odds):
        return "not_estimated"
    if odds > 350:
        return "PS3_very_strong"
    if odds > 18.7:
        return "PS3"
    if odds > 4.3:
        return "PS3_moderate"
    if odds > 2.1:
        return "PS3_supporting"
    if odds < 0.053:
        return "BS3"
    if odds < 0.23:
        return "BS3_moderate"
    if odds < 0.48:
        return "BS3_supporting"
    return "indeterminate"


def readout_strength(odds: float, readout: str) -> str:
    """Table 3 level for one readout: PS3 levels for 'abnormal', BS3 levels for 'normal'.

    An OddsPath on the wrong side of 1 for its readout, for example an abnormal set that
    holds only the added benign control, is indeterminate, not evidence the other way.
    """
    level = evidence_strength(odds)
    wrong = {"abnormal": "BS3", "normal": "PS3"}[readout]
    return "indeterminate" if level.startswith(wrong) else level
