"""Figures: per score set panels and a cross-analysis forest plot."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.figure import Figure

PATH_COLOUR = "#b2182b"
BEN_COLOUR = "#2166ac"
ANALYSIS_LABELS = {
    "main": "main: 2026-10, 2+ stars",
    "s1_one_star": "S1: 2026-10, 1+ star",
    "s2_release_2025_10": "S2: 2025-10, 2+ stars",
    "s3_release_2018_01": "S3: 2018-01, 1+ star",
    "s4_before_publication": "S4: submissions before publication",
}


def roc_points(oriented: np.ndarray, y: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    order = np.argsort(-oriented, kind="mergesort")
    ys = y[order]
    tpr = np.r_[0.0, np.cumsum(ys) / max(ys.sum(), 1)]
    fpr = np.r_[0.0, np.cumsum(1 - ys) / max((1 - ys).sum(), 1)]
    return fpr, tpr


def _save(fig: Figure, out_png: Path, out_svg: Path) -> None:
    fig.savefig(out_png, dpi=150, bbox_inches="tight")
    fig.savefig(out_svg, bbox_inches="tight")
    plt.close(fig)


def scoreset_figure(
    variants: Path, summary: Path, bins: Path, title: str, direction: str, out_png: Path, out_svg: Path
) -> None:
    df = pd.read_csv(variants, sep="\t")
    s = json.loads(summary.read_text())
    fig, axes = plt.subplots(1, 3, figsize=(13, 4))
    y = (df["label"] == "P").to_numpy(int)
    sign = 1.0 if direction == "higher_is_abnormal" else -1.0
    ax = axes[0]
    if s.get("status") == "ok":
        fpr, tpr = roc_points(sign * df["score"].to_numpy(float), y)
        ax.plot(fpr, tpr, color="black", lw=1.5)
        ax.set_title(f"ROC, AUC {s['auc']:.3f} (95% CI {s['auc_lo']:.3f} to {s['auc_hi']:.3f})", fontsize=9)
    ax.plot([0, 1], [0, 1], ls=":", color="grey")
    ax.set_xlabel("1 - specificity (benign called abnormal)")
    ax.set_ylabel("sensitivity (pathogenic called abnormal)")

    ax = axes[1]
    bins_edges = np.histogram_bin_edges(df["score"], bins=30)
    ax.hist(
        df.loc[df.label == "B", "score"],
        bins=bins_edges,
        alpha=0.6,
        color=BEN_COLOUR,
        label=f"benign (n={s['n_benign']})",
    )
    ax.hist(
        df.loc[df.label == "P", "score"],
        bins=bins_edges,
        alpha=0.6,
        color=PATH_COLOUR,
        label=f"pathogenic (n={s['n_pathogenic']})",
    )
    if "t1_threshold_all_data" in s:
        ax.axvline(float(s["t1_threshold_all_data"]), color="black", ls="--", lw=1, label="Youden threshold, all data")
    ax.set_xlabel("assay score (as deposited)")
    ax.set_ylabel("controls")
    ax.legend(fontsize=7)
    ax.set_title("Score distributions of ClinVar controls", fontsize=9)

    ax = axes[2]
    if bins.stat().st_size > 1:
        b = pd.read_csv(bins, sep="\t")
        if len(b):
            ax.errorbar(
                b["mean_predicted"],
                b["observed"],
                # Wilson bounds can sit a rounding error inside an observed 0 or 1.
                yerr=[(b["observed"] - b["obs_lo"]).clip(lower=0), (b["obs_hi"] - b["observed"]).clip(lower=0)],
                fmt="o",
                color="black",
                ms=4,
            )
    ax.plot([0, 1], [0, 1], ls=":", color="grey")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_xlabel("out-of-fold predicted P(pathogenic label)")
    ax.set_ylabel("observed fraction pathogenic")
    brier = s.get("brier")
    ax.set_title("Reliability" + (f", Brier {brier:.3f}" if brier is not None else ""), fontsize=9)
    fig.suptitle(title, fontsize=11)
    fig.tight_layout()
    _save(fig, out_png, out_svg)


def forest_figure(summary_tsv: Path, out_png: Path, out_svg: Path) -> None:
    df = pd.read_csv(summary_tsv, sep="\t")
    df = df[df["status"] == "ok"].copy()
    order = list(ANALYSIS_LABELS)
    df["analysis_rank"] = df["analysis"].map({a: i for i, a in enumerate(order)})
    df = df.sort_values(["scoreset", "analysis_rank"], ascending=[True, False])
    fig, ax = plt.subplots(figsize=(8, 0.28 * len(df) + 1.5))
    ypos = np.arange(len(df))
    is_main = (df["analysis"] == "main").to_numpy()
    for mask, colour in ((is_main, "black"), (~is_main, "grey")):
        sub = df[mask]
        ax.errorbar(
            sub["auc"],
            ypos[mask],
            xerr=[sub["auc"] - sub["auc_lo"], sub["auc_hi"] - sub["auc"]],
            fmt="o",
            ms=3.5,
            color=colour,
            elinewidth=1.2,
        )
    labels = [
        f"{r['scoreset']}  {ANALYSIS_LABELS.get(str(r['analysis']), str(r['analysis']))}"
        f"  (P={r['n_pathogenic']}, B={r['n_benign']})"
        for r in df.to_dict("records")
    ]
    ax.set_yticks(ypos, labels, fontsize=7)
    ax.axvline(0.5, ls=":", color="grey")
    ax.set_xlabel("ROC AUC with 95% bootstrap interval")
    ax.set_xlim(min(0.4, float(df["auc_lo"].min()) - 0.02), 1.0)
    fig.tight_layout()
    _save(fig, out_png, out_svg)
