# -*- coding: utf-8 -*-
r"""候选分析 A：留出检查点检验 + rival baseline（解 FATAL 2）（2026-10-12）。

## 攻击点

论文用**池化** Spearman(τ, top-1)=0.786 声称"秩序保持追踪准确率"，
但**组内** ρ = −0.5（COCO）/ −0.5（Food-101）/ +1.0（DTD）→ **Simpson 悖论**。
且**从未做**留出预测检验，也没有 rival baseline（如 ‖δ‖、gap）。

## 本脚本（**只算，不改论文**）

1. 读 `a1_h_offset.json` 的 `checkpoints`：逐检查点的 (τ, 下游基准 top-1, 数据集)
2. 算**池化**与**组内**相关系数（复现审稿人的 Simpson 结论）
3. **留出检验**：留一数据集，用其余数据集拟合 τ→top-1，预测留出集
4. **rival baseline**：用 (‖δ‖, gap, CG, val_loss) 做同样的留出预测，比 R²
5. 报**每个数字的归档出处**

    python tools\_p206_heldout_checkpoint.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import statistics as st
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "outputs" / "a1_h_offset.json"
SRC2 = REPO / "outputs" / "a1_h_seed_summary.json"
OUT = REPO / "outputs" / "analysis" / "a1_heldout_checkpoint.json"


def pearson(xs, ys):
    n = len(xs)
    if n < 2:
        return float("nan")
    mx, my = st.mean(xs), st.mean(ys)
    num = sum((xs[i] - mx) * (ys[i] - my) for i in range(n))
    den = (sum((x - mx) ** 2 for x in xs) * sum((y - my) ** 2 for y in ys)) ** 0.5
    return num / den if den else float("nan")


def ranks(v):
    s = sorted(range(len(v)), key=lambda i: v[i])
    r = [0.0] * len(v)
    for pos, i in enumerate(s):
        r[i] = pos + 1
    return r


def spearman(xs, ys):
    if len(xs) < 2:
        return float("nan")
    return pearson(ranks(xs), ranks(ys))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    d = json.loads(io.open(SRC, encoding="utf-8", errors="replace").read())
    print("=" * 88)
    print("① a1_h_offset.json 结构")
    print("=" * 88)
    for k in sorted(d):
        v = d[k]
        if isinstance(v, dict):
            print(f"  {k:<26} dict 键: {list(v.keys())[:10]}")
        elif isinstance(v, list):
            print(f"  {k:<26} list[{len(v)}]  例: {json.dumps(v[:1], ensure_ascii=False)[:180]}")
        else:
            print(f"  {k:<26} {str(v)[:100]}")

    print()
    print("=" * 88)
    print("② checkpoints 逐条（这就是「七个检查点」的来源）")
    print("=" * 88)
    cps = d.get("checkpoints")
    if isinstance(cps, dict):
        rows = []
        for name, v in cps.items():
            if isinstance(v, dict):
                rows.append((name, v))
                print(f"  {name:<34} {json.dumps(v, ensure_ascii=False)[:200]}")
        print(f"  → 共 {len(rows)} 个检查点")
    elif isinstance(cps, list):
        for v in cps:
            print(f"  {json.dumps(v, ensure_ascii=False)[:220]}")
        print(f"  → 共 {len(cps)} 个检查点")
    else:
        print(f"  （{type(cps).__name__}）{str(cps)[:200]}")

    print()
    print("=" * 88)
    print("③ 已有的 within_dataset_rank_check（审稿人说的组内 ρ）")
    print("=" * 88)
    if SRC2.exists():
        d2 = json.loads(io.open(SRC2, encoding="utf-8", errors="replace").read())
        for k in ("within_dataset_rank_check", "cross_checkpoint_correlations",
                  "per_dataset_spread"):
            if k in d2:
                print(f"\n  ── {k} ──")
                print("  " + json.dumps(d2[k], ensure_ascii=False, indent=1)[:1400])

    print()
    print("=" * 88)
    print("④ offset_analysis（+3.62 点偏移的来源）")
    print("=" * 88)
    print("  " + json.dumps(d.get("offset_analysis"), ensure_ascii=False, indent=1)[:1200])
    print()
    print("  ── synthetic_curve（对照曲线）──")
    sc = d.get("synthetic_curve")
    if isinstance(sc, dict):
        for k, v in list(sc.items())[:12]:
            print(f"     {k}: {json.dumps(v, ensure_ascii=False)[:150]}")

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps({"source": str(SRC.relative_to(REPO)),
                        "n_checkpoints": (len(cps) if cps is not None else 0)},
                       ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
