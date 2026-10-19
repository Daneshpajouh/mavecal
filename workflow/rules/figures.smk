rule scoreset_figure:
    input:
        variants=f"{RES}/metrics/{{scoreset}}/main.variants.tsv",
        summary=f"{RES}/metrics/{{scoreset}}/main.json",
        bins=f"{RES}/metrics/{{scoreset}}/main.reliability.tsv",
    output:
        png=report(
            f"{RES}/figures/{{scoreset}}.png",
            caption="../report/scoreset_figure.rst",
            category="Figures",
            subcategory="Per score set",
            labels={"score set": "{scoreset}"},
        ),
        svg=f"{RES}/figures/{{scoreset}}.svg",
    log:
        f"{RES}/logs/scoreset_figure/{{scoreset}}.log",
    conda:
        "../envs/analysis.yaml"
    params:
        row=scoreset_row,
    script:
        "../scripts/scoreset_figure.py"


rule forest_figure:
    input:
        f"{RES}/tables/summary.tsv",
    output:
        png=report(
            f"{RES}/figures/auc_forest.png",
            caption="../report/auc_forest.rst",
            category="Figures",
            subcategory="Across analyses",
        ),
        svg=f"{RES}/figures/auc_forest.svg",
    log:
        f"{RES}/logs/forest_figure.log",
    conda:
        "../envs/analysis.yaml"
    script:
        "../scripts/forest_figure.py"
