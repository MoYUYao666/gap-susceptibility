# -*- coding: utf-8 -*-
r"""Merge the cloud run records into the manuscript's robustness material.

Reads:
  runs/cloud_l14/*.json        ViT-L/14 grid (4 arms x 2 corpora x 3 sites x 2 seeds)
  runs/cloud_fullcorpus/*.json full-corpus cells (human/metadata x 2 corpora x 3 seeds)
  runs/cloud_geol14/*.json     optional GeoRSCLIP-L/14 cells
Writes:
  analysis/cloud_summary.json
  draft/table_cloud_l14.tex
  draft/table_cloud_fullcorpus.tex
  draft/cloud_numbers.tex      macros used in the robustness section

Usage
  python analyse_cloud_runs.py
"""
import glob
import io
import json
import os
import statistics as st
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARMS = ["human", "segmented", "templated", "metadata"]
LABEL = {"human": "Human captions", "segmented": "Parsed-object", "templated": "Templated", "metadata": "Metadata",
         "humanrich": "Human-rich"}
DS = {"rsicd": "RSICD", "nwpu_captions": "NWPU-Captions"}
SITES = ["vision", "text", "both"]


def load_dir(name):
    out = defaultdict(list)
    prefix = {"cloud_l14": "l14_", "cloud_fullcorpus": "full_", "cloud_fullextra": "fullextra_",
                  "cloud_l14_nwpu": "l14_nwpu_", "cloud_geol14": "geol14_"}[name]
    for p in glob.glob(os.path.join(ROOT, "runs", name, "*.json")):
        rec = json.loads(io.open(p, encoding="utf-8").read())
        stem = os.path.basename(p)[:-5]
        if not stem.startswith(prefix):
            continue
        tokens = stem[len(prefix):].split("_")
        seed = int(tokens[-1][1:])
        if name in ("cloud_fullcorpus", "cloud_fullextra"):
            site = "both"
            arm = tokens[-2]
            dataset = "_".join(tokens[:-2])
        elif name == "cloud_l14_nwpu":
            site = tokens[-2]
            arm = tokens[-3]
            dataset = "nwpu_captions"
        else:
            site = tokens[-2]
            arm = tokens[-3]
            dataset = "_".join(tokens[:-3])
        if name in ("cloud_l14", "cloud_l14_nwpu") and rec.get("seed") not in (0, None):
            continue
        out[(dataset, arm, site)].append(rec["metrics"])
    return out


def mean_std(vals):
    return round(st.mean(vals), 4), round(st.stdev(vals), 4) if len(vals) > 1 else 0.0


def table_l14(cells):
    lines = [r"\begin{table}[t]", r"\centering", r"\setlength{\tabcolsep}{3pt}", r"\footnotesize",
             r"\caption{The provenance ordering at the large backbone (RemoteCLIP ViT-L/14, batch 8, 10{,}000 pairs, "
             r"seed 0). R@1 (image$\rightarrow$text); bold marks the best adaptation site per row.}",
             r"\label{tab:l14grid}",
                          r"\begin{tabular}{@{}llccc@{}}", r"\hline",
             r"Dataset & Provenance & Vision tower & Text tower & Both towers \\", r"\hline"]
    for ds in ("rsicd", "nwpu_captions"):
        first = True
        for arm in ARMS:
            cells_row = []
            best_site, best_val = None, -1
            for site in SITES:
                vals = cells.get((ds, arm, site), [])
                if vals:
                    m, _ = mean_std([v["R@1_i2t"] for v in vals])
                    if m > best_val:
                        best_site, best_val = site, m
            for site in SITES:
                vals = cells.get((ds, arm, site), [])
                if not vals:
                    cells_row.append("--")
                    continue
                m, s = mean_std([v["R@1_i2t"] for v in vals])
                txt = ("%.3f $\\pm$ %.3f" % (m, s)) if len(vals) > 1 else ("%.3f" % m)
                cells_row.append("\\textbf{%s}" % txt if site == best_site else txt)
            lines.append("%s & %s & %s \\\\" % (DS[ds] if first else "", LABEL[arm], " & ".join(cells_row)))
            first = False
        lines.append(r"\hline")
    lines += [r"\end{tabular}", r"\end{table}"]
    io.open(os.path.join(ROOT, "draft", "table_cloud_l14.tex"), "w", encoding="utf-8", newline="").write("\n".join(lines) + "\n")


def table_full(cells):
    lines = [r"\begin{table}[t]", r"\centering", r"\setlength{\tabcolsep}{3pt}", r"\footnotesize",
             r"\caption{Every image instead of the 10{,}000-pair budget (three seeds, joint site). "
             r"Mean $\pm$ standard deviation of R@1 (image$\rightarrow$text).}",
             r"\label{tab:cloudfull}",
                          r"\begin{tabular}{@{}llc@{}}", r"\hline",
             r"Dataset & Provenance & R@1 (full corpus) \\", r"\hline"]
    for ds in ("rsicd", "nwpu_captions"):
        for arm in ("human", "segmented", "templated", "metadata", "humanrich"):
            vals = cells.get((ds, arm, "both"), [])
            if not vals:
                continue
            m, s = mean_std([v["R@1_i2t"] for v in vals])
            lines.append("%s & %s & %.3f $\\pm$ %.3f \\\\" % (DS[ds], LABEL[arm], m, s))
        lines.append(r"\hline")
    lines += [r"\end{tabular}", r"\end{table}"]
    io.open(os.path.join(ROOT, "draft", "table_cloud_fullcorpus.tex"), "w", encoding="utf-8", newline="").write("\n".join(lines) + "\n")


def main():
    l14 = load_dir("cloud_l14")
    l14.update(load_dir("cloud_l14_nwpu"))
    full = load_dir("cloud_fullcorpus")
    full.update(load_dir("cloud_fullextra"))
    geo = load_dir("cloud_geol14")
    os.makedirs(os.path.join(ROOT, "analysis"), exist_ok=True)
    summary = {"l14_cells": {("%s|%s|%s" % k): v for k, v in l14.items()},
               "full_cells": {("%s|%s|%s" % k): v for k, v in full.items()},
               "geol14_cells": {("%s|%s|%s" % k): v for k, v in geo.items()}}
    io.open(os.path.join(ROOT, "analysis", "cloud_summary.json"), "w", encoding="utf-8", newline="").write(
        json.dumps(summary, indent=1))
    if l14:
        table_l14(l14)
    if full:
        table_full(full)
    macros = ["% Generated by analyse_cloud_runs.py from the cloud run records."]
    for (ds, arm, site), vals in sorted(full.items()):
        if site != "both":
            continue
        m, s = mean_std([v["R@1_i2t"] for v in vals])
        key = "clfull" + ds.replace("_", "") + arm
        macros.append("\\newcommand{\\%s}{%.3f}" % (key, m))
        macros.append("\\newcommand{\\%sSd}{%.3f}" % (key, s))
    for (ds, arm) in sorted({(k[0], k[1]) for k in l14}):
        for s_ in SITES:
            vs = l14.get((ds, arm, s_), [])
            if not vs:
                continue
            m, _ = mean_std([v["R@1_i2t"] for v in vs])
            macros.append("\\newcommand{\\cllfourteen%s%s%s}{%.3f}" % (ds.replace("_", ""), arm, s_, m))
    io.open(os.path.join(ROOT, "draft", "cloud_numbers.tex"), "w", encoding="utf-8", newline="").write(
        "\n".join(macros) + "\n")
    print("wrote analysis/cloud_summary.json and the cloud tables/macros")
    print("l14 cells:", sum(len(v) for v in l14.values()), "| full cells:", sum(len(v) for v in full.values()),
          "| geo cells:", sum(len(v) for v in geo.values()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
