# -*- coding: utf-8 -*-
r"""核 task-7 最终表（19 runs / 7 lr）与"无内部极小值"的主张（2026-10-12）。

## 队友最终表（ddof=1）

| lr | n | zero-shot % | ΔCG | R@1 |
|---|---|---|---|---|
| 1e-07 | 2 | 60.52 ± 0.02 | −0.0058 ± 0.0004 | 0.1760 |
| 3e-07 | 2 | 61.07 ± 0.01 | −0.0069 ± 0.0012 | 0.1782 |
| 1e-06 | 3 | 60.87 ± 0.21 | −0.0016 ± 0.0052 | 0.1808 |
| 1e-05 | 3 | 52.18 ± 1.03 | +0.1860 ± 0.0047 | 0.1700 |
| 3e-05 | 3 | 29.72 ± 1.50 | +0.2531 ± 0.0029 | 0.1508 |
| 1e-04 | 3 | 2.63 ± 2.17 | +0.4416 ± 0.3077 | 0.0448 |
| 3e-04 | 3 | 0.10 ± 0.03 | +0.1545 ± 0.8551 | 0.0010 |

    python tools\_p402_verify_final_lr_table.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import statistics
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
FULL = REPO / "outputs" / "analysis" / "pr_fullft_lr_sweep_full.json"
OUT = REPO / "outputs" / "analysis" / "final_lr_table_verified.json"
CG_FROZEN = 0.8157


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    d = json.loads(io.open(FULL, encoding="utf-8", errors="replace").read())
    a_ = d.get("analysis", {})
    print("=" * 100)
    print("① 合并文件自带的 per_lr 统计（队友渲染的来源）")
    print("=" * 100)
    per = a_.get("per_lr", {})
    for lr in sorted(per, key=lambda x: float(x)):
        v = per[lr]
        print(f"  lr={lr:<8} n={v.get('n_seeds')}  "
              f"zero-shot {v.get('zero_shot_top1_pct_mean')} ± {v.get('zero_shot_top1_pct_sd')} ｜ "
              f"ΔCG {v.get('dCG_mean')} ± {v.get('dCG_sd')} ｜ R@1 {v.get('R@1_mean_of_runs')}")
        print(f"        ΔCG 逐 seed = {v.get('dCG_values')}")

    print()
    print("=" * 100)
    print("② 我独立从 runs 重算（冻结基准 0.8157），并给 ddof=0 与 ddof=1")
    print("=" * 100)
    from collections import defaultdict
    g = defaultdict(list)
    for r in d.get("runs", []):
        f = r.get("final") or {}
        cg = f.get("CG")
        zs = f.get("zero_shot_imagenet1k_top1_pct")
        if cg is None:
            continue
        g[str(r.get("lr"))].append({"seed": r.get("seed"), "dcg": cg - CG_FROZEN, "zs": zs,
                                    "cg": cg, "dg": f.get("DG")})
    ok_all = True
    for lr in sorted(g, key=lambda x: float(x)):
        vals = [x["dcg"] for x in g[lr]]
        n = len(vals)
        sd0 = statistics.pstdev(vals) if n > 1 else None
        sd1 = statistics.stdev(vals) if n > 1 else None
        m = statistics.mean(vals)
        print(f"  lr={lr:<8} n={n}  ΔCG={m:+.4f} ｜ ddof=0 sd={None if sd0 is None else round(sd0,4)} "
              f"｜ ddof=1 sd={None if sd1 is None else round(sd1,4)}")
        print(f"        逐 seed: {[(x['seed'], round(x['dcg'],4), round(x['zs'],2) if x['zs'] is not None else None) for x in g[lr]]}")

    print()
    print("=" * 100)
    print("③ 核「无内部极小值」与「平台略负」")
    print("=" * 100)
    order = sorted(g, key=lambda x: float(x))
    means = [(lr, statistics.mean([x["dcg"] for x in g[lr]])) for lr in order]
    print("  ΔCG 随 lr 序列：")
    for lr, m in means:
        print(f"     lr={lr:<8} {m:+.4f}")
    neg = [m for _, m in means if m < 0]
    print(f"  → 负值点数 {len(neg)}（应集中在 lr ≤ 1e-6）")
    print(f"  → 符号翻转发生在 1e-6({means[2][1]:+.4f}) 与 1e-5({means[3][1]:+.4f}) 之间："
          f"{'✅' if means[2][1] < 0 < means[3][1] else '🔴'}")
    # 内部极小值 = 序列里某点小于其两侧邻点（且非端点）
    interior = []
    for i in range(1, len(means) - 1):
        if means[i][1] < means[i-1][1] and means[i][1] < means[i+1][1]:
            interior.append(means[i])
    print(f"  → 内部极小值：{interior if interior else '无 ✅（与队友主张一致）'}")

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(
            {"per_lr": {lr: {"n": len(g[lr]),
                             "dcg_mean": round(statistics.mean([x["dcg"] for x in g[lr]]), 6),
                             "dcg_sd_ddof0": (round(statistics.pstdev([x["dcg"] for x in g[lr]]), 6)
                                              if len(g[lr]) > 1 else None),
                             "dcg_sd_ddof1": (round(statistics.stdev([x["dcg"] for x in g[lr]]), 6)
                                              if len(g[lr]) > 1 else None),
                             "values": [round(x["dcg"], 4) for x in g[lr]]}
                         for lr in g},
             "interior_minima": [list(x) for x in interior]},
            ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
