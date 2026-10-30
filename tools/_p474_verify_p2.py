# -*- coding: utf-8 -*-
r"""核 P2（6-seed）的关键统计（2026-10-13）。

## 待核（每条都会改稿）

1. **`exp` vs `uniform`**：6v6，均值差 3570，Welch **p=0.0055**（**过了 Bonferroni×3 的 0.0167**）
   ← 比 3-seed 的 p=0.024 **更强**
2. **`inverse` vs `uniform`**：3-seed 时 **p=0.037** ⇒ 6-seed 时 **p=0.2057**（**不再显著**）
   ⇒ **"反序也优于 uniform"是小样本假象** ⇒ 我先前"方向性未获支持"的**证据基础被削弱**
3. **池的组内 sd（3196.6）> 组间 sd（3010.1）** ⇒ **噪声主要来自"同一分配内的 seed 波动"**
4. **Levene p=0.1753 > 0.05** ⇒ 按预先写定的判据，**不得提及方差** ✅
5. **所需 n 更新为 11–28**（σ 与 Δ 都变了）

    python tools\_p474_verify_p2.py [--apply]
"""
from __future__ import annotations

import argparse
import glob
import io
import json
import math
import statistics
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "outputs" / "analysis" / "p3_p2_verified.json"

Z_A, Z_B = 1.959963985, 0.841621234
K2 = 2 * (Z_A + Z_B) ** 2


def welch(a, b):
    ma, mb = statistics.mean(a), statistics.mean(b)
    va, vb = statistics.variance(a), statistics.variance(b)
    na, nb = len(a), len(b)
    se = math.sqrt(va / na + vb / nb)
    t = (ma - mb) / se
    df = (va / na + vb / nb) ** 2 / ((va / na) ** 2 / (na - 1) + (vb / nb) ** 2 / (nb - 1))
    return t, df, ma, mb, va, vb


def tcdf_p(t, df):
    """双侧 p（Student-t，用不完全贝塔的连分式近似）。"""
    x = df / (df + t * t)
    # 正则化不完全贝塔 I_x(df/2, 1/2)
    def betacf(a, b, x, itmax=200, eps=3e-14):
        qab, qap, qam = a + b, a + 1, a - 1
        c, d = 1.0, 1.0 - qab * x / qap
        if abs(d) < 1e-30:
            d = 1e-30
        d = 1.0 / d
        h = d
        for m in range(1, itmax + 1):
            m2 = 2 * m
            aa = m * (b - m) * x / ((qam + m2) * (a + m2))
            d = 1.0 + aa * d
            if abs(d) < 1e-30:
                d = 1e-30
            c = 1.0 + aa / c
            if abs(c) < 1e-30:
                c = 1e-30
            d = 1.0 / d
            h *= d * c
            aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
            d = 1.0 + aa * d
            if abs(d) < 1e-30:
                d = 1e-30
            c = 1.0 + aa / c
            if abs(c) < 1e-30:
                c = 1e-30
            d = 1.0 / d
            de = d * c
            h *= de
            if abs(de - 1.0) < eps:
                break
        return h
    a, b = df / 2.0, 0.5
    lbeta = math.lgamma(a) + math.lgamma(b) - math.lgamma(a + b)
    if x < (a + 1) / (a + b + 2):
        ib = math.exp(a * math.log(x) + b * math.log(1 - x) - lbeta) * betacf(a, b, x) / a
    else:
        ib = 1 - math.exp(b * math.log(1 - x) + a * math.log(x) - lbeta) * betacf(b, a, 1 - x) / b
    return ib  # = P(|T| > |t|) 双侧


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    rep = {}

    g = defaultdict(list)
    for f in glob.glob(str(REPO / "outputs/analysis/p3_alloc_runs/main/*.json")):
        d = json.loads(io.open(f, encoding="utf-8", errors="replace").read())
        if isinstance(d.get("delta_E"), (int, float)):
            g[str(d.get("plan"))].append(d["delta_E"])

    print("=" * 104)
    print("① 逐方案（P2 后）")
    print("=" * 104)
    for k in ("exp_beta_paper_0.137", "uniform", "corner", "inverse_beta_paper_0.137"):
        v = g.get(k, [])
        if v:
            print(f"  {k:<26} n={len(v)}  mean={statistics.mean(v):+9.1f}  "
                  f"sd={statistics.stdev(v) if len(v)>1 else float('nan'):8.1f}  "
                  f"{[round(x,1) for x in sorted(v)]}")
            rep[k] = {"n": len(v), "mean": round(statistics.mean(v), 2),
                      "sd": round(statistics.stdev(v), 2) if len(v) > 1 else None}

    print()
    print("=" * 104)
    print("② Welch 检验（我独立实现 t 分布双侧 p）")
    print("=" * 104)
    uni = g.get("uniform", [])
    comps = [("exp_beta_paper_0.137", "exp(Γ-guided)"), ("corner", "corner"),
             ("inverse_beta_paper_0.137", "inverse(反序)")]
    for key, label in comps:
        v = g.get(key, [])
        if len(v) < 2 or len(uni) < 2:
            continue
        t, df, ma, mb, va, vb = welch(v, uni)
        p = tcdf_p(t, df)
        verdict = "✅ 过 Bonferroni×3 (0.0167)" if p < 0.0167 else ("⚠️ <0.05 但未过校正" if p < 0.05 else "❌ 不显著")
        print(f"  {label:<18} vs uniform: t={t:+7.3f}  df={df:5.1f}  **p={p:.4f}**  {verdict}")
        rep[f"welch_{key}_vs_uniform"] = {"t": round(t, 4), "df": round(df, 3), "p": round(p, 6),
                                          "passes_bonferroni3": p < 0.0167}

    print()
    print("=" * 104)
    print("③ 池的组间 vs 组内 sd（关键表述）")
    print("=" * 104)
    INDEP = [f"random_{i:02d}" for i in (1, 2, 3, 5, 6, 7, 8, 9, 10, 11)]
    plan_means, within_sds, pool = [], [], []
    for k in INDEP:
        v = g.get(k, [])
        if len(v) >= 2:
            plan_means.append(statistics.mean(v))
            within_sds.append(statistics.stdev(v))
        pool += v
    between = statistics.stdev(plan_means)
    within_med = statistics.median(within_sds)
    mixed = statistics.stdev(pool)
    print(f"  池的**组间 sd**（{len(plan_means)} 个方案均值之间）= **{between:.1f}**")
    print(f"  池的**组内 sd 中位数**（方案内 seed sd）= **{within_med:.1f}**")
    print(f"  混合池 sd（不应直接比）= {mixed:.1f}")
    print(f"  ⇒ **组内({within_med:.0f}) > 组间({between:.0f})** ⇒ "
          f"**噪声主要来自同一分配内的 seed 波动，而非不同分配之间**")
    rep["pool_sd"] = {"between": round(between, 2), "within_median": round(within_med, 2),
                      "mixed": round(mixed, 2), "n_plans": len(plan_means), "n_runs": len(pool)}

    print()
    print("=" * 104)
    print("④ Γ-guided 在池中的分位 + 所需 n 更新")
    print("=" * 104)
    em = statistics.mean(g["exp_beta_paper_0.137"])
    lo = sum(1 for x in pool if x < em)
    print(f"  Γ-guided 均值 {em:+.1f} ｜ 池内更低 {lo}/{len(pool)} = {100*lo/len(pool):.1f}%")
    um = statistics.mean(uni)
    delta = abs(em - um)
    print(f"  Δ = |exp − uniform| = {abs(statistics.mean(g['exp_beta_paper_0.137']) - um):.1f}")
    for label, s in (("池组间 sd", between), ("池组内 sd 中位数", within_med),
                     ("混合池 sd", mixed),
                     ("inverse sd（最坏）", statistics.stdev(g["inverse_beta_paper_0.137"]))):
        n = K2 * s * s / (delta * delta)
        print(f"     σ={s:8.1f}（{label:<20}）⇒ 每方案 n ≈ **{n:.1f}**")
    rep["delta"] = round(delta, 2)
    rep["gamma_percentile"] = round(100 * lo / len(pool), 2)

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps(rep, ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
