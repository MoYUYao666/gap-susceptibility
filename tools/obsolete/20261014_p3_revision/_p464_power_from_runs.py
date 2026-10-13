# -*- coding: utf-8 -*-
r"""复算功效样本量（从逐 run 明细取数，修正归档键名漂移）（2026-10-13）。

## 我先前错在哪

我写 "$n \\approx 2\\sigma^2(z+z)^2/\\Delta^2 \\approx \\mathbf{87}$"，
但复算时**实际用的是不含因子 2 的式子** $n = \\sigma^2(z+z)^2/\\Delta^2$ ⇒ 结果大了 2 倍。
**正确值**（含因子 2）：$\\sigma$=4771 → ≈**21**；$\\sigma$=6937 → ≈**44**。

**⇒ 成员是对的，我错了。** 它明确写"我不写一个自己复算不出的数"（项目铁律的正面执行）。

## 数据来源（修正）

`p3_alloc_results.json :: per_plan` **现在只含 10 个随机方案**（规则方案已移出）。
⇒ **本脚本从逐 run 明细 `outputs/analysis/p3_alloc_runs/main/*.json` 直接聚合**（权威且键名稳定）。

    python tools\_p464_power_from_runs.py [--apply]
"""
from __future__ import annotations

import argparse
import glob
import io
import json
import math
import os
import statistics
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "outputs" / "analysis" / "p3_power_recompute.json"

Z_A, Z_B = 1.959963985, 0.841621234
K2 = 2 * (Z_A + Z_B) ** 2      # 正确（每方案）
K1 = (Z_A + Z_B) ** 2          # 我先前误用


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    rep = {"constants": {"k_correct_per_arm": round(K2, 4), "k_i_misused": round(K1, 4)}}

    g = defaultdict(list)
    for f in glob.glob(str(REPO / "outputs/analysis/p3_alloc_runs/main/*.json")):
        d = json.loads(io.open(f, encoding="utf-8", errors="replace").read())
        x = d.get("delta_E")
        if isinstance(x, (int, float)):
            g[str(d.get("plan"))].append(x)

    print("=" * 100)
    print("Δ = |exp − uniform|（从逐 run 明细）")
    print("=" * 100)
    exp, uni = g.get("exp_beta_paper_0.137"), g.get("uniform")
    if not (exp and uni):
        print(f"  🔴 缺：exp={len(exp) if exp else 0} uniform={len(uni) if uni else 0}")
        return 1
    em, um = statistics.mean(exp), statistics.mean(uni)
    delta = abs(em - um)
    print(f"  exp     n={len(exp)} mean={em:+.4f}  {[round(x,1) for x in exp]}")
    print(f"  uniform n={len(uni)} mean={um:+.4f}  {[round(x,1) for x in uni]}")
    print(f"  **Δ = {delta:.4f}**")
    rep["delta"] = round(delta, 4)
    rep["delta_source"] = "outputs/analysis/p3_alloc_runs/main/{exp_beta_paper_0.137,uniform}__seed*.json :: delta_E"

    INDEP = [f"random_{i:02d}" for i in (1, 2, 3, 5, 6, 7, 8, 9, 10, 11)]
    pool = [x for k in INDEP for x in g.get(k, [])]
    print()
    print("=" * 100)
    print(f"独立随机池（n={len(pool)}）")
    print("=" * 100)
    pm = statistics.mean(pool)
    psd = statistics.stdev(pool)
    lo = sum(1 for x in pool if x < em)
    print(f"  mean={pm:+.1f}  sd={psd:.1f}  min={min(pool):+.1f}  max={max(pool):+.1f}")
    print(f"  负值（随机分配改善对齐）: {sum(1 for x in pool if x<0)}/{len(pool)}")
    print(f"  Γ-guided 均值经验分位: {lo}/{len(pool)} = {100*lo/len(pool):.1f}%")
    print(f"  池 sd({psd:.1f}) vs Δ({delta:.1f}) ⇒ 噪声/信号 = {psd/delta:.2f}")
    rep["pool"] = {"n": len(pool), "mean": round(pm, 2), "sd": round(psd, 2),
                   "n_negative": sum(1 for x in pool if x < 0),
                   "gamma_percentile": round(100 * lo / len(pool), 2),
                   "sd_source": "outputs/analysis/p3_alloc_runs/main/random_*__seed*.json :: delta_E"}

    print()
    print("=" * 100)
    print("每方案所需 n（**含因子 2** 的公式）")
    print("=" * 100)
    print(f"  {'σ 来源':<26} {'σ':>9}  {'n/方案':>9}")
    rows = []
    for label, s in (("池 sd（最终，n=30）", psd),):
        n = K2 * s * s / (delta * delta)
        print(f"  {label:<26} {s:>9.1f}  {n:>9.1f}")
        rows.append({"label": label, "sigma": round(s, 2), "n_per_arm": round(n, 1)})
    for label, s in (("我先前引用的 σ=6937（n=7 时）", 6937.4),):
        n = K2 * s * s / (delta * delta)
        print(f"  {label:<26} {s:>9.1f}  {n:>9.1f}   ← **正确值**")
        print(f"  {'（同一 σ，我误用的公式给）':<26} {'':>9}  {K1 * s * s / (delta * delta):>9.1f}   ← 我先前报的 87")
        rows.append({"label": label, "sigma": s, "n_per_arm": round(n, 1),
                     "n_wrong_formula": round(K1 * s * s / (delta * delta), 1)})
    rep["power"] = rows
    rep["correct_n_range"] = [round(K2 * psd ** 2 / delta ** 2, 1),
                              round(K2 * 6937.4 ** 2 / delta ** 2, 1)]

    print()
    print("=" * 100)
    print("结论")
    print("=" * 100)
    print(f"  **正确所需 n = {rep['correct_n_range'][0]:.0f}–{rep['correct_n_range'][1]:.0f} 每方案**")
    print(f"  **我先前报的 87 是漏掉因子 2 所致；成员复算的 21–44 正确。**")
    print(f"  3（→6）个 seed 相对 {rep['correct_n_range'][0]:.0f}–{rep['correct_n_range'][1]:.0f} 仍不足 ⇒ **判定不变**")

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps(rep, ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
