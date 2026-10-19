import sys
from pathlib import Path

sys.path.insert(0, str(Path(snakemake.scriptdir).resolve().parents[1] / "src"))

from mavecal.logs import setup_logging

log = setup_logging(snakemake.log[0])

from mavecal import pipeline

pipeline.filter_clinvar(Path(snakemake.input[0]), list(snakemake.params.genes), Path(snakemake.output[0]))
