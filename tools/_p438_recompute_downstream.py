# -*- coding: utf-8 -*-
r"""独立重算 task-10 的核心统计（不信报告，从归档 runs 自己算）（2026-10-12）。

    python tools\_p438_recompute_downstream.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import statistics
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "outputs" / "analysis" / "p3_downstream_recomputed.json"


def spearman(xs, ys):
    def rank(v):
        order = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and v[order[j + 1]] == v[order[i]]:
                j += 1
            avg = (i + j) / 2.0 + 1
            for k in range(i, j + 1):
                r[order[k]] = avg
            i = j + 1
        return r
    rx, ry = rank(xs), rank(ys)
    n = len(xs)
    mx, my = statistics.mean(rx), statistics.mean(ry)
    num = sum((rx[i] - mx) * (ry[i] - my) for i in range(n))
    dx = sum((rx[i] - mx) ** 2 for i in range(n)) ** 0.5
    dy = sum((ry[i] - my) ** 2 for i in range(n)) ** 0.5
    return num / (dx * dy) if dx and dy else float("nan")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    rep = {}

    d = json.loads(io.open(REPO / "outputs/analysis/p3d_clip_ranksweep.json",
                           encoding="utf-8", errors="replace").read())
    runs = d.get("runs") if isinstance(d, dict) else d
    print(f"  runs = {len(runs)}")
    print(f"  键 = {sorted(runs[0].keys())}")
    print()

    # 找出能量与 R@1 字段
    def pick(r, *names):
        for nm in names:
            if nm in r and isinstance(r[nm], (int, float)):
                return r[nm]
        for k, v in r.items():
            for nm in names:
                if k.endswith(nm) and isinstance(v, (int, float)):
                    return v
        return None

    xs, ys, rows = [], [], []
    for r in runs:
        e = pick(r, "dE_test", "delta_E_test", "dE_eval", "dE")
        q = pick(r, "dR1", "delta_R1", "R1_delta")
        if q is None:
            r1 = pick(r, "R@1", "R1")
            q = None if r1 is None else r1 - 0.7058
        if e is None or q is None:
            continue
        xs.append(e)
        ys.append(q)
        rows.append({"cond": r.get("condition"), "n_train": r.get("n_train"),
                     "rank": r.get("rank"), "seed": r.get("seed"),
                     "dE": round(e, 6), "dR1": round(q, 6)})
    print(f"  可用配对 n = {len(xs)}")
    if len(xs) > 2:
        rho = spearman(xs, ys)
        print(f"  **Spearman(ΔE_test, ΔR@1) = {rho:.4f}**（n={len(xs)}）")
        rep["spearman_dE_dR1"] = {"rho": round(rho, 6), "n": len(xs)}
        sub = [(e, q) for e, q in zip(xs, ys) if e < 0]
        sup = [(e, q) for e, q in zip(xs, ys) if e > 0]
        print(f"  ΔE<0：n={len(sub)} 平均 ΔR@1={statistics.mean(q for _, q in sub):+.4f}")
        print(f"  ΔE>0：n={len(sup)} 平均 ΔR@1={statistics.mean(q for _, q in sup):+.4f}")
        rep["dE_neg"] = {"n": len(sub), "mean_dR1": round(statistics.mean(q for _, q in sub), 6)}
        rep["dE_pos"] = {"n": len(sup), "mean_dR1": round(statistics.mean(q for _, q in sup), 6)}

    print()
    print("  极端反例核对（n=1024, r=16）：")
    for cond in ("real", "blank"):
        sel = [x for x in rows if x["cond"] == cond and x["n_train"] == 1024 and x["rank"] == 16]
        for s in sel:
            print(f"     {cond:<6} n={s['n_train']} r={s['rank']} seed={s['seed']} "
                  f"ΔE={s['dE']:+.4f} ΔR@1={s['dR1']:+.4f}")
            rep.setdefault("n1024_r16", []).append(s)

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps(rep, ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
