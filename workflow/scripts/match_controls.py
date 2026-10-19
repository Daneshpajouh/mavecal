import sys
from pathlib import Path

sys.path.insert(0, str(Path(snakemake.scriptdir).resolve().parents[1] / "src"))

from mavecal.logs import setup_logging

log = setup_logging(snakemake.log[0])

from mavecal import pipeline

subs = snakemake.input.submissions
pipeline.match(
    scores=Path(snakemake.input.scores),
    variants=Path(snakemake.input.variants),
    row=dict(snakemake.params.row),
    analysis=dict(snakemake.params.analysis),
    submissions=Path(subs[0]) if len(subs) else None,
    out_table=Path(snakemake.output.table),
    out_stats=Path(snakemake.output.stats),
)
