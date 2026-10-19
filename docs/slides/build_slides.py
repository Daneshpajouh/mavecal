"""Build docs/slides/slides.html, a self-contained deck for a non-specialist audience.

Numbers are copied from results/tables/summary.tsv of the 2026-10-19 run; figures are inlined
from results/figures so the file opens without network access.
Run from the repository root: python docs/slides/build_slides.py
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def svg(name: str) -> str:
    text = (ROOT / "results" / "figures" / name).read_text()
    text = re.sub(r"^<\?xml[^>]*>\s*", "", text)
    text = re.sub(r"<!DOCTYPE[^>]*>\s*", "", text)
    return text


SLIDES = [
    """<h1>Do lab assays agree with what is known about disease variants?</h1>
<p class="sub">Six multiplexed assays of variant effect checked against ClinVar</p>
<p>Amir Daneshpajouh, 2026-10-19. Research software; nothing here classifies a patient's variant.</p>""",
    """<h2>The problem</h2>
<p>Genetic tests find many variants that change a single amino acid in a protein.</p>
<p>For most of them nobody knows whether they cause disease. The report says
<b>variant of uncertain significance</b>, and the patient and their doctor cannot act on it.</p>""",
    """<h2>What a MAVE measures</h2>
<p>A multiplexed assay of variant effect makes thousands of versions of a gene and measures, in
cells, how well each version works.</p>
<p>The score measures function in a lab system. It is not a probability of disease.</p>""",
    """<h2>How to check an assay</h2>
<p>Take variants whose effect is already settled in ClinVar (pathogenic or benign, reviewed by
at least two labs or an expert panel) and ask:</p>
<ul><li>Does the assay score them apart? (ROC AUC: 0.5 is a coin toss, 1.0 is perfect.)</li>
<li>How much more often is an "abnormal" result seen for pathogenic variants? (OddsPath, which
ClinGen maps to evidence levels: above 4.3 moderate, above 18.7 strong.)</li></ul>""",
    """<h2>Keeping the test honest</h2>
<ul><li>The analysis plan was committed before any score was compared with a label.</li>
<li>The cut-off between "abnormal" and "normal" for each variant was chosen on the other
variants only (five-fold cross-fitting).</li>
<li>Some ClinVar labels may already rest on these assays. The test is repeated on ClinVar as it
stood in January 2018, before any of the six assays was published.</li></ul>""",
    """<h2>Six assays, four genes</h2>
<table><tr><th>assay</th><th>pathogenic</th><th>benign</th></tr>
<tr><td>BRCA1 genome editing</td><td>146</td><td>22</td></tr>
<tr><td>BRCA1 DNA repair reporter</td><td>31</td><td>16</td></tr>
<tr><td>TP53 cell growth</td><td>202</td><td>74</td></tr>
<tr><td>PTEN enzyme activity</td><td>142</td><td>3</td></tr>
<tr><td>PTEN protein abundance</td><td>107</td><td>5</td></tr>
<tr><td>MSH2 drug resistance</td><td>112</td><td>54</td></tr></table>
<p>Known benign variants are scarce. For PTEN there are too few to calibrate anything.</p>""",
    f"""<h2>All six separate the known variants</h2>
<div class="fig">{svg("auc_forest.svg")}</div>
<p class="note">Black: main analysis. Grey: the same test with other label sets.</p>""",
    """<h2>How much evidence each readout is worth</h2>
<table><tr><th>assay</th><th>"abnormal" result</th><th>"normal" result</th></tr>
<tr><td>BRCA1 genome editing</td><td>moderate</td><td>strong (benign)</td></tr>
<tr><td>BRCA1 DNA repair reporter</td><td>supporting</td><td>supporting (benign)</td></tr>
<tr><td>TP53 cell growth</td><td>moderate</td><td>moderate (benign)</td></tr>
<tr><td>MSH2 drug resistance</td><td>moderate</td><td>moderate (benign)</td></tr>
<tr><td>PTEN, both assays</td><td colspan="2">not estimated: 3 and 5 benign controls</td></tr></table>
<p class="note">Levels read from the cautious end of each 95% interval.</p>""",
    """<h2>Against 2018 labels, every assay scores lower</h2>
<table><tr><th>assay</th><th>AUC, 2026 labels</th><th>AUC, 2018 labels</th></tr>
<tr><td>BRCA1 genome editing</td><td>0.983</td><td>0.944</td></tr>
<tr><td>BRCA1 DNA repair reporter</td><td>0.861</td><td>0.735</td></tr>
<tr><td>TP53 cell growth</td><td>0.960</td><td>0.912</td></tr>
<tr><td>MSH2 drug resistance</td><td>0.924</td><td>0.807</td></tr></table>
<p>Part of today's agreement may come from labels that used the assays. The 2018 label sets are
also smaller and less reviewed, so the drop mixes both effects.</p>""",
    """<h2>What this does and does not show</h2>
<ul><li>Shows: agreement between assay scores and expert labels, with honest uncertainty.</li>
<li>Does not show: that an assay models the disease, which ClinGen asks experts to judge
separately.</li>
<li>Next: more benign controls, for example from population frequencies, and labels whose
evidence sources are recorded, so assay-informed labels can be removed directly.</li></ul>
<p class="note">Code, data sources and every number: the repository's docs/report.md.</p>""",
]

PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>MAVE calibration against ClinVar</title>
<style>
body {{ margin: 0; font-family: Helvetica, Arial, sans-serif; background: #fafafa; color: #222; }}
section {{ display: none; box-sizing: border-box; min-height: 100vh; padding: 6vh 8vw; }}
section.on {{ display: block; }}
h1 {{ font-size: 2.4em; margin-top: 18vh; }} h2 {{ font-size: 1.9em; }}
p, li, td, th {{ font-size: 1.3em; line-height: 1.45; }}
.sub {{ font-size: 1.5em; color: #555; }} .note {{ font-size: 1em; color: #666; }}
table {{ border-collapse: collapse; margin: 1em 0; }}
td, th {{ border-bottom: 1px solid #ccc; padding: 0.3em 1.2em 0.3em 0; text-align: left; }}
.fig svg {{ max-width: 100%; height: auto; max-height: 68vh; }}
footer {{ position: fixed; bottom: 1em; right: 2em; color: #888; font-size: 0.9em; }}
</style></head><body>
{slides}
<footer><span id="n"></span> / {count} (arrow keys or click)</footer>
<script>
const s = document.querySelectorAll("section"); let i = 0;
function show(k) {{ i = Math.max(0, Math.min(s.length - 1, k)); s.forEach((e, j) => e.classList.toggle("on", j === i));
  document.getElementById("n").textContent = i + 1; }}
document.addEventListener("keydown", e => {{ if (["ArrowRight", "PageDown", " "].includes(e.key)) show(i + 1);
  if (["ArrowLeft", "PageUp"].includes(e.key)) show(i - 1); }});
document.addEventListener("click", e => show(e.clientX > innerWidth / 3 ? i + 1 : i - 1));
show(0);
</script></body></html>
"""


def main() -> None:
    body = "\n".join(f"<section>{s}</section>" for s in SLIDES)
    out = ROOT / "docs" / "slides" / "slides.html"
    out.write_text(PAGE.format(slides=body, count=len(SLIDES)))


if __name__ == "__main__":
    main()
