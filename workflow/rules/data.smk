rule fetch_mavedb:
    output:
        scores=f"{DATA}/mavedb/{{scoreset}}/scores.csv",
        metadata=f"{DATA}/mavedb/{{scoreset}}/metadata.json",
    log:
        f"{RES}/logs/fetch_mavedb/{{scoreset}}.log",
    benchmark:
        f"{RES}/benchmarks/fetch_mavedb/{{scoreset}}.tsv"
    conda:
        "../envs/analysis.yaml"
    resources:
        mavedb_api=1,
    params:
        urn=lambda wc: SCORESETS.loc[wc.scoreset, "urn"],
        offline=lambda wc: (
            f"{config['offline_mavedb_dir']}/{wc.scoreset}"
            if config.get("offline_mavedb_dir")
            else ""
        ),
    script:
        "../scripts/fetch_mavedb.py"


rule filter_clinvar:
    input:
        clinvar_file("variant_summary"),
    output:
        f"{DATA}/interim/variants_{{release}}.tsv.gz",
    log:
        f"{RES}/logs/filter_clinvar/{{release}}.log",
    benchmark:
        f"{RES}/benchmarks/filter_clinvar/{{release}}.tsv"
    conda:
        "../envs/analysis.yaml"
    resources:
        mem_mb=6000,
        runtime=30,
    params:
        genes=sorted(set(SCORESETS["gene"])),
    script:
        "../scripts/filter_clinvar.py"


rule filter_submissions:
    input:
        submissions=clinvar_file("submission_summary"),
        variants=f"{DATA}/interim/variants_{{release}}.tsv.gz",
    output:
        f"{DATA}/interim/submissions_{{release}}.tsv.gz",
    log:
        f"{RES}/logs/filter_submissions/{{release}}.log",
    benchmark:
        f"{RES}/benchmarks/filter_submissions/{{release}}.tsv"
    conda:
        "../envs/analysis.yaml"
    resources:
        mem_mb=6000,
        runtime=30,
    script:
        "../scripts/filter_submissions.py"
