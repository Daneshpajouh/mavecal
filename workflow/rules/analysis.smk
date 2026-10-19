rule match_controls:
    input:
        scores=f"{DATA}/mavedb/{{scoreset}}/scores.csv",
        variants=variants_for_analysis,
        submissions=submissions_for_analysis,
    output:
        table=f"{RES}/matched/{{scoreset}}/{{analysis}}.tsv",
        stats=f"{RES}/matched/{{scoreset}}/{{analysis}}.match.json",
    log:
        f"{RES}/logs/match_controls/{{scoreset}}/{{analysis}}.log",
    benchmark:
        f"{RES}/benchmarks/match_controls/{{scoreset}}/{{analysis}}.tsv"
    conda:
        "../envs/analysis.yaml"
    params:
        row=scoreset_row,
        analysis=analysis_settings,
    script:
        "../scripts/match_controls.py"


rule evaluate:
    input:
        f"{RES}/matched/{{scoreset}}/{{analysis}}.tsv",
    output:
        summary=f"{RES}/metrics/{{scoreset}}/{{analysis}}.json",
        variants=f"{RES}/metrics/{{scoreset}}/{{analysis}}.variants.tsv",
        bins=f"{RES}/metrics/{{scoreset}}/{{analysis}}.reliability.tsv",
    log:
        f"{RES}/logs/evaluate/{{scoreset}}/{{analysis}}.log",
    benchmark:
        f"{RES}/benchmarks/evaluate/{{scoreset}}/{{analysis}}.tsv"
    conda:
        "../envs/analysis.yaml"
    params:
        row=scoreset_row,
        stats=config["statistics"],
        n_primary=len(SCORESETS),
    script:
        "../scripts/evaluate.py"


rule aggregate:
    input:
        summaries=expand(
            f"{RES}/metrics/{{scoreset}}/{{analysis}}.json",
            scoreset=SCORESETS.index,
            analysis=ANALYSES,
        ),
        match_stats=expand(
            f"{RES}/matched/{{scoreset}}/{{analysis}}.match.json",
            scoreset=SCORESETS.index,
            analysis=ANALYSES,
        ),
    output:
        summary=report(
            f"{RES}/tables/summary.tsv",
            caption="../report/summary.rst",
            category="Tables",
        ),
        matching=report(
            f"{RES}/tables/matching.tsv",
            caption="../report/matching.rst",
            category="Tables",
        ),
    log:
        f"{RES}/logs/aggregate.log",
    benchmark:
        f"{RES}/benchmarks/aggregate.tsv"
    conda:
        "../envs/analysis.yaml"
    script:
        "../scripts/aggregate.py"
