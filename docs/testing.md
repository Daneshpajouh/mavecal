# Testing

Three layers, all on synthetic data in `tests/data/` (described in its README), so none needs
network access or the ClinVar files.

| layer | where | what it checks |
|---|---|---|
| known-answer | `tests/test_stats.py`, `tests/test_oddspath.py` | AUC against hand-worked cases and scikit-learn; Holm against a hand-computed example; Youden thresholds and their tie rule; bootstrap seeding, class sizes and coverage of a binormal AUC; OddsPath formula, the misclassified-control device, the Brnich et al. worked example, every Table 3 boundary; no abnormal readout quoted as BS3 or normal readout as PS3; reliability bins and Wilson intervals |
| edge cases and parsing | `tests/test_edge_cases.py`, `tests/test_clinvar_matching.py` | one class only, empty input, all scores tied, too few controls to cross-fit, small-set rule, malformed and multi-variant HGVS, missing scores, duplicate rows for one protein change or one allele, a header-only score set, X and Y chromosome names, discordant SNVs for one protein change, a 2018-format ClinVar file without VariationID, label rebuilding before a date, errors that name the bad file |
| pipeline and workflow | `tests/test_end_to_end.py`, `tests/test_workflow.py`, `.tests/unit/` | each pipeline step and the figures on fixtures; `snakemake --lint`; a dry run that plans every rule; schema rejection of a bad config; a full offline run of the workflow; one generated Snakemake rule test per rule (8) |

The rule tests were generated with `snakemake --generate-unit-tests` from the offline run and
then edited in three places: the generated command passed `config/config.yaml` after the test
configuration, which overrode it; the test configuration and fixtures are copied into each
temporary workdir; and figures are checked for existence, not byte equality, because PNG and
SVG output differs between runs.

## Results on 2026-10-19

macOS 27 (arm64), Python 3.13.9, 90 tests in 31 s:

```console
$ .venv/bin/python -m pytest -p no:cacheprovider --cov=mavecal --cov-report=term
Name                         Stmts   Miss  Cover
------------------------------------------------
src/mavecal/__init__.py          1      0   100%
src/mavecal/analysis.py         98      0   100%
src/mavecal/calibration.py      72      2    97%
src/mavecal/clinvar.py          98      5    95%
src/mavecal/logs.py             10      0   100%
src/mavecal/manifest.py         59      4    93%
src/mavecal/matching.py         25      0   100%
src/mavecal/mavedb.py           68     14    79%
src/mavecal/oddspath.py         53      0   100%
src/mavecal/pipeline.py         87     18    79%
src/mavecal/plots.py            82      0   100%
src/mavecal/stats.py            80      1    99%
------------------------------------------------
TOTAL                          733     44    94%
90 passed in 31.42s
$ .venv/bin/python -m pytest .tests/unit -p no:cacheprovider
8 passed
```

The uncovered lines are mostly `mavedb.fetch_score_set` and `pipeline.fetch`, which need the
network and run only in the real workflow.

## In the container

The image from `Dockerfile` (python:3.13-slim pinned by digest), built and run on 2026-10-19:

```console
$ docker build -t mavecal:1.0.0 .
$ docker run --rm --entrypoint sh mavecal:1.0.0 -c \
    'uname -sm; python --version; python -m pytest -q; python -m pytest .tests/unit -q; snakemake --lint'
Linux aarch64
Python 3.13.16
...............................................................          [100%]
........                                                                 [100%]
Congratulations, your workflow is in a good condition!
```

The first container run failed one rule test: the evaluate rule's floats differ in the last
digits between the macOS and Linux numerical libraries, which a byte comparison rejects. The
rule tests now compare JSON and TSV outputs with a relative tolerance of 1e-9.
