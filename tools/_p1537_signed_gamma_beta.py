# -*- coding: utf-8 -*-
r"""Signed-Gamma and beta sensitivity of the allocation rule (B3).

Uses the archived CLIP per-block Gamma (signed) and compares the paper's absolute-value rule with a signed rule
rank_k ~ exp(-beta * Gamma_k), over a beta grid.

    python tools/_p1537_signed_gamma_beta.py
"""
from __future__ import annotations

import io
import json
import os

import numpy as np

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AN = os.path.join(REPO, "outputs", "analysis")
OUT = os.path.join(AN, "p3_signed_gamma_beta.json")
BUDGET = 16
BLOCKS = ["vision", "text_shallow", "text_mid", "text_deep"]
BETAS = [0.05, 0.1, 0.2, 0.5, 1.0, 2.0]


def alloc_from(weights):
    w = np.array([max(float(weights[k]), 1e-12) for k in BLOCKS])
    share = w / w.sum()
    ranks = np.maximum(1, np.round(share * BUDGET)).astype(int)
    while ranks.sum() > BUDGET:
        i = int(np.argmax(ranks))
        if ranks[i] > 1:
            ranks[i] -= 1
        else:
            break
    while ranks.sum() < BUDGET:
        i = int(np.argmin(share * BUDGET - ranks))
        ranks[i] += 1
    return {k: int(v) for k, v in zip(BLOCKS, ranks)}, share


def main() -> int:
    g = json.load(io.open(os.path.join(AN, "p3d_gamma_real_vs_blank.json"), encoding="utf-8"))
    gamma = {k: float(g["conditions"]["real"]["blocks"][k]["gamma"]) for k in BLOCKS}
    absg = {k: abs(v) for k, v in gamma.items()}
    gnorm = {k: v / max(absg.values()) for k, v in gamma.items()}
    out = {"meta": {"script": "tools/_p1537_signed_gamma_beta.py", "task": "B3 signed-Gamma / beta sensitivity",
                    "budget": BUDGET, "gamma": gamma},
           "abs_rule": alloc_from(absg)[0],
           "signed_rules": {}, "beta_grid": BETAS}
    for beta in BETAS:
        w = {k: float(np.exp(-beta * gnorm[k])) for k in BLOCKS}
        ranks, share = alloc_from(w)
        out["signed_rules"][str(beta)] = {"ranks": ranks, "weights": w}
        print(f"  beta={beta}: signed ranks {ranks}")
    # beta sensitivity of the absolute rule (temperature does not change the ordering)
    abs_rules = {}
    for beta in BETAS:
        w = {k: float(np.exp(-beta * (absg[k] / max(absg.values())))) for k in BLOCKS}
        abs_rules[str(beta)] = alloc_from(w)[0]
    out["abs_beta_grid"] = abs_rules
    print("  abs rule:", out["abs_rule"], "| abs beta grid:", abs_rules)
    json.dump(out, io.open(OUT, "w", encoding="utf-8"), indent=1)
    print("wrote", os.path.relpath(OUT, REPO))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
