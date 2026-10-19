def scoreset_row(wildcards):
    return SCORESETS.loc[wildcards.scoreset].to_dict()


def analysis_settings(wildcards):
    return config["analyses"][wildcards.analysis]


def variants_for_analysis(wildcards):
    release = config["analyses"][wildcards.analysis]["release"]
    return f"{DATA}/clinvar/variants_{release}.tsv.gz"


def submissions_for_analysis(wildcards):
    a = config["analyses"][wildcards.analysis]
    if a["labels"] == "before_publication":
        return [f"{DATA}/clinvar/submissions_{a['release']}.tsv.gz"]
    return []


def final_outputs():
    out = [
        f"{RES}/tables/summary.tsv",
        f"{RES}/tables/matching.tsv",
        f"{RES}/figures/auc_forest.png",
    ]
    out += expand(f"{RES}/figures/{{scoreset}}.png", scoreset=SCORESETS.index)
    return out
