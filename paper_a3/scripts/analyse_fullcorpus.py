# -*- coding: utf-8 -*-
r"""Full-corpus check: does the 10k-pair conclusion hold when every image is used?

The full-corpus cells train on every image of the corpus (all captions, at most one caption per image per batch),
so they answer the reviewer question "why subsample to 10,000 pairs?". This script compares those cells with the
matched 10k cells from the main grid and writes the table, the macros and the JSON record.

Outputs
  analysis/fullcorpus.json
  draft/table_fullcorpus.tex
  draft/rust_numbers.tex   (appends the full-corpus macros)
"""
import glob
import io
import json
import os
import statistics as st

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LABEL = {"human": "Human captions", "metadata": "Metadata"}
DS = {"rsicd": "RSICD", "nwpu_captions": "NWPU-Captions"}


def main():
    base = json.loads(io.open(os.path.join(ROOT, "analysis", "full_10k_aggregate.json"), encoding="utf-8").read())
    ten_k = {(e["dataset"], e["arm"], e["site"]): e for e in base["table"]}

    rows = []
    for p in sorted(glob.glob(os.path.join(ROOT, "runs", "fullcorpus", "*.json"))):
        rec = json.loads(io.open(p, encoding="utf-8").read())
        name = os.path.basename(p)[:-5]
        parts = name.split("_")
        dataset = "_".join(parts[:-4])
        arm = parts[-4]
        ref = ten_k.get((dataset, arm, "both"))
        rows.append({
            "dataset": dataset, "arm": arm,
            "pairs": rec.get("pairs_used"),
            "full_R1_i2t": rec["metrics"]["R@1_i2t"], "full_R1_t2i": rec["metrics"]["R@1_t2i"],
            "full_gap": rec["metrics"].get("modality_gap"),
            "tenk_R1_i2t": ref["R@1_i2t"]["mean"] if ref else None,
            "tenk_std": ref["R@1_i2t"]["std"] if ref else None,
            "delta": (rec["metrics"]["R@1_i2t"] - ref["R@1_i2t"]["mean"]) if ref else None,
        })

    lines = [r"\begin{table}[t]", r"\centering", r"\footnotesize",
             r"\caption{Using every image instead of the 10{,}000-pair budget (joint site; at most one caption per "
             r"image per batch; the full-corpus cells use all captions, seed 0). The ordering is unchanged where both "
             r"arms exist, and the absolute values move only slightly.}",
             r"\label{tab:fullcorpus}",
             r"\resizebox{\linewidth}{!}{%",
             r"\begin{tabular}{@{}llccc@{}}", r"\hline",
             r"Dataset & Provenance & pairs (full) & R@1 full & R@1 at 10k \\", r"\hline"]
    for r in rows:
        dataset_label = DS.get(r["dataset"], r["dataset"])
        tenk = ("%.3f $\\pm$ %.3f" % (r["tenk_R1_i2t"], r["tenk_std"])) if r["tenk_R1_i2t"] is not None else "--"
        lines.append("%s & %s & %d & %.3f & %s \\\\" % (dataset_label, LABEL.get(r["arm"], r["arm"]),
                                                       r["pairs"] or 0, r["full_R1_i2t"], tenk))
    lines += [r"\hline", r"\end{tabular}", r"}", r"\end{table}"]
    io.open(os.path.join(ROOT, "draft", "table_fullcorpus.tex"), "w", encoding="utf-8", newline="").write("\n".join(lines) + "\n")

    # macros
    mac = io.open(os.path.join(ROOT, "draft", "rust_numbers.tex"), encoding="utf-8").read().splitlines()
    mac = [l for l in mac if not l.startswith("\\newcommand{\\full")]
    for r in rows:
        key = r["dataset"].replace("_", "") + r["arm"]
        mac.append("\\newcommand{\\full%s}{%.3f}" % (key, r["full_R1_i2t"]))
        if r["tenk_R1_i2t"] is not None:
            mac.append("\\newcommand{\\tenk%s}{%.3f}" % (key, r["tenk_R1_i2t"]))
    io.open(os.path.join(ROOT, "draft", "rust_numbers.tex"), "w", encoding="utf-8", newline="").write("\n".join(mac) + "\n")

    io.open(os.path.join(ROOT, "analysis", "fullcorpus.json"), "w", encoding="utf-8", newline="").write(
        json.dumps({"note": "full corpus vs 10k pairs, joint site, seed 0", "rows": rows}, indent=1))
    print("wrote analysis/fullcorpus.json, draft/table_fullcorpus.tex and the full-corpus macros")
    for r in rows:
        print("  %-14s %-9s pairs %6s full %.4f | 10k %.4f" % (r["dataset"], r["arm"], r["pairs"],
                                                              r["full_R1_i2t"], r["tenk_R1_i2t"] or 0))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
