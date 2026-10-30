# -*- coding: utf-8 -*-
r"""Insert the per-float provenance appendix into the four LaTeX manuscripts and the P3 supplement.

Each manuscript receives a "Data and code provenance" appendix whose table lists every results float with its generating
script and result archive, generated from docs/provenance_manifest.json.

    python tools/_p1436_insert_provenance.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANIFEST = os.path.join(REPO, "docs", "provenance_manifest.json")
A1 = "paper_a1/main.tex"
A23 = "paper_a2/main_ieee.tex"
PANEL = "paper合/sections/provenance_appendix.tex"
PNC = "paper合/main_nc.tex"
PSPR = "paper合/main_springer.tex"
P3SUPP = "paper3/paper_ieee/supplementary/supplementary.tex"


def rows_for(manuscript):
    d = json.load(io.open(MANIFEST, encoding="utf-8"))
    rows = []
    for e in sorted(d["manuscripts"][manuscript]["floats"], key=lambda x: x["label"]):
        sc = e.get("script") or "--"
        arcs = e.get("archives") or ([e["archive"]] if e.get("archive") else [])
        arc = ", ".join(os.path.basename(a) for a in arcs if a) or "--"
        kind = "T" if e["kind"] == "table" else "F"
        esc = lambda s: s.replace("_", "\\_")
        rows.append("%s & \\texttt{%s} & \\texttt{%s} & \\texttt{%s} \\\\" % (
            e["label"], esc(sc), esc(arc), e["status"]))
    return rows


def section(title, rows, label):
    head = ("\n\\section*{%s}\n\\label{%s}\n\nThis appendix lists, for every table (T) and figure (F) that reports our own results, the\n"
            "generating script and the result archive (file names; full relative paths in the repository).\n\n"
            "\\begin{longtable}{@{}p{0.24\\textwidth}p{0.34\\textwidth}p{0.28\\textwidth}l@{}}\n"
            "\\toprule\nitem & generating script & result archive & status \\\\\n\\midrule\n"
            "\\endhead\n" % (title, label))
    tail = "\\bottomrule\n\\end{longtable}\n\n"
    return head + "\n".join(rows) + "\n" + tail


def ensure_longtable(text):
    if "longtable" in text:
        return text
    for anchor in ("\\usepackage{booktabs}", "\\usepackage{amsmath}", "\\documentclass"):
        i = text.find(anchor)
        if i >= 0:
            j = text.find("\n", i)
            return text[: j + 1] + "\\usepackage{longtable}\n" + text[j + 1:]
    return "\\usepackage{longtable}\n" + text


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    ops = []
    # A1
    t = io.open(A1, encoding="utf-8").read()
    if "Data and code provenance" not in t:
        t = ensure_longtable(t)
        sec = section("Data and code provenance", rows_for("A1"), "app:provenance")
        anchor = "\\begin{thebibliography}"
        if anchor not in t:
            anchor = "\\end{document}"
        t = t.replace(anchor, sec + "\n" + anchor, 1)
        ops.append(("A1", A1, t))
    # A23
    t = io.open(A23, encoding="utf-8").read()
    if "Data and code provenance" not in t:
        t = ensure_longtable(t)
        sec = section("Data and code provenance", rows_for("A23"), "app:provenance")
        anchor = "\\begin{thebibliography}"
        t = t.replace(anchor, sec + "\n" + anchor, 1)
        ops.append(("A23", A23, t))
    # Paper A shared appendix file + inputs
    t = io.open(PNC, encoding="utf-8").read()
    if "provenance_appendix" not in t:
        ops.append(("paperA main", PNC, t.replace("\\bibliography{references}", "\\input{sections/provenance_appendix}\n\n\\bibliography{references}", 1)
                    if "\\bibliography{references}" in t else t))
    ts = io.open(PSPR, encoding="utf-8").read()
    if "provenance_appendix" not in ts:
        if "\\bibliography{references}" in ts:
            ops.append(("paperA springer", PSPR, ts.replace("\\bibliography{references}",
                                                            "\\input{sections/provenance_appendix}\n\n\\bibliography{references}", 1)))
    if not os.path.exists(PANEL):
        ops.append(("paperA appendix", PANEL, section("Data and code provenance", rows_for("paperA"), "app:provenance")))
    # P3 supplement
    t = io.open(P3SUPP, encoding="utf-8").read()
    if "Data and code provenance" not in t:
        t = ensure_longtable(t)
        sec = section("Data and code provenance", rows_for("P3"), "app:provenance")
        anchor = "\\bibliographystyle{IEEEtran}"
        t = t.replace(anchor, sec + "\n" + anchor, 1)
        ops.append(("P3 supplement", P3SUPP, t))
    print("  pending edits:", len(ops))
    for name, path, _ in ops:
        print("   -", name, "->", path)
    if not a.apply:
        print("  (dry run)")
        return 0
    for name, path, content in ops:
        io.open(path, "w", encoding="utf-8", newline="").write(content)
    print("  written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
