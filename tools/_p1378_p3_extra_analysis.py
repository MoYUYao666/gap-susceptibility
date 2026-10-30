# -*- coding: utf-8 -*-
r"""P3: analyse the extended current-protocol runs (intermediate ranks, second seed) and the local Qwen2-VL-2B check.

Reads p3_rerun_protocol.json, p3_rerun_extra.json and (if present) p3_qwen2b_crossing.json, computes
- the current-protocol crossing over ranks 5, 6, 7, 8, 10, 16 (seed 42 where available),
- the seed-consistency of the sign at r=5 and r=6 (seed 42 and seed 123),
- an exact two-sided permutation test on the r=5 vs r=6 difference (n=2+2; the smallest attainable p is 1/6),
and writes outputs/analysis/p3_rerun_analysis.json.

    python tools/_p1378_p3_extra_analysis.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import os

import numpy as np

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = os.path.join(REPO, "outputs", "analysis", "p3_rerun_protocol.json")
EXTRA = os.path.join(REPO, "outputs", "analysis", "p3_rerun_extra.json")
QWEN = os.path.join(REPO, "outputs", "analysis", "p3_qwen2b_crossing_fixed.json")
QWEN_OLD = os.path.join(REPO, "outputs", "analysis", "p3_qwen2b_crossing.json")
OUT = os.path.join(REPO, "outputs", "analysis", "p3_rerun_analysis.json")


def load(p):
    return json.load(io.open(p, encoding="utf-8")) if os.path.exists(p) else None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    runs = {}
    for src in (BASE, EXTRA):
        d = load(src)
        if d:
            runs.update({k: {"rank": v["rank"], "seed": v["seed"], "E": v["E"], "delta_E": v["delta_E"]}
                         for k, v in d["runs"].items() if v.get("ok")})
    by_rank = {}
    for k, v in sorted(runs.items()):
        by_rank.setdefault(v["rank"], []).append(v)
    curve = {}
    for rank, vs in sorted(by_rank.items()):
        s42 = next((x for x in vs if x["seed"] == 42), None)
        curve[rank] = {"E_seed42": s42["E"] if s42 else None,
                       "dE_seed42": s42["delta_E"] if s42 else None,
                       "dE_other_seeds": [x["delta_E"] for x in vs if x["seed"] != 42]}
    neg = [r for r in sorted(by_rank) if curve[r]["dE_seed42"] is not None and curve[r]["dE_seed42"] < 0]
    pos = [r for r in sorted(by_rank) if curve[r]["dE_seed42"] is not None and curve[r]["dE_seed42"] > 0]
    bracket = [max(neg), min(pos)] if neg and pos else None

    # exact permutation test r=5 vs r=6 over the available seeds
    r5 = [v["delta_E"] for v in by_rank.get(5, [])]
    r6 = [v["delta_E"] for v in by_rank.get(6, [])]
    perm = {"r5": r5, "r6": r6}
    if r5 and r6:
        pooled = r5 + r6
        obs = abs(float(np.mean(r5)) - float(np.mean(r6)))
        n5 = len(r5)
        cnt = 0
        tot = 0
        from itertools import combinations
        for idx in combinations(range(len(pooled)), n5):
            g1 = [pooled[i] for i in idx]
            g2 = [pooled[i] for i in range(len(pooled)) if i not in idx]
            tot += 1
            if abs(float(np.mean(g1)) - float(np.mean(g2))) >= obs - 1e-12:
                cnt += 1
        perm.update({"observed_diff": obs, "p_two_sided": cnt / tot, "assignments": tot,
                     "min_attainable_p": 1.0 / tot, "n_seeds": [len(r5), len(r6)]})

    qwen = load(QWEN) or load(QWEN_OLD)
    qwen_summary = None
    if qwen:
        q = qwen["runs"]
        es = {k: tuple(v["E"]) for k, v in q.items() if v.get("ok")}
        distinct = len({e for e in es.values()}) == len(es)
        trs = [q[k].get("trainable_M") for k in q]
        rank_varied = len({t for t in trs if t is not None}) > 1
        qwen_summary = {k: {"E": q[k]["E"], "delta_E": q[k]["delta_E"], "ok": q[k]["ok"],
                            "trainable_M": q[k].get("trainable_M")} for k in q}
        qwen_summary["valid"] = bool(distinct and (rank_varied or len(q) == 1))
        qwen_summary["note"] = ("" if qwen_summary["valid"] else
                                "trajectories coincide across ranks; the check is inconclusive and is not used as evidence")

    out = {"curve": curve, "bracket_seed42": bracket, "permutation": perm, "qwen2b": qwen_summary}
    print("  current-protocol curve (seed 42):")
    for rank in sorted(by_rank):
        print(f"   r={rank:>2}: ΔE={curve[rank]['dE_seed42']}  other seeds={curve[rank]['dE_other_seeds']}")
    print("  bracket (seed 42):", bracket)
    if perm.get("p_two_sided") is not None:
        print(f"  permutation r5 vs r6: diff={perm['observed_diff']:.1f}, p={perm['p_two_sided']:.3f} "
              f"({perm['assignments']} assignments; min attainable {perm['min_attainable_p']:.2f})")
    if qwen_summary:
        print("  qwen2b:", qwen_summary)
    if a.apply:
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(out, indent=1))
        print("  wrote", os.path.relpath(OUT, REPO))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
