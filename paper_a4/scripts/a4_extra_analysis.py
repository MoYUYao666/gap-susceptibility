# -*- coding: utf-8 -*-
"""Summarise the additional A4 robustness experiments (methods, retrieval, SigLIP, rank sensitivity)."""
from __future__ import annotations
import glob, io, json, os
import numpy as np
from scipy.stats import spearmanr

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(REPO, "outputs", "a4", "a4_extra_analysis_2026-11-10.json")
BLOCKS = {
    "methods": os.path.join(REPO, "outputs", "a4", "extra", "methods", "summary.json"),
    "retrieval": os.path.join(REPO, "outputs", "a4", "extra", "retrieval", "summary.json"),
    "siglip": os.path.join(REPO, "outputs", "a4", "extra", "siglip", "summary.json"),
    "rank_b32": os.path.join(REPO, "outputs", "a4", "extra", "rank_b32", "summary.json"),
    "rank_b16": os.path.join(REPO, "outputs", "a4", "extra", "rank_b16", "summary.json"),
}


def sp(a, b):
    a = np.asarray(a, float); b = np.asarray(b, float); m = np.isfinite(a) & np.isfinite(b)
    if m.sum() < 3 or np.std(a[m]) == 0 or np.std(b[m]) == 0: return None
    return float(spearmanr(a[m], b[m]).correlation)


def flatten(path):
    if not os.path.exists(path): return []
    d = json.load(io.open(path, encoding="utf-8"))
    rows = []
    for run in d.get("runs", []):
        m = run["run"]
        for e in run.get("epochs", []):
            r = {"backbone": m.get("backbone"), "dataset": m.get("dataset"), "rank": m.get("rank"),
                 "seed": m.get("seed"), "method": m.get("method", "lora"), "tower": m.get("tower", "both"),
                 "epoch": e["epoch"]}
            for cond, metrics in e["conditions"].items():
                for k, v in metrics.items(): r["%s_%s" % (cond, k)] = v
            rows.append(r)
    return rows


def main():
    out = {}
    for name, path in BLOCKS.items():
        rows = flatten(path)
        if not rows: continue
        orig = rows
        b = {"n_runs": len(set((r["backbone"], r["dataset"], r["rank"], r["seed"], r["method"], r["tower"]) for r in orig)),
             "n_checkpoints": len(orig)}
        for key in ("corpus",):
            pass
        b["rho_CG_DG"] = sp([r.get("original_CG") for r in orig], [r.get("original_DG") for r in orig])
        b["effects"] = {}
        for cond in ("mean_center", "gap_project", "random_project"):
            for k in ("classification_top1", "R1_i2t", "R1_t2i", "ARI"):
                vals = [r.get(cond + "_" + k) - r.get("original_" + k) for r in orig
                        if r.get(cond + "_" + k) is not None and r.get("original_" + k) is not None]
                if vals: b["effects"]["%s__%s" % (cond, k)] = {"mean": float(np.mean(vals)), "sd": float(np.std(vals)), "n": len(vals)}
        b["predictive"] = {}
        for m in ("CG", "DG", "spec_eff_rank", "spec_top1_share"):
            for t in ("classification_top1", "R1_i2t", "R1_t2i", "ARI"):
                rr = sp([r.get("original_" + m) for r in orig], [r.get("original_" + t) for r in orig])
                if rr is not None: b["predictive"]["%s__%s" % (m, t)] = rr
        b["means"] = {}
        for k in ("original_CG", "original_DG", "original_spec_eff_rank", "original_R1_i2t", "original_R1_t2i",
                  "original_R1_i2t", "original_classification_top1", "original_ARI"):
            vals = [r.get(k) for r in orig if r.get(k) is not None]
            if vals: b["means"][k] = float(np.mean(vals))
        out[name] = b
    json.dump(out, io.open(OUT, "w", encoding="utf-8"), indent=1)
    lines = ["# A4 additional robustness experiments (2026-11-10)", ""]
    for name, b in out.items():
        lines.append("## %s" % name); lines.append("- runs: %d; checkpoints: %d" % (b["n_runs"], b["n_checkpoints"]))
        lines.append("- CG/DG rho: %s" % (b["rho_CG_DG"] if b["rho_CG_DG"] is not None else "NA"))
        for k, v in b["means"].items(): lines.append("- %s: %.3f" % (k, v))
        for k, v in b["effects"].items(): lines.append("- %s: %+.2f (sd %.2f, n=%d)" % (k, v["mean"], v["sd"], v["n"]))
        for k, v in b["predictive"].items(): lines.append("- rho %s: %+.2f" % (k, v))
        lines.append("")
    io.open(os.path.join(REPO, "outputs", "a4", "A4_EXTRA_RESULTS_2026-11-10.md"), "w", encoding="utf-8", newline="").write("\n".join(lines) + "\n")
    print("wrote", OUT)


if __name__ == "__main__":
    main()
