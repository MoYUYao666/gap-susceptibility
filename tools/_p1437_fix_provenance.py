# -*- coding: utf-8 -*-
r"""Fix the provenance appendix rendering: escaped labels, breakable \\path cells, url package.

    python tools/_p1437_fix_provenance.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANIFEST = os.path.join(REPO, "docs", "provenance_manifest.json")
TARGETS = [
    ("A1", "paper_a1/main.tex", "\\begin{thebibliography}"),
    ("A23", "paper_a2/main_ieee.tex", "\\begin{thebibliography}"),
    ("P3", "paper3/paper_ieee/supplementary/supplementary.tex", "\\bibliographystyle{IEEEtran}"),
]
PREAMBLES = ["paper_a1/main.tex", "paper_a2/main_ieee.tex", "paper3/paper_ieee/supplementary/supplementary.tex",
             "paper合/main_nc.tex", "paper合/main_springer.tex"]
PANEL = "paper合/sections/provenance_appendix.tex"
START = "\\section*{Data and code provenance}"


def ensure_url(text: str) -> str:
    if "\\usepackage{url}" in text or "\\usepackage{hyperref}" in text:
        return text
    for anchor in ("\\usepackage{longtable}", "\\usepackage{booktabs}", "\\documentclass"):
        i = text.find(anchor)
        if i >= 0:
            j = text.find("\n", i)
            return text[: j + 1] + "\\usepackage{url}\n" + text[j + 1:]
    return text


def label_tex(s: str) -> str:
    return s.replace("_", "\\_")


def section(rows, label="app:provenance"):
    head = ("\n\\section*{Data and code provenance}\n\\label{%s}\n\n"
            "This appendix lists, for every table (T) and figure (F) that reports our own results, the generating script\n"
            "and the result archive (file names; full relative paths in the repository).\n\n"
            "\\begingroup\\footnotesize\n"
            "\\setlength{\\tabcolsep}{4pt}\\begin{longtable}{@{}p{0.24\\textwidth}p{0.26\\textwidth}p{0.24\\textwidth}l@{}}\n"
            "\\toprule\nitem & generating script & result archive & status \\\\\n\\midrule\n\\endhead\n" % label)
    tail = "\\bottomrule\n\\end{longtable}\n\\endgroup\n\n"
    return head + "\n".join(rows) + "\n" + tail


def rows_for(manuscript):
    d = json.load(io.open(MANIFEST, encoding="utf-8"))
    rows = []
    for e in sorted(d["manuscripts"][manuscript]["floats"], key=lambda x: x["label"]):
        sc = (e.get("script") or "--").replace("\\", "/")
        arcs = e.get("archives") or ([e["archive"]] if e.get("archive") else [])
        arc = ", ".join(os.path.basename(a) for a in arcs if a) or "--"
        rows.append("\\raggedright %s & \\raggedright\\path{%s} & \\raggedright\\path{%s} & \\texttt{%s} \\\\" % (
            label_tex(e["label"]), sc, arc, e["status"]))
    return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    ops = []
    for path, anchor in [(t[1], t[2]) for t in TARGETS]:
        t = io.open(os.path.join(REPO, path), encoding="utf-8").read()
        name = [t0[0] for t0 in TARGETS if t0[1] == path][0]
        i = t.find(START)
        assert i >= 0, path
        j = t.find(anchor, i)
        assert j > i, (path, j)
        t = t[:i] + section(rows_for(name)) + "\n" + t[j:]
        ops.append((path, t))
    ops.append((PANEL, section(rows_for("paperA"))))
    for p in PREAMBLES:
        fp = os.path.join(REPO, p)
        t = io.open(fp, encoding="utf-8").read()
        nt = ensure_url(t)
        if nt != t:
            ops.append((p, nt))
    print("  edits:", [p for p, _ in ops])
    if not a.apply:
        print("  (dry run)")
        return 0
    for path, content in ops:
        io.open(os.path.join(REPO, path), "w", encoding="utf-8", newline="").write(content)
    print("  written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
