# -*- coding: utf-8 -*-
r"""对比归档与我的 run 的**衰减率 β**（2026-10-08）。

## 已知

| 量 | 归档 `v1_both_r8` | 我的 trainer 基座 run |
|---|---|---|
| 起始 DG\\* | 1.4767 | 1.88（epoch 1 之后） |
| 第 1 轮漂移 | ~0.10 | **0.50**（差 5 倍） |
| 总跨度 | 0.1641 | **0.6389**（差 4 倍） |

**frozen 基线**（我实测，500 样本验证集）：**1.3761**；LoRA 注入后 1.3763（**B 零初始化验证通过**）。

**→ 初始化正确，差异在漂移速率。**

## 本脚本

1. 拟合归档 `v1_both_r8` 逐 seed 的 (α, β)；
2. 与我的 run 的 (α, β) 对比；
3. 给出**要达到归档跨度所需的学习率缩放**（从 `final_train_loss` 与 β 反推）。

    python tools\_p30_compare_beta.py
"""
from __future__ import annotations

import glob
import io
import json
import statistics as st
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def fit(t, y):
    import numpy as np
    t = np.asarray(t, float); y = np.asarray(y, float)
    dg0 = float(y[0]); r = y - dg0
    best = (float("nan"), float("nan"), float("inf"))
    for logb in np.linspace(np.log10(0.005), np.log10(20.0), 800):
        b = 10.0 ** logb
        u = 1.0 - np.exp(-b * t); den = float((u * u).sum())
        if den < 1e-12:
            continue
        a = float((u * r).sum()) / den
        res = float(((r - a * u) ** 2).sum())
        if res < best[2]:
            best = (a * b, b, res)
    return best[0], best[1]


def main() -> int:
    print("=== 归档 v1_both_r8 逐 seed ===")
    arch = []
    for f in sorted(glob.glob(str(REPO / "outputs/theory/v1_trajectory/v1_both_r8/seed*/dg_star_history.json"))):
        d = json.loads(io.open(f, encoding="utf-8").read())
        A, B = fit(d["epochs"], d["dg_star"])
        y = d["dg_star"]
        ratio = A / B if B else float("nan")
        arch.append((A, B, max(y) - min(y)))
        print(f"  {Path(f).parts[-2]:<10} α={A:+.5f} β={B:.4f} ｜ ASPL α/β={ratio:+.4f} "
              f"｜ 第1轮漂移 {y[0]-y[1]:+.4f} ｜ 跨度 {max(y)-min(y):.4f}")
    if arch:
        print(f"  归档均值: α={st.mean(x[0] for x in arch):+.5f}  "
              f"β={st.mean(x[1] for x in arch):.4f}  "
              f"α/β={st.mean(x[0]/x[1] for x in arch):+.4f}（渐近幅值）")

    print("\n=== 我的 trainer 基座 run ===")
    p = REPO / "outputs/theory/alpha_trainer_based/alpha_trainer_based.json"
    if p.exists():
        d = json.loads(io.open(p, encoding="utf-8").read())
        for r in d.get("records", []):
            y = r["dg_star"]
            A, B = fit(list(range(1, len(y) + 1)), y)
            print(f"  seed {r['seed']}: α={A:+.5f} β={B:.4f} ｜ α/β={A/B if B else float('nan'):+.4f} "
                  f"｜ 第1轮漂移 {y[0]-y[1]:+.4f} ｜ 跨度 {max(y)-min(y):.4f}")
            if arch:
                a_arch = st.mean(x[0] for x in arch); b_arch = st.mean(x[1] for x in arch)
                print(f"     → 与归档之比：α {A/a_arch:.2f}× ｜ β {B/b_arch:.2f}× ｜ "
                      f"渐近幅值 {(A/B)/(a_arch/b_arch):.2f}×")

    print("\n=== 达到归档跨度需要什么 ===")
    print("  归档：α/β ≈ 0.282（渐近幅值 0.28），起始 1.4767 → 渐近 1.19，跨度 ~0.16")
    print("  我的：见上。**β 越大 → 衰减越快 → 但渐近幅值 α/β 决定总跨度。**")
    print("  → **总跨度由 α/β 决定，而 α ∝ 有效学习率**（梯度流恒等式 d(DG*)/dt = −η⟨∇DG*,∇L⟩）。")
    print("  → **若我的 α/β 约为归档的 4 倍，则把 lr 缩小约 4 倍应能对齐。**")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
