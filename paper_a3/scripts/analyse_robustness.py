# -*- coding: utf-8 -*-
r"""Robustness analyses for A3: does the provenance ordering survive training length, backbone and target corpus?

Reads only archived JSON records (never the run directories directly except for adapters' summaries that were already
aggregated) and writes:
  analysis/robustness.json
  draft/table_epochs.tex      two versus six epochs
  draft/table_backbones.tex   ViT-B/32, GeoRSCLIP ViT-B/32 and RemoteCLIP ViT-L/14
  draft/table_transfer.tex    cross-corpus transfer matrix, averaged over seeds where available
  draft/rust_numbers.tex      macros for the numbers quoted in the robustness section

Usage
  python analyse_robustness.py
"""
import glob
import io
import json
import os
import statistics as st
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARMS = ["human", "segmented", "templated", "metadata"]
LABEL = {"human": "Human captions", "segmented": "Parsed-object", "templated": "Templated",
         "metadata": "Metadata", "humanrich": "Human-rich (5 captions)", "metaclass": "Class-only metadata"}
DATASETS = ["rsicd", "rsitmd", "nwpu_captions", "dior_rsvg"]
DS_LABEL = {"rsicd": "RSICD", "rsitmd": "RSITMD", "nwpu_captions": "NWPU-Captions", "dior_rsvg": "DIOR-RSVG"}


def load(path):
    return json.loads(io.open(path, encoding="utf-8").read())


def aggregate_dir(runs_dir):
    out = defaultdict(list)
    for p in glob.glob(os.path.join(ROOT, "runs", runs_dir, "*.json")):
        rec = load(p)
        name = os.path.basename(p)[:-5]
        parts = name.split("_")
        seed = parts[-1]
        site = parts[-2]
        arm = parts[-4]
        dataset = "_".join(parts[:-4])
        out[(dataset, arm)].append(rec["metrics"])
    return {k: {m: round(st.mean([r.get(m, 0) for r in v]), 4) for m in ("R@1_i2t", "R@1_t2i")} for k, v in out.items()}


def table_epochs(epochs):
    rows = epochs["rows"]
    lines = [r"\begin{table}[t]", r"\centering", r"\footnotesize",
             r"\caption{Training length matters as much as provenance. Same cells, two versus six epochs (site = both, "
             r"10{,}000 pairs, seed 0 for the six-epoch column). The ordering of the provenance arms changes: short "
             r"training flatters text that is easy to align quickly.}",
             r"\label{tab:epochs}",
             r"\begin{tabular}{@{}llccc@{}}", r"\hline",
             r"Dataset & Provenance & R@1 (2 epochs) & R@1 (6 epochs) & change \\", r"\hline"]
    for r in rows:
        lines.append("%s & %s & %.3f & %.3f & %+.3f \\\\" % (
            DS_LABEL.get(r["dataset"], r["dataset"]), LABEL.get(r["arm"], r["arm"]),
            r["epochs2"]["R@1_i2t"], r["epochs6"]["R@1_i2t"],
            r["epochs6"]["R@1_i2t"] - r["epochs2"]["R@1_i2t"]))
    lines += [r"\hline", r"\end{tabular}", r"\end{table}"]
    io.open(os.path.join(ROOT, "draft", "table_epochs.tex"), "w", encoding="utf-8", newline="").write("\n".join(lines) + "\n")


def table_backbones(base, geo, l14, humanrich):
    lines = [r"\begin{table}[t]", r"\centering", r"\footnotesize",
             r"\caption{The two-epoch ordering is not specific to one backbone, and packing more human text into the pair "
             r"helps. Human captions against metadata where the grid allows; human-rich is five captions concatenated into "
             r"one description. All cells: joint adaptation site, 10{,}000 pairs.}",
             r"\label{tab:backbones}",
             r"\begin{tabular}{@{}llccc@{}}", r"\hline",
             r"Backbone & Dataset & Human captions & Metadata & Human-rich \\", r"\hline"]
    for ds in ("rsicd", "nwpu_captions"):
        def pick(agg, arm):
            e = [x for x in agg["table"] if x["dataset"] == ds and x["arm"] == arm and x["site"] == "both"]
            return e[0]["R@1_i2t"]["mean"] if e else None
        h32, m32 = pick(base, "human"), pick(base, "metadata")
        g32 = pick(geo, "human")
        l14h, l14m = pick(l14, "human"), pick(l14, "metadata")
        hr = humanrich.get(ds)
        lines.append("ViT-B/32 (RemoteCLIP) & %s & %.3f & %.3f & %s \\\\" % (
            DS_LABEL[ds], h32 or 0, m32 or 0, ("%.3f" % hr) if hr else "--"))
        lines.append("ViT-B/32 (GeoRSCLIP) & %s & %.3f & -- & -- \\\\" % (DS_LABEL[ds], g32 or 0))
        lines.append("ViT-L/14 (RemoteCLIP) & %s & %.3f & %.3f & -- \\\\" % (DS_LABEL[ds], l14h or 0, l14m or 0))
        lines.append(r"\hline")
    lines += [r"\end{tabular}", r"\end{table}"]
    io.open(os.path.join(ROOT, "draft", "table_backbones.tex"), "w", encoding="utf-8", newline="").write("\n".join(lines) + "\n")


def table_transfer(transfer):
    rows = transfer["rows"]
    by = defaultdict(list)
    for r in rows:
        by[(r["arm"], r["target_corpus"])].append(r["R@1_i2t"])
    lines = [r"\begin{table}[t]", r"\centering", r"\footnotesize",
             r"\caption{Provenance ordering under a change of target corpus. Adapters trained on RSICD or NWPU-Captions "
             r"(joint site, seed 0), evaluated on each target's test split with a 600-query pool (the pool size affects the "
             r"absolute value, so only rows within this table are comparable). Human captions stay ahead on every target; "
             r"the metadata arm loses least in relative terms because its text is corpus-independent.}",
             r"\label{tab:transfer}",
             r"\begin{tabular}{@{}lccc@{}}", r"\hline",
             r"Provenance & target RSICD & target RSITMD & target NWPU \\", r"\hline"]
    for arm in ("human", "templated", "metadata"):
        cells = []
        for target in ("rsicd", "rsitmd", "nwpu_captions"):
            vals = by.get((arm, target), [])
            cells.append("%.3f" % st.mean(vals) if vals else "--")
        lines.append("%s & %s \\\\" % (LABEL[arm], " & ".join(cells)))
    lines += [r"\hline", r"\end{tabular}", r"\end{table}"]
    io.open(os.path.join(ROOT, "draft", "table_transfer.tex"), "w", encoding="utf-8", newline="").write("\n".join(lines) + "\n")


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
    base = load(os.path.join(ROOT, "analysis", "full_10k_aggregate.json"))
    geo = load(os.path.join(ROOT, "analysis", "georsclip", "full_10k_aggregate.json"))
    l14 = load(os.path.join(ROOT, "analysis", "l14", "full_10k_aggregate.json"))
    epochs = load(os.path.join(ROOT, "analysis", "epoch_ablation.json"))
    transfer = load(os.path.join(ROOT, "analysis", "transfer_matrix.json"))

    humanrich = {}
    for ds, runs_dir in (("rsicd", "humanrich_10k"), ("nwpu_captions", "humanrich_10k")):
        vals = []
        for p in glob.glob(os.path.join(ROOT, "runs", runs_dir, ds + "*.json")):
            vals.append(load(p)["metrics"]["R@1_i2t"])
        if vals:
            humanrich[ds] = round(st.mean(vals), 4)

    table_epochs(epochs)
    table_backbones(base, geo, l14, humanrich)
    table_transfer(transfer)

    # macros for the prose
    mac = ["% Generated by analyse_robustness.py from the archived JSON records."]
    def add(name, value):
        mac.append("\\newcommand{\\%s}{%s}" % (name, value))
    for r in epochs["rows"]:
        key = r["dataset"].replace("_", "") + r["arm"]
        add("ep" + key + "Two", "%.3f" % r["epochs2"]["R@1_i2t"])
        add("ep" + key + "Six", "%.3f" % r["epochs6"]["R@1_i2t"])
    for ds, v in humanrich.items():
        add("rich" + ds.replace("_", ""), "%.3f" % v)
    for x in geo["table"]:
        if x["site"] == "both":
            add("geo" + x["dataset"].replace("_", "") + x["arm"], "%.3f" % x["R@1_i2t"]["mean"])
    for x in l14["table"]:
        add("lfourteen" + x["dataset"].replace("_", "") + x["arm"], "%.3f" % x["R@1_i2t"]["mean"])
    # transfer macros: mean over source corpora per (arm, target)
    by = {}
    for r in transfer["rows"]:
        by.setdefault((r["arm"], r["target_corpus"]), []).append(r["R@1_i2t"])
    for (arm, target), vals in by.items():
        add("tr" + arm + target.replace("_", ""), "%.3f" % st.mean(vals))
    io.open(os.path.join(ROOT, "draft", "rust_numbers.tex"), "w", encoding="utf-8", newline="").write("\n".join(mac) + "\n")

    summary = {"epoch_ablation": epochs["rows"], "humanrich": humanrich,
               "georsclip_human_first": geo["H1_human_first"],
               "l14_table": l14["table"], "transfer_rows": len(transfer["rows"])}
    io.open(os.path.join(ROOT, "analysis", "robustness.json"), "w", encoding="utf-8", newline="").write(
        json.dumps(summary, indent=1))
    wrap_tables()
    print("wrote draft/table_{epochs,backbones,transfer}.tex, draft/rust_numbers.tex, analysis/robustness.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
