# Data sources

Nothing below is stored in the repository except derived tables in `results/`. Paths are relative
to `data_dir`.

## ClinVar

Monthly releases from NCBI's ClinVar archive, fetched on 2026-10-19 (Pacific) over FTP
(`ftp://ftp.ncbi.nlm.nih.gov/pub/clinvar/tab_delimited/archive/`). The same files are served over
HTTPS, but `https://ftp.ncbi.nlm.nih.gov/robots.txt` disallows all automated clients, so no
script read the HTTPS host. The archive publishes no checksums; each file passed `gzip -t` and
its size matched the server's reported length.

| file (under `clinvar_releases/`) | server date (GMT) | bytes | SHA-256 |
|---|---|---|---|
| `variant_summary_2026-10.txt.gz` | 2026-10-01 04:05 | 450,727,547 | `a6a58df4d9049c9187a79a8fb4e70f1f3b5550e1708c6c74b7be0b268f5032da` |
| `submission_summary_2026-10.txt.gz` | 2026-10-01 04:05 | 394,172,714 | `c93758c972fbeb958b49aa560a374bdaf5c57cc4f159644a19bed88200a870ac` |
| `variant_summary_2025-10.txt.gz` | 2025-10-02 04:05 | 384,432,958 | `b99920190c2eb00382cf9ec154442bb83fe5a14a397f93e6db22c8fda094fc77` |
| `variant_summary_2018-01.txt.gz` (`archive/2018/`) | 2018-01-04 05:05 | 25,120,853 | `9e81416ea144a1c05eec15198cc42d15ab808193a906a3ff3c67d78dd0e17fb1` |

The 2026-10 monthly release is used instead of the weekly `variant_summary.txt.gz` because an
archived release can be fetched again by name. Terms: the ClinVar README in that directory
states no licence. ClinVar is distributed by NCBI under its website and data usage policies,
which were not re-read for this run; cite Landrum et al. (2018).

## MaveDB

Fetched on 2026-10-19 with `GET https://api.mavedb.org/api/v1/score-sets/{urn}` and
`GET .../variants/data?namespaces=scores&namespaces=mavedb`, one request per second.
`https://api.mavedb.org/robots.txt` does not exist (HTTP 404). Every score set carries the CC0
1.0 licence on its MaveDB record.

| id | URN | rows | bytes (`mavedb/<id>/scores.csv`) | SHA-256 |
|---|---|---|---|---|
| brca1_sge | urn:mavedb:00000097-0-2 | 3,893 | 717,224 | `570993a0ef65f4d421669de575a9d60580af3eb5f1f0de5ea153cd93db892996` |
| brca1_hdr | urn:mavedb:00000081-a-2 | 2,820 | 455,542 | `be8497ba3d9ae8798c0800385d1bad9c7c788776fafbe7d03ed4d78bfa77c4be` |
| tp53_nutlin | urn:mavedb:00000068-b-1 | 8,274 | 1,341,613 | `496efde49b8b5efb76af408f715350eeb342342bf3ef7f759d70c6490f48a0e0` |
| pten_phosphatase | urn:mavedb:00000054-a-1 | 8,681 | 1,925,503 | `af12f0cb0061d3c00f8f42edffa859e8a5c202c0e3d279b8fe27adc1083efd4a` |
| pten_abundance | urn:mavedb:00000013-a-1 | 4,409 | 708,812 | `68edaae8ce48a270d9b82d87122f590691397af02ef55baf7326544cbce72b05` |
| msh2_lof | urn:mavedb:00000050-a-1 | 17,746 | 2,883,100 | `6625594063e5812708e50da0ce5bd52ec4368c9b379e778d03a8fe3a24875a03` |

MaveDB can update post-mapped annotations after publication, so a later download may differ;
`results/run/manifest_start.json` records the hashes each run read.

## Publication dates

First online dates, used for S4, come from Europe PMC (`firstPublicationDate`): Findlay
2018-09-12, Starita 2018-09-12, Giacomelli 2018-09-17, Mighell 2018-04-26, Matreyek 2018-05-21,
Jia 2020-12-23.
