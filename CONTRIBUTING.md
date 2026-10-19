# Contributing

Bug reports and pull requests are welcome. Before opening a pull request:

```console
$ make lint test rule-tests
```

All three must pass; CI runs the same targets on Ubuntu. New statistics need a known-answer
test with the expected value worked out by hand or taken from a publication, not computed by
the code under test.

Changes to the analysis itself (labels, thresholds, sensitivity analyses) go in a new dated
section at the end of `docs/analysis_plan.md` before any results are produced, and change the
major version (see CHANGELOG.md).

To add a score set, add a row to `config/scoresets.tsv`; the schema in `workflow/schemas/`
lists the required columns, and `direction` must come from the score set's own documentation.
