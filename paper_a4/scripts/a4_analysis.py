# -*- coding: utf-8 -*-
"""A4 analysis: redundancy, readout dependence and predictive validity of gap metrics."""
from __future__ import annotations
import io, json, os, statistics as st
import numpy as np
from scipy.stats import spearmanr

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
R = os.path.join(REPO, "outputs", "a4", "a4_readouts_2026-11-09.json")
OUT = os.path.join(REPO, "outputs", "a4", "a4_analysis_2026-11-09.json")


def spearman(a, b):
    a = np.asarray(a, float); b = np.asarray(b, float)
    m = np.isfinite(a) & np.isfinite(b)
    if m.sum() < 3 or a[m].std() == 0 or b[m].std() == 0:
        return {"rho": None, "p": None, "n": int(m.sum())}
    r = spearmanr(a[m], b[m])
    return {"rho": float(r.correlation), "p": float(r.pvalue), "n": int(m.sum())}


def get(row, cond, key):
    v = row.get(cond, {}).get(key)
    return float(v) if isinstance(v, (int, float)) else None


def main():
    d = json.load(io.open(R, encoding="utf-8"))
    rows = []
    for key, v in d.items():
        enc, ds = key.split("__")
        rows.append({"cell": key, "encoder": enc, "dataset": ds, "kind": v["kind"]})
    # gap values under conditions
    for cond in ("original", "mean_center", "gap_project", "random_project"):
        for r in rows:
            src = d[r["cell"]][cond]
            for k in ("CG", "DG", "spec_eff_rank", "spec_top1_share"):
                r[cond + "_" + k] = src["gap"][k]
    # readouts under conditions
    readout_keys = ["classification_top1", "R1_i2t", "R1_t2i", "R5_i2t", "ARI", "mixed_R1"]
    for cond in ("original", "mean_center", "gap_project", "random_project"):
        for r in rows:
            src = d[r["cell"]][cond]
            for k in readout_keys:
                r[cond + "_" + k] = src.get(k)
    out = {"n_cells": len(rows), "cells": rows}

    # C1 redundancy
    cg = [r["original_CG"] for r in rows]; dg = [r["original_DG"] for r in rows]
    out["C1_original_CG_DG_spearman"] = spearman(cg, dg)
    out["C1_original_CG_DG_pearson"] = {"r": float(np.corrcoef(cg, dg)[0, 1]), "n": len(rows)}
    for cond in ("mean_center", "gap_project", "random_project"):
        out["C1_%s_CG_DG_spearman" % cond] = spearman([r[cond + "_CG"] for r in rows], [r[cond + "_DG"] for r in rows])
    out["C1_cg_dg_ratio_by_condition"] = {}
    for cond in ("original", "mean_center", "gap_project", "random_project"):
        c = np.asarray([r[cond + "_CG"] for r in rows]); g = np.asarray([r[cond + "_DG"] for r in rows])
        out["C1_cg_dg_ratio_by_condition"][cond] = {"CG_mean": float(c.mean()), "DG_mean": float(g.mean()),
                                                   "CG_over_DG": float(c.mean() / max(g.mean(), 1e-12))}

    # C2 intervention effects: mean change relative to original
    out["C2_effect_means"] = {}
    for cond in ("mean_center", "gap_project", "random_project"):
        eff = {}
        for k in readout_keys:
            vals = [r[cond + "_" + k] - r["original_" + k] for r in rows
                    if r[cond + "_" + k] is not None and r["original_" + k] is not None]
            if vals:
                eff[k] = {"mean": float(st.mean(vals)), "sd": float(st.stdev(vals)) if len(vals) > 1 else 0.0, "n": len(vals)}
        out["C2_effect_means"][cond] = eff
    # counts of direction by dataset kind
    out["C2_direction_counts"] = {}
    for kind in ("class", "caption"):
        for cond in ("mean_center", "gap_project", "random_project"):
            sub = [r for r in rows if r["kind"] == kind]
            cnt = {}
            for k in readout_keys:
                vals = [r[cond + "_" + k] - r["original_" + k] for r in sub
                        if r[cond + "_" + k] is not None and r["original_" + k] is not None]
                if vals:
                    cnt[k] = {"n": len(vals), "improved": int(sum(v > 0 for v in vals)), "worse": int(sum(v < 0 for v in vals))}
            out["C2_direction_counts"]["%s__%s" % (kind, cond)] = cnt

    # C3 predictive validity of gap metrics for readouts (across cells, per kind)
    out["C3_predictive_spearman"] = {}
    for kind in ("class", "caption"):
        sub = [r for r in rows if r["kind"] == kind]
        for metric in ("CG", "DG", "spec_eff_rank", "spec_top1_share"):
            for target in ("classification_top1", "R1_i2t", "R1_t2i", "ARI"):
                a = [r["original_" + metric] for r in sub]
                b = [r["original_" + target] for r in sub]
                out["C3_predictive_spearman"]["%s__%s__%s" % (kind, metric, target)] = spearman(a, b)

    # C4 readout rank agreement (class cells: classification vs retrieval vs ARI; all cells: i2t vs t2i)
    out["C4_readout_rank_agreement"] = {}
    for kind in ("class", "caption"):
        sub = [r for r in rows if r["kind"] == kind]
        pairs = [("classification_top1", "R1_i2t"), ("classification_top1", "R1_t2i"),
                 ("R1_i2t", "R1_t2i"), ("R1_i2t", "ARI"), ("R1_t2i", "ARI")]
        for a, b in pairs:
            if a == "classification_top1" and kind != "class": continue
            out["C4_readout_rank_agreement"]["%s__%s__%s" % (kind, a, b)] = spearman(
                [r["original_" + a] for r in sub if r["original_" + a] is not None and r["original_" + b] is not None],
                [r["original_" + b] for r in sub if r["original_" + a] is not None and r["original_" + b] is not None])

    json.dump(out, io.open(OUT, "w", encoding="utf-8"), indent=1)

    # markdown summary
    lines = ["# A4 readout-validity results (2026-11-09)", "",
             "Cells: %d (5 encoders x 6 datasets; class datasets: DTD, iNat, NKSID; caption: marine, COCO-5K, Flickr30K)." % len(rows), "",
             "## C1: CG/DG redundancy", ""]
    lines.append("- original cells: Spearman rho = %.3f (n=%d)" % (out["C1_original_CG_DG_spearman"]["rho"], out["C1_original_CG_DG_spearman"]["n"]))
    for cond in ("mean_center", "gap_project", "random_project"):
        s = out["C1_%s_CG_DG_spearman" % cond]
        lines.append("- %s: CG/DG rho = %.3f; mean CG/DG = %.3f" % (cond, s["rho"], out["C1_cg_dg_ratio_by_condition"][cond]["CG_over_DG"]))
    lines += ["", "## C2: intervention effects (mean change vs original)", ""]
    for cond in ("mean_center", "gap_project", "random_project"):
        lines.append("**%s**" % cond)
        for k, v in out["C2_effect_means"][cond].items():
            lines.append("- %s: %+.2f (sd %.2f, n=%d)" % (k, v["mean"], v["sd"], v["n"]))
        lines.append("")
    lines += ["## C3: predictive Spearman (across cells) — selected", ""]
    for key, v in out["C3_predictive_spearman"].items():
        if v["rho"] is not None and abs(v["rho"]) >= 0.4:
            lines.append("- %s: rho = %+.3f (n=%d)" % (key, v["rho"], v["n"]))
    lines += ["", "## C4: readout rank agreement — selected", ""]
    for key, v in out["C4_readout_rank_agreement"].items():
        if v["rho"] is not None:
            lines.append("- %s: rho = %+.3f (n=%d)" % (key, v["rho"], v["n"]))
    io.open(os.path.join(REPO, "outputs", "a4", "A4_RESULTS_2026-11-09.md"), "w", encoding="utf-8", newline="").write("\n".join(lines) + "\n")
    print("wrote", OUT)
    print("\n".join(lines[:40]))


if __name__ == "__main__":
    main()
