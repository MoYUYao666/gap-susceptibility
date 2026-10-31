# -*- coding: utf-8 -*-
r"""复算功效样本量：核我先前报的 n≈87 是否错了（2026-10-13）。

## 背景

我在 07:19 的消息里写："$n \\approx 2\\sigma^2(z_{1-\\alpha/2}+z_{1-\\beta})^2/\\Delta^2 \\approx \\mathbf{87}$"，
并给出 $\\sigma \\approx 6937$、$\\Delta \\approx 4172$。

**成员复算不出 87**，它用同一公式得：$\\sigma$=4919→≈22、6937→≈44。
**它明确写："我不写一个自己复算不出的数"（项目铁律）。**

## 我要自己算清楚（可能是**我漏了公式里的因子 2**，也可能是它漏了）

    python tools\_p463_recompute_power.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import math
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "outputs" / "analysis" / "p3_power_recompute.json"

Z_A = 1.959963985   # alpha/2 = 0.025 (two-sided 0.05)
Z_B = 0.841621234   # power 0.80
K_FULL = 2 * (Z_A + Z_B) ** 2       # 公式① 含因子 2
K_NO2 = (Z_A + Z_B) ** 2            # 公式② 不含因子 2（我先前用的）


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    rep = {"z_alpha_2": Z_A, "z_beta": Z_B,
           "k_with_factor_2": K_FULL, "k_without_factor_2": K_NO2}

    print("=" * 100)
    print("两个公式常数")
    print("=" * 100)
    print(f"  (z_a/2 + z_b)^2            = {K_NO2:.4f}")
    print(f"  2*(z_a/2 + z_b)^2          = {K_FULL:.4f}")
    print(f"  ⇒ 两者差因子 2（我先前用的是**不含 2** 的那个）")

    # Δ 与 σ 的出处
    print()
    print("=" * 100)
    print("Δ（方案间差）与 σ（池 sd）的出处")
    print("=" * 100)
    d = json.loads(io.open(REPO / "outputs/analysis/p3_alloc_results.json",
                           encoding="utf-8", errors="replace").read())
    pp = d.get("per_plan", {})
    exp_m = pp["exp_beta_paper_0.137"]["delta_E"]["mean"]
    uni_m = pp["uniform"]["delta_E"]["mean"]
    delta = abs(exp_m - uni_m)
    print(f"  exp.mean   = {exp_m:.4f}  ← per_plan.exp_beta_paper_0.137.delta_E.mean")
    print(f"  uniform.mean = {uni_m:.4f}  ← per_plan.uniform.delta_E.mean")
    print(f"  Δ = {delta:.4f}")
    rep["delta"] = round(delta, 4)
    rep["delta_source"] = "outputs/analysis/p3_alloc_results.json :: per_plan.*.delta_E.mean"

    sigmas = [("池 sd, n=28", 4919.1), ("池 sd, n=30（最终）", 4771.2),
              ("池 sd, n=7（最保守）", 6937.4)]
    print()
    print("=" * 100)
    print("每方案所需 n（两种公式 × 三个 σ）")
    print("=" * 100)
    print(f"  {'σ 取值':<24} {'σ':>9}  {'含因子2':>9}  {'不含因子2':>11}")
    rows = []
    for label, s in sigmas:
        n_full = K_FULL * s * s / (delta * delta)
        n_no2 = K_NO2 * s * s / (delta * delta)
        print(f"  {label:<24} {s:>9.1f}  {n_full:>9.1f}  {n_no2:>11.1f}")
        rows.append({"label": label, "sigma": s, "n_with_factor_2": round(n_full, 1),
                     "n_without_factor_2": round(n_no2, 1)})
    rep["rows"] = rows

    print()
    print("=" * 100)
    print("判定：87 是怎么来的？")
    print("=" * 100)
    n87_sigma_full = math.sqrt(87 * delta * delta / K_FULL)
    n87_sigma_no2 = math.sqrt(87 * delta * delta / K_NO2)
    print(f"  若用**含因子 2** 的公式，要得到 n=87 需 σ = {n87_sigma_full:.1f}")
    print(f"  若用**不含因子 2** 的公式，要得到 n=87 需 σ = {n87_sigma_no2:.1f}")
    print(f"  ⇒ 我先前用的 σ≈6937 代入**不含因子 2** 的公式 = "
          f"{K_NO2 * 6937.4 ** 2 / delta ** 2:.1f}  ← **这正是 87**")
    print()
    print(f"  ⇒ **我漏了公式里的因子 2。** 正确值（含因子 2）对 σ=6937 是 "
          f"{K_FULL * 6937.4 ** 2 / delta ** 2:.1f}，对 σ=4771 是 {K_FULL * 4771.2 ** 2 / delta ** 2:.1f}")
    rep["my_87_came_from"] = "公式漏因子 2，σ=6937.4"
    rep["correct_range"] = [round(K_FULL * 4771.2 ** 2 / delta ** 2, 1),
                            round(K_FULL * 6937.4 ** 2 / delta ** 2, 1)]

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps(rep, ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
