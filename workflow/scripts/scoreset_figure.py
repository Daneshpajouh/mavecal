import sys
from pathlib import Path

sys.path.insert(0, str(Path(snakemake.scriptdir).resolve().parents[1] / "src"))

from mavecal.logs import setup_logging

log = setup_logging(snakemake.log[0])

from mavecal import plots

row = dict(snakemake.params.row)
plots.scoreset_figure(
    Path(snakemake.input.variants),
    Path(snakemake.input.summary),
    Path(snakemake.input.bins),
    f"{row['gene']}: {row['assay']} ({row['urn']}), ClinVar 2026-10, 2+ stars, missense",
    row["direction"],
    Path(snakemake.output.png),
    Path(snakemake.output.svg),
)
