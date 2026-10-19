# mave-clinvar-calibration

How well do six published multiplexed assays of variant effect separate disease-causing from
harmless missense variants in BRCA1, TP53, PTEN and MSH2, and how much clinical evidence would
their readouts be worth under ClinGen's OddsPath method? This repository answers that with
public data, a Snakemake workflow and an analysis plan committed before the first result. It is research software;
nothing here classifies a patient's variant.

## The question in plain terms

Genetic testing finds many variants that change one amino acid. For most of them nobody knows
whether they cause disease; the lab reports them as variants of uncertain significance (VUS).
A multiplexed assay of variant effect (MAVE) measures, in cells, what thousands of such
variants do to a protein's function. If an assay's "broken" and "working" calls agree with
variants whose effect is already known, its calls can count as evidence for the unknown ones.

An assay score measures function in a lab system. It is not a probability of disease, and a
good match to known variants does not show that the assay models the disease mechanism. ClinGen
asks for that judgement separately (Brnich et al. 2019); this repository does not make it.

The known variants come from ClinVar, which collects classifications from clinical labs and
expert panels. One trap: some of those classifications already used the same assay data, which
makes the assay look better than it is. Two of the four sensitivity analyses address this.

## What was found

ClinVar release 2026-10, missense variants with 2 or more review stars. P and B are the numbers
of pathogenic and benign controls. OddsPath and evidence strength come from cross-fitted
thresholds; the strength quoted is the one the conservative end of the 95% interval supports.

| score set | P | B | ROC AUC (95% CI) | abnormal readout | normal readout |
|---|---|---|---|---|---|
| BRCA1 saturation genome editing | 151 | 22 | 0.983 (0.952 to 1.000) | PS3_moderate | BS3 |
| BRCA1 HDR reporter | 31 | 16 | 0.861 (0.736 to 0.968) | PS3_supporting | BS3_supporting |
| TP53 nutlin-3 growth | 202 | 74 | 0.960 (0.935 to 0.982) | PS3_moderate | BS3_moderate |
| PTEN lipid phosphatase | 142 | 3 | 0.965 (3 benign, no interval) | not estimated | not estimated |
| PTEN abundance (VAMP-seq) | 108 | 5 | 0.819 (5 benign, no interval) | not quoted, 5 benign | not quoted, 5 benign |
| MSH2 6-thioguanine resistance | 112 | 54 | 0.924 (0.871 to 0.967) | PS3_moderate | BS3_moderate |

- BRCA1 SGE, TP53 and MSH2 support moderate evidence or better for both readouts, BRCA1 HDR
  supporting-level evidence. PTEN cannot be calibrated from ClinVar: there are only 3 and 5
  benign missense controls.
- Against the ClinVar release of January 2018, which predates all six assay papers, the point
  AUC is lower for every score set that can still be scored, but every 2018 interval overlaps
  the main one: BRCA1 SGE 0.983 to 0.946 (0.87 to 1.00), BRCA1 HDR 0.861 to 0.735 (0.45 to
  1.00, which includes 0.5), TP53 0.960 to 0.912 (0.78 to 0.99), MSH2 0.924 to 0.807 (0.69 to
  0.91). Rebuilding labels from submissions made before each paper (S4) shows no drop for BRCA1
  SGE (0.985) and a drop for MSH2 (0.839, 8 benign controls). Neither check separates
  circularity from the smaller, older label sets, which also include 1-star records.

The full results, with intervals, are in [docs/report.md](docs/report.md).

## Running it

Python 3.12 or later. The workflow reads four ClinVar files from three monthly releases (1.25 GB) and downloads
six MaveDB score sets (8 MB) through the MaveDB API.

```console
$ python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"
$ make test           # 63 tests on synthetic data, about 30 s
$ make rule-tests     # 8 Snakemake rule tests
```

For the real analysis, put the ClinVar files listed in [docs/data_sources.md](docs/data_sources.md)
under `<data_dir>/clinvar_releases/` and point the workflow at that directory:

```console
$ export MAVECAL_DATA_DIR=/path/to/data
$ .venv/bin/snakemake --profile profiles/local
...
79 of 79 steps (100%) done
$ .venv/bin/snakemake --report results/snakemake_report.html
```

`data_dir` can also be set with `--config data_dir=/path`, or `data` in the repository root can be
a symlink to it. On a Slurm cluster use
`--profile profiles/slurm` after setting the account and partition in that file. The
container image passed the tests and the offline workflow run (docs/testing.md); the real
analysis was run in the virtual environment, not in the container. To run it there:

```console
$ docker build -t mave-clinvar-calibration:1.0.0 .
$ docker run --rm -e MAVECAL_DATA_DIR=/data -v /path/to/data:/data \
    -v "$PWD/results:/opt/mave-clinvar-calibration/results" mave-clinvar-calibration:1.0.0
```

## Layout

```
config/          config.yaml, scoresets.tsv (validated by workflow/schemas)
workflow/        Snakefile, rules/, scripts/, envs/, schemas/, report/ captions
profiles/        local and slurm Snakemake profiles
src/mavecal/     the statistics, ClinVar and MaveDB parsing, and plotting
tests/           pytest suite and synthetic test data
.tests/          Snakemake integration config and generated rule tests
results/         tables, figures, matched controls and run manifests from the 2026-10-19 run
docs/            analysis plan, report, methods, validation, limitations, data sources,
                 testing and logging notes
```

## Documents

- [docs/analysis_plan.md](docs/analysis_plan.md): the plan, committed before any score was
  joined to a label (commit 61bc081).
- [docs/report.md](docs/report.md): results and their context in published MAVE calibrations.
- [docs/slides/slides.html](docs/slides/slides.html): ten slides for a non-specialist audience;
  opens offline, rebuilt by `docs/slides/build_slides.py`.
- [docs/methods.md](docs/methods.md), [docs/validation.md](docs/validation.md),
  [docs/limitations.md](docs/limitations.md), [docs/data_sources.md](docs/data_sources.md),
  [docs/testing.md](docs/testing.md), [docs/logging.md](docs/logging.md).

## Licence and citation

Code: Apache-2.0. MaveDB score sets used here are CC0; ClinVar data are public and carry
NCBI's terms (see docs/data_sources.md). Cite with [CITATION.cff](CITATION.cff).
