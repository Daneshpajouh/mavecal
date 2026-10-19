# Logging

Each run writes three kinds of record under `results_dir`:

- before any rule runs, `run/manifest_start.json`: start time (UTC), git commit and whether the
  working tree had uncommitted changes, SHA-256 of `docs/analysis_plan.md`, package versions,
  the full config, and size and SHA-256 of every input file (paths relative to `data_dir`);
- per rule, `logs/<rule>/<wildcards>.log` (timestamped messages from the `mavecal` logger, plus
  any traceback) and `benchmarks/<rule>/<wildcards>.tsv` from Snakemake's `benchmark`
  directive;
- at the end, `run/manifest_end.json`: status (`success` or `error`), duration, SHA-256 of
  `tables/summary.tsv` and of every table and figure.

All Python code logs through one logger set up by `mavecal.logs.setup_logging`, which also sends
stderr to the rule log so a failed job leaves its traceback there.

On macOS, Snakemake's benchmark sampler cannot read memory statistics (psutil raises
`mach_vm_region` errors), so the memory columns are `NA` and the local profile retries a job
whose sampler failed. On Linux the columns are filled.

## Example from the run of 2026-10-19

`results/run/manifest_start.json` (abridged):

```json
{
 "started_utc": "2026-10-19T19:09:14+00:00",
 "git_commit": "4c676522e828e30cf92bbf265a78328639f30762",
 "git_uncommitted_changes": false,
 "analysis_plan": {"path": "docs/analysis_plan.md", "bytes": 7969,
  "sha256": "30246cf38de8f2acfcea9dc5ab54dd85f73c6dcf03d48680e71ad055ca7c87b6"},
 "versions": {"python": "3.13.9", "snakemake": "9.27.0", "numpy": "2.5.4", "pandas": "3.0.6"},
 "inputs": [
  {"path": "clinvar_releases/variant_summary_2026-10.txt.gz", "bytes": 450727547,
   "sha256": "a6a58df4d9049c9187a79a8fb4e70f1f3b5550e1708c6c74b7be0b268f5032da"},
  "... 9 more"
 ]
}
```

`results/logs/filter_clinvar/2026-10.log`:

```
2026-10-19 12:10:01,320 INFO mavecal: variant_summary_2026-10.txt.gz: 23658 GRCh38 SNV rows for BRCA1,MSH2,PTEN,TP53
2026-10-19 12:10:01,320 INFO mavecal: label counts: {nan: 13606, 'B': 7467, 'P': 2585}
```

`results/benchmarks/filter_clinvar/2026-10.tsv`: 39.02 s wall time, memory columns `NA`.

`results/run/manifest_end.json` (abridged):

```json
{
 "status": "success",
 "finished_utc": "2026-10-19T19:10:26+00:00",
 "duration_seconds": 72.1,
 "summary_table_sha256": "c327f52a35d4f0483ebb4413fb6f4460f243e5b273ea351ea47160071cf1277d",
 "outputs": ["... 16 tables and figures with size and SHA-256"]
}
```

The summary table had this hash after the aggregation run at 12:06 Pacific and after two full
reruns at 12:08 and 12:09 that re-downloaded every MaveDB score set.
