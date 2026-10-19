import sys
from pathlib import Path

sys.path.insert(0, str(Path(snakemake.scriptdir).resolve().parents[1] / "src"))

from mavecal.logs import setup_logging

log = setup_logging(snakemake.log[0])

from mavecal import pipeline
from mavecal.analysis import Settings

row = dict(snakemake.params.row)
st = snakemake.params.stats
settings = Settings(
    direction=row["direction"],
    n_boot=int(st["n_boot"]),
    seed=int(st["seed"]),
    n_folds=int(st["n_folds"]),
    min_per_class_threshold=int(st["min_per_class_threshold"]),
    small_class=int(st["small_class"]),
    n_primary=int(snakemake.params.n_primary),
)
pipeline.run_evaluate(
    Path(snakemake.input[0]),
    row,
    settings,
    Path(snakemake.output.summary),
    Path(snakemake.output.variants),
    Path(snakemake.output.bins),
)
