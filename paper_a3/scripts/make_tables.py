# -*- coding: utf-8 -*-
r"""Generate the LaTeX tables for A3 directly from the archived analysis JSONs.

table_main.tex     - mean +- std of R@1(image->text) per dataset x provenance x site
table_scaling.tex  - NWPU-Captions, 10k vs 50k pairs by provenance arm
table_setup.tex    - corpus statistics from the frozen provenance manifests

Every number in the generated files comes from an archived JSON; nothing is typed by hand.

Usage
  python make_tables.py
"""
import glob
import io
import json
import os
import statistics as st

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEX = os.path.join(ROOT, "draft")
ARMS = ["human", "segmented", "templated", "metadata"]
ARMS_LABEL = {"human": "Human captions", "segmented": "Parsed-object", "templated": "Templated", "metadata": "Metadata"}
SITES = ["vision", "text", "both"]
DATASETS = ["rsicd", "rsitmd", "nwpu_captions", "dior_rsvg"]
DATASETS_LABEL = {"rsicd": "RSICD", "rsitmd": "RSITMD", "nwpu_captions": "NWPU-Captions", "dior_rsvg": "DIOR-RSVG"}


def macname(*parts):
    return "".join(parts).replace("_", "")


def load(path):
    return json.loads(io.open(path, encoding="utf-8").read())


def table_main(agg):
    table = {(e["dataset"], e["arm"], e["site"]): e for e in agg["table"]}
    lines = [r"\begin{table}[t]", r"\centering", r"\footnotesize",
             r"\caption{Retrieval at a matched 10{,}000-pair budget: R@1 (image$\rightarrow$text), mean $\pm$ standard "
             r"deviation over three seeds. The best site per dataset and provenance arm is in bold.}",
             r"\label{tab:main}",
             r"\begin{tabular}{@{}llccc@{}}", r"\hline",
             r"Dataset & Text provenance & Vision tower & Text tower & Both towers \\", r"\hline"]
    for ds in DATASETS:
        first = True
        for arm in ARMS:
            cells = []
            vals = {}
            for site in SITES:
                e = table.get((ds, arm, site))
                vals[site] = e["R@1_i2t"]["mean"] if e else -1
            best = max(vals, key=vals.get)
            for site in SITES:
                e = table.get((ds, arm, site))
                if not e:
                    cells.append("--")
                    continue
                txt = "%.3f $\\pm$ %.3f" % (e["R@1_i2t"]["mean"], e["R@1_i2t"]["std"])
                cells.append("\\textbf{%s}" % txt if site == best else txt)
            lines.append("%s & %s & %s \\\\" % (DATASETS_LABEL[ds] if first else "", ARMS_LABEL[arm], " & ".join(cells)))
            first = False
        lines.append(r"\hline")
    lines += [r"\end{tabular}", r"\end{table}"]
    out = os.path.join(TEX, "table_main.tex")
    io.open(out, "w", encoding="utf-8", newline="").write("\n".join(lines) + "\n")
    return out


def table_scaling(scaling):
    lines = [r"\begin{table}[t]", r"\centering", r"\footnotesize",
             r"\caption{The return from more pairs depends on the text: NWPU-Captions, R@1 (image$\rightarrow$text), "
             r"seeds 0--1 common to both budgets. The derived arms stop at 31{,}500 pairs, the number of images.}",
             r"\label{tab:scaling}",
             r"\begin{tabular}{@{}llcccc@{}}", r"\hline",
             r"Provenance & Site & 10k pairs & larger budget & change & modality gap \\", r"\hline"]
    by = {(r["arm"], r["site"]): r for r in scaling["rows"]}
    for arm in ARMS:
        for site in ("vision", "both"):
            r = by.get((arm, site))
            if not r:
                continue
            lines.append("%s & %s & %.3f & %.3f & %+.3f & %.3f \\\\" % (
                ARMS_LABEL[arm], site, r["R1_10k"], r["R1_50k"], r["delta"], r["gap_50k"]))
        lines.append(r"\hline")
    lines += [r"\end{tabular}", r"\end{table}"]
    out = os.path.join(TEX, "table_scaling.tex")
    io.open(out, "w", encoding="utf-8", newline="").write("\n".join(lines) + "\n")
    return out


def table_setup():
    rows = []
    for ds in DATASETS:
        manifest_path = os.path.join(ROOT, "corpora", ds, "provenance_manifest.json")
        if not os.path.exists(manifest_path):
            continue
        m = load(manifest_path)
        per = m["per_corpus"]
        rows.append((DATASETS_LABEL[ds], m["records_in"],
                     per.get("human", {}).get("kept", 0),
                     per.get("segmented", {}).get("kept", 0),
                     per.get("templated", {}).get("kept", 0),
                     per.get("metadata", {}).get("kept", 0)))
    lines = [r"\begin{table}[t]", r"\centering", r"\footnotesize",
             r"\caption{The four frozen provenance corpora. Pair counts are after de-duplication; the human column counts "
             r"captions, the derived columns one text per image.}",
             r"\label{tab:corpora}",
             r"\begin{tabular}{@{}lccccc@{}}", r"\hline",
             r"Dataset & Images & Human & Parsed-object & Templated & Metadata \\", r"\hline"]
    for r in rows:
        lines.append("%s & %d & %d & %d & %d & %d \\\\" % r)
    lines += [r"\hline", r"\end{tabular}", r"\end{table}"]
    out = os.path.join(TEX, "table_setup.tex")
    io.open(out, "w", encoding="utf-8", newline="").write("\n".join(lines) + "\n")
    return out


def wrap_tables():
    """Ensure every generated table fits the text width (resizebox around the tabular)."""
    import glob as _glob
    import re as _re
    for path in _glob.glob(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "draft", "table_*.tex")):
        s = io.open(path, encoding="utf-8").read()
        if "resizebox" in s:
            continue
        m = _re.search(r"\\begin\{tabular\}.*?\\end\{tabular\}", s, _re.S)
        if m:
            s = s.replace(m.group(0), "\\resizebox{\\linewidth}{!}{%\n" + m.group(0) + "}")
            io.open(path, "w", encoding="utf-8", newline="").write(s)


def main():
    os.makedirs(TEX, exist_ok=True)
    agg = load(os.path.join(ROOT, "analysis", "full_10k_aggregate.json"))
    written = [table_main(agg), table_setup()]
    scaling_path = os.path.join(ROOT, "analysis", "h2_scaling.json")
    if os.path.exists(scaling_path):
        written.append(table_scaling(load(scaling_path)))
    for p in written:
        print("wrote", p)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
