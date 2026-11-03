# -*- coding: utf-8 -*-
r"""核 model-coverage 的两条新主张 + 处理"子集命中"的统计虚假问题（2026-10-12）。

## 待核

1. **我的舍入错**：`strict_freeze_rank/r4/both` 的 3-seed 均值 0.6796667
   → `round(...,3)` = **0.680**，只有**截断**才是 0.679。**若成立，我 caption 里那句要改。**
2. **他说"真正的命中者是 `strict_freeze_b32_r4/both` 的 seeds 42/123/456"** →
   需要实测该目录逐 seed 值。
3. **他说"允许 size 3–5 的 seed 子集后，三格全部可达"** →
   ⚠️ **这个推理有统计陷阱**：94 个组 × 每组 C(5,3)=10 个 3-seed 子集 ≈ **940 个候选**，
   在 0.001 网格上**必然**能碰到任何三位小数。**必须用置换/覆盖率检验判断这是否有意义。**

    python tools\_p330_subset_overfit_check.py [--apply]
"""
from __future__ import annotations

import argparse
import glob
import io
import itertools
import json
import random
import statistics
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "outputs" / "analysis" / "subset_overfit_check.json"
TARGETS = {"CLIP_B32_r4/both": 0.679, "CLIP_B16_r4/text_only": 0.651,
           "CLIP_B32_r4/text_only": 0.621}


def group_key(parts):
    arm_i = next((i for i, p in enumerate(parts)
                  if p in ("text_only", "both", "vision_only")), None)
    return "/".join(parts[:arm_i + 1]) if arm_i is not None else "/".join(parts[:-1])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    # 载入所有组
    groups = defaultdict(list)
    for f in glob.glob(str(REPO / "outputs" / "**" / "results.json"), recursive=True):
        try:
            d = json.loads(io.open(f, encoding="utf-8", errors="replace").read())
        except Exception:
            continue
        if "initial_gap" not in d or "final_gap" not in d:
            continue
        v = (d.get("final_task_metrics") or {}).get("R@1")
        if v is None:
            continue
        parts = Path(f).relative_to(REPO).parts[1:-1]
        groups[group_key(parts)].append({
            "R@1": float(v), "seed": str(d.get("seed")),
            "n": d.get("n_trainable_params"),
        })

    print("=" * 104)
    print("① 核我的舍入错：strict_freeze_rank/r4/both 逐 seed")
    print("=" * 104)
    for k in ("strict_freeze_rank/r4/both", "strict_freeze_b32_r4/both",
              "strict_freeze_b16/r4/text_only", "strict_freeze_b32_r4/text_only"):
        vs = groups.get(k, [])
        if not vs:
            print(f"  ⚠️  {k}: 无")
            continue
        vals = sorted((x["R@1"], x["seed"]) for x in vs)
        full = [v for v, _ in vals]
        m = sum(full) / len(full)
        print(f"  {k}")
        print(f"     逐 seed: {[(s, round(v,4)) for v, s in vals]}")
        print(f"     5-seed 均值 = {m:.6f} ｜ round(3)={round(m,3)} ｜ trunc(3)={int(m*1000)/1000}")
        # 所有 3-seed 子集
        subs = []
        for c in itertools.combinations(range(len(full)), 3):
            sm = sum(full[i] for i in c) / 3
            subs.append((sm, [vals[i][1] for i in c]))
        subs.sort()
        print(f"     3-seed 子集（{len(subs)} 个）均值范围: {subs[0][0]:.6f} … {subs[-1][0]:.6f}")
        for tgt in (0.679, 0.680, 0.651, 0.621):
            hit_r = [s for s in subs if round(s[0], 3) == tgt]
            hit_t = [s for s in subs if int(s[0] * 1000) / 1000 == tgt]
            if hit_r or hit_t:
                print(f"       目标 {tgt}: round 命中 {len(hit_r)} ｜ trunc 命中 {len(hit_t)}"
                      + (f" 例: {[round(s[0],6) for s in (hit_r or hit_t)][:3]}" if (hit_r or hit_t) else ""))

    print()
    print("=" * 104)
    print("② 统计检验：「3-seed 子集命中」是否只是必然的巧合？")
    print("=" * 104)
    # 收集所有 3-seed 子集均值，看它们覆盖多少不同的三位小数值
    all_sub_means = []
    for k, vs in groups.items():
        vals = [x["R@1"] for x in vs]
        if len(vals) < 3:
            continue
        for c in itertools.combinations(vals, 3):
            all_sub_means.append(sum(c) / 3)
    n_cand = len(all_sub_means)
    rounded = {round(m, 3) for m in all_sub_means}
    print(f"  全部 3-seed 子集候选数 = {n_cand}")
    print(f"  它们四舍五入后覆盖的不同三位小数值 = {len(rounded)} 个")
    lo, hi = min(all_sub_means), max(all_sub_means)
    print(f"  取值范围 = [{lo:.4f}, {hi:.4f}]（跨度 {hi-lo:.4f}）")
    span_bins = int((hi - lo) * 1000)
    print(f"  → 该跨度上共有 {span_bins} 个三位小数格；候选数 {n_cand} 个")
    print(f"  → 期望覆盖 {min(span_bins, n_cand)} 格；实际覆盖 {len(rounded)} 格")
    for tgt in (0.679, 0.651, 0.621):
        hit = [m for m in all_sub_means if round(m, 3) == tgt]
        print(f"    目标 {tgt}: {len(hit)} 个候选命中 "
              f"（占候选 {100*len(hit)/max(1,n_cand):.2f}%）")
    print("  ⚠️ 判读：若命中数远高于「1 个格的概率」，说明子集命中是**必然巧合**，")
    print("     不构成「该数字有来源」的证据。")

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(
            {"n_candidates": n_cand, "n_rounded_values": len(rounded),
             "range": [lo, hi],
             "hits": {str(t): len([m for m in all_sub_means if round(m, 3) == t])
                      for t in (0.679, 0.651, 0.621)}},
            ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
