# -*- coding: utf-8 -*-
r"""核配对 Wilcoxon 检验（p3-downstream 的更正）（2026-10-12）。

## 它纠正了什么

我写 *"同一干预在两种训练量下，**能量变化的符号相反**"* —— 但：
- **n=16**：Δ(ΔE_test) = −0.00641，**21/21 全负**，Wilcoxon **p=9.5e-7** → 显著下降 ✅
- **n=1024**：Δ(ΔE_test) = **+0.00039**，**7 正 / 11 负**，Wilcoxon **p=0.899** → **无显著变化**（不是"略升"）

⇒ **"符号相反"方向对、证据偏强**。**更硬的说法**：
**能量变化对下游方向既非充分也非必要**（两档都全票配对 + 双侧 Wilcoxon，**不依赖任何相关口径**）。

    python tools\_p43c_verify_paired_tests.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "outputs" / "analysis" / "p3_paired_tests_verified.json"


def wilcoxon(xs):
    """双侧 Wilcoxon 符号秩检验（正态近似，含连续性校正）。"""
    nz = [x for x in xs if x != 0]
    n = len(nz)
    if n == 0:
        return float("nan"), 0
    order = sorted(range(n), key=lambda i: abs(nz[i]))
    ranks = [0.0] * n
    i = 0
    while i < n:
        j = i
        while j + 1 < n and abs(nz[order[j + 1]]) == abs(nz[order[i]]):
            j += 1
        avg = (i + j) / 2.0 + 1
        for k in range(i, j + 1):
            ranks[order[k]] = avg
        i = j + 1
    wpos = sum(ranks[i] for i in range(n) if nz[i] > 0)
    mu = n * (n + 1) / 4.0
    sd = (n * (n + 1) * (2 * n + 1) / 24.0) ** 0.5
    if sd == 0:
        return float("nan"), n
    z = (wpos - mu - 0.5 * (1 if wpos > mu else -1)) / sd
    # 双侧 p（正态近似）
    p = 2 * (1 - _Phi(abs(z)))
    return p, n


def _Phi(z):
    return 0.5 * (1 + _erf(z / (2 ** 0.5)))


def _erf(x):
    # Abramowitz-Stegun 7.1.26
    sign = 1 if x >= 0 else -1
    x = abs(x)
    a1, a2, a3, a4, a5 = (0.254829592, -0.284496736, 1.421413741,
                          -1.453152027, 1.061405429)
    p = 0.3275911
    t = 1.0 / (1.0 + p * x)
    y = 1.0 - (((((a5 * t + a4) * t) + a3) * t + a2) * t + a1) * t * math.exp(-x * x)
    return sign * y


import math  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    d = json.loads(io.open(REPO / "outputs/analysis/p3d_clip_ranksweep.json",
                           encoding="utf-8", errors="replace").read())
    runs = d.get("runs") if isinstance(d, dict) else d
    g = defaultdict(dict)
    for r in runs:
        if r.get("dE_test") is None or r.get("R@1") is None:
            continue
        g[(r.get("n_train"), r.get("rank"), r.get("seed"))][r.get("condition")] = r

    rep = {}
    print("=" * 100)
    print("配对检验（同 rank / 同 n / 同 seed，real → blank）")
    print("=" * 100)
    for n in sorted({k[0] for k in g if k[0] is not None}):
        pairs = [(v["blank"], v["real"]) for k, v in sorted(g.items())
                 if k[0] == n and "real" in v and "blank" in v]
        if len(pairs) < 3:
            continue
        dE = [b["dE_test"] - r["dE_test"] for b, r in pairs]
        dR = [(b["R@1"] - 0.7058) - (r["R@1"] - 0.7058) for b, r in pairs]
        pE, nE = wilcoxon(dE)
        pR, nR = wilcoxon(dR)
        posE, posR = sum(1 for x in dE if x > 0), sum(1 for x in dR if x > 0)
        print(f"\n  n={n} ｜ 对数 {len(pairs)}")
        print(f"     Δ(ΔE_test): 均值 {statistics.mean(dE):+.5f} ｜ {posE} 正 / {len(dE)-posE} 负 "
              f"｜ Wilcoxon p = {pE:.2e}")
        print(f"     Δ(R@1)    : 均值 {statistics.mean(dR):+.5f} ｜ {posR} 正 / {len(dR)-posR} 负 "
              f"｜ Wilcoxon p = {pR:.2e}")
        print(f"     判定：能量 {'显著变化' if pE < 0.05 else '**无显著变化**'} ｜ "
              f"下游 {'显著变化' if pR < 0.05 else '无显著变化'}")
        rep[f"n{n}"] = {"n_pairs": len(pairs),
                        "dE_mean": round(statistics.mean(dE), 6), "dE_pos": posE,
                        "dE_p": float(f"{pE:.3g}"),
                        "dR1_mean": round(statistics.mean(dR), 6), "dR1_pos": posR,
                        "dR1_p": float(f"{pR:.3g}"),
                        "energy_significant": pE < 0.05, "downstream_significant": pR < 0.05}

    print()
    print("=" * 100)
    print("结论（不依赖任何相关口径）")
    print("=" * 100)
    n16, n1024 = rep.get("n16", {}), rep.get("n1024", {})
    print(f"  n=16  ：能量显著下降（p={n16.get('dE_p')}）+ 下游显著**升**（p={n16.get('dR1_p')}）")
    print(f"  n=1024：能量**无显著变化**（p={n1024.get('dE_p')}）+ 下游显著**降**（p={n1024.get('dR1_p')}）")
    print("  ⇒ 能量的变化**对下游方向既非充分也非必要**")

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps(rep, ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
