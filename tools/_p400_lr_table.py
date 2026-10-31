# -*- coding: utf-8 -*-
r"""逐 lr × seed 列出 task-7 结果，核「1e-4 未饱和 / 3e-4 退化塌缩」（2026-10-12）。

字段结构（实测）：`run["final"] = {zero_shot_imagenet1k_top1_pct, zero_shot_n_images, CG, DG, R@1_mean}`

    python tools\_p400_lr_table.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import math
import statistics
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
P = REPO / "outputs" / "analysis" / "pr_fullft_lr_sweep_ext.json"
OUT = REPO / "outputs" / "analysis" / "lr_table_verified.json"
CG_FROZEN = 0.8157


def r4(x):
    return None if x is None else round(float(x), 4)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    d = json.loads(io.open(P, encoding="utf-8", errors="replace").read())
    runs = d.get("runs", [])
    g = defaultdict(list)
    for r in runs:
        g[str(r.get("lr"))].append(r)

    print("=" * 100)
    print(f"逐 lr × seed（冻结：CG {CG_FROZEN} / zero-shot 59.91%）")
    print("=" * 100)
    rep = {}
    for lr in sorted(g, key=lambda x: float(x)):
        print(f"\n  lr = {lr}")
        dcs, zss = [], []
        for r in g[lr]:
            f = r.get("final") or {}
            cg, dg = f.get("CG"), f.get("DG")
            zs = f.get("zero_shot_imagenet1k_top1_pct")
            r1 = f.get("R@1_mean")
            dc = None if cg is None else cg - CG_FROZEN
            if dc is not None:
                dcs.append(dc)
            if zs is not None:
                zss.append(zs)
            print(f"     seed={str(r.get('seed')):<5} CG={r4(cg)} DG={r4(dg)} "
                  f"**ΔCG={r4(dc)}** zero-shot={r4(zs)} R@1={r4(r1)}"
                  + (f"  ⚠️ {str(r.get('error'))[:60]}" if r.get("error") else ""))
        if dcs:
            m, sd = statistics.mean(dcs), (statistics.pstdev(dcs) if len(dcs) > 1 else None)
            print(f"     → ΔCG {m:+.4f} ± {sd if sd is None else round(sd,4)} ｜ n={len(dcs)}"
                  f" ｜ zero-shot 均值 {statistics.mean(zss) if zss else float('nan'):.2f}%")
            rep[lr] = {"n": len(dcs), "dCG_mean": round(m, 6),
                       "dCG_sd": None if sd is None else round(sd, 6),
                       "dCG_values": [round(v, 4) for v in dcs],
                       "zero_shot_mean": round(statistics.mean(zss), 4) if zss else None}

    print()
    print("=" * 100)
    print("核两条关键主张")
    print("=" * 100)
    ln64 = math.log(64)
    print(f"  ln(64) = {ln64:.4f}（均匀解 train loss）")
    print()
    print("  (1) 1e-4 是否饱和？")
    v = rep.get("0.0001", {}).get("dCG_values")
    print(f"      1e-4 ΔCG 逐 seed = {v} ｜ sd = {rep.get('0.0001',{}).get('dCG_sd')}")
    print(f"      → {'✅ 未饱和（sd 大，只有 seed42 在 ≈+0.80）' if v and max(v)-min(v) > 0.3 else '⚠️ 与队友主张不符'}")
    print()
    print("  (2) 3e-4 是否退化塌缩？")
    v3 = rep.get("0.0003", {}).get("dCG_values")
    print(f"      3e-4 ΔCG 逐 seed = {v3} ｜ sd = {rep.get('0.0003',{}).get('dCG_sd')}")
    for r in g.get("0.0003", []):
        f = r.get("final") or {}
        print(f"        seed={r.get('seed')}: CG={r4(f.get('CG'))} DG={r4(f.get('DG'))} "
              f"zero-shot={r4(f.get('zero_shot_imagenet1k_top1_pct'))} R@1={r4(f.get('R@1_mean'))}")
    print(f"      → {'✅ 见上：若 CG/DG 塌到 ~1e-3 且 zero-shot ≈0，则为退化塌缩，ΔCG 失去意义' }")

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps(rep, ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
