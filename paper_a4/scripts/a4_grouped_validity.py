# -*- coding: utf-8 -*-
"""A4 grouped held-out validity: leave-one-dataset/encoder-out linear prediction."""
from __future__ import annotations
import io, json, os
import numpy as np
from scipy.stats import spearmanr, pearsonr

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
A = json.load(io.open(os.path.join(REPO, "outputs", "a4", "a4_analysis_2026-11-09.json"), encoding="utf-8"))
rows = A["cells"]; OUT = os.path.join(REPO, "outputs", "a4", "a4_grouped_validity_2026-11-09.json")


def fit_predict(x, y):
    x = np.asarray(x, float); y = np.asarray(y, float)
    A_ = np.column_stack([np.ones(len(x)), x])
    beta, *_ = np.linalg.lstsq(A_, y, rcond=None)
    return A_ @ beta, beta


def cv(rows, metric, target, group):
    xs = [r["original_" + metric] for r in rows]; ys = [r["original_" + target] for r in rows]
    groups = [r[group] for r in rows]
    pred = np.full(len(xs), np.nan)
    for g in sorted(set(groups)):
        te = np.array([gg == g for gg in groups]); tr = ~te
        if tr.sum() < 3 or te.sum() == 0: continue
        _, beta = fit_predict(np.asarray(xs)[tr], np.asarray(ys)[tr])
        xte = np.asarray(xs)[te]
        pred[te] = beta[0] + beta[1] * xte
    ok = np.isfinite(pred)
    if ok.sum() < 3: return None
    rr = pearsonr(pred[ok], np.asarray(ys)[ok])[0]
    ss_res = ((np.asarray(ys)[ok] - pred[ok]) ** 2).sum()
    ss_tot = ((np.asarray(ys)[ok] - np.asarray(ys)[ok].mean()) ** 2).sum()
    r2 = 1 - ss_res / ss_tot if ss_tot else None
    return {"pearson": float(rr), "r2": float(r2) if r2 is not None else None,
            "spearman": float(spearmanr(pred[ok], np.asarray(ys)[ok]).correlation), "n": int(ok.sum())}


out = {}
for kind in ("class", "caption"):
    sub = [r for r in rows if r["kind"] == kind]
    targets = ["classification_top1", "R1_i2t", "R1_t2i", "ARI"] if kind == "class" else ["R1_i2t", "R1_t2i"]
    for metric in ("CG", "DG", "spec_eff_rank", "spec_top1_share"):
        for target in targets:
            for group in ("dataset", "encoder"):
                key = "%s__%s__%s__%s" % (kind, metric, target, group)
                out[key] = cv(sub, metric, target, group)
# all cells, retrieval target
for metric in ("CG", "DG", "spec_eff_rank", "spec_top1_share"):
    for target in ("R1_i2t", "R1_t2i"):
        for group in ("dataset", "encoder"):
            out["all__%s__%s__%s" % (metric, target, group)] = cv(rows, metric, target, group)
json.dump(out, io.open(OUT, "w", encoding="utf-8"), indent=1)
for k, v in out.items():
    if v: print(k, "r2=%.3f pearson=%.3f rho=%.3f n=%d" % (v["r2"], v["pearson"], v["spearman"], v["n"]))
