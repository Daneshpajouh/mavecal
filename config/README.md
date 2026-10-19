# Configuration

`config.yaml` holds paths and settings; `scoresets.tsv` lists the MaveDB score sets. Both are
validated against the JSON Schemas in `workflow/schemas/` when the workflow starts.

- `data_dir`: where MaveDB downloads and filtered ClinVar tables are written. Keep it outside
  the repository.
- `clinvar`: one entry per ClinVar release, with the path to `variant_summary` and, for the
  release used by the `before_publication` analysis, `submission_summary`.
- `analyses`: release, minimum review stars and label source for each analysis. `aggregate`
  uses ClinVar's aggregate classification; `before_publication` rebuilds labels from
  submissions last evaluated before the assay was published.
- `statistics`: bootstrap replicates, random seed, number of folds, the minimum controls per
  class for threshold cross-fitting, and the class size below which results are flagged small.

`scoresets.tsv` columns: `id`, `urn`, `gene`, `assay`, `pmid`, `doi`, `published` (first online
date), `direction` (`lower_is_abnormal` or `higher_is_abnormal`, from the score set's method
text), `level` (`protein` or `nucleotide`), `transcript` (RefSeq accession without version),
`protein`, and the published class rules `t2_abnormal` and `t2_normal` (empty when the assay has
none on MaveDB).

`.tests/integration/config/` holds a configuration that runs the whole workflow on the tiny
fixtures in `tests/data/` without network access.
