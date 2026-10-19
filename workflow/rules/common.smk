def in_data_dir(path):
    return path if os.path.isabs(path) else os.path.normpath(os.path.join(DATA, path))


def clinvar_file(kind):
    return lambda wc: in_data_dir(config["clinvar"][wc.release][kind])


def scoreset_row(wildcards):
    return SCORESETS.loc[wildcards.scoreset].to_dict()


def analysis_settings(wildcards):
    return config["analyses"][wildcards.analysis]


def variants_for_analysis(wildcards):
    release = config["analyses"][wildcards.analysis]["release"]
    return f"{DATA}/interim/variants_{release}.tsv.gz"


def submissions_for_analysis(wildcards):
    a = config["analyses"][wildcards.analysis]
    if a["labels"] == "before_publication":
        return [f"{DATA}/interim/submissions_{a['release']}.tsv.gz"]
    return []


def final_outputs():
    out = [
        f"{RES}/tables/summary.tsv",
        f"{RES}/tables/matching.tsv",
        f"{RES}/figures/auc_forest.png",
    ]
    out += expand(f"{RES}/figures/{{scoreset}}.png", scoreset=SCORESETS.index)
    return out


def manifest_inputs():
    paths = [in_data_dir(f) for r in config["clinvar"].values() for f in r.values()]
    paths += [f"{DATA}/mavedb/{s}/scores.csv" for s in SCORESETS.index]
    return [Path(p) for p in paths]
