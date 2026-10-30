# -*- coding: utf-8 -*-
r"""按更正后的版本改写稿中配对段（2026-10-12）。

## 依据（`tools/_p43c` 我独立复核，判定与 `p3-downstream` 一致）

| 训练量 | 对数 | Δ(ΔE_test) | Wilcoxon p | Δ(R@1) | Wilcoxon p |
|---|---|---|---|---|---|
| **n=16** | 21 | **−0.00641**（**0/21 全负**） | **显著下降** | **+0.00651**（**21/0 全正**） | **显著改善** |
| **n=1024** | 18 | **+0.00039**（7 正/11 负） | **p≈0.90 无显著变化** | **−0.02244**（**0/18 全负**） | **显著恶化** |

⇒ **我先前写的"能量符号相反"过强**（n=1024 是"没动"，不是"略升"）。
**更硬且不依赖任何相关口径的版本**：**能量的变化对下游方向既非充分也非必要。**

    python tools\_p43d_fix_paired_wording.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
EX = REPO / "paper3" / "paper_ieee" / "sections" / "experiments.tex"

OLD = (
    "The cleanest\n"
    "evidence is paired and does not depend on how the two conditions cluster: at\n"
    "$n = 16$ replacing real images with blank ones lowers the energy further by $0.0064$\n"
    "on average and \\emph{raises} $R@1$ by $0.0065$, while at $n = 1024$ the same\n"
    "replacement leaves the energy essentially unchanged ($+0.0004$) and lowers $R@1$ by\n"
    "$0.0224$ (range $-0.0081$ to $-0.0346$). The sign of the energy change therefore\n"
    "does not determine the sign of the downstream change even when the intervention is\n"
    "held fixed.")

NEW = (
    "The cleanest evidence is paired and rests on neither a\n"
    "correlation nor the cluster structure: holding rank, training size and seed fixed\n"
    "and replacing real images by blank ones, at $n = 16$ the substitution significantly\n"
    "\\emph{lowers} the alignment energy ($21$ of $21$ pairs, Wilcoxon\n"
    "$p = 9.5\\times10^{-7}$) and significantly \\emph{improves} retrieval ($21$ of $21$,\n"
    "$p = 5.9\\times10^{-5}$), whereas at $n = 1024$ it leaves the energy statistically\n"
    "unchanged ($+0.0004$, $7$ positive of $18$, $p = 0.90$) and significantly\n"
    "\\emph{degrades} retrieval ($18$ of $18$, $p = 7.6\\times10^{-6}$). An energy change\n"
    "is therefore neither sufficient nor necessary for the direction of downstream\n"
    "performance.")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(EX, encoding="utf-8", errors="replace").read()
    n = t.count(OLD)
    print(f"  锚点命中 {n}")
    if n != 1:
        i = t.find("The cleanest")
        print("  附近：" + repr(t[max(0, i - 60):i + 240]) if i >= 0 else "  （找不到）")
        return 1
    if not a.apply:
        print("  （预演）")
        return 0
    bak = EX.with_suffix(".tex.bak_p43d")
    if not bak.exists():
        shutil.copy2(EX, bak)
    io.open(EX, "w", encoding="utf-8", newline="").write(t.replace(OLD, NEW))
    t2 = io.open(EX, encoding="utf-8", errors="replace").read()
    checks = {
        "含 n=16 的 21/21 与 Wilcoxon": "$21$ of $21$" in t2,
        "含 n=1024 能量无显著变化 p=0.90": "$p = 0.90$" in t2,
        "含 n=1024 下游 18/18 全负": "$18$ of $18$" in t2,
        "含'既非充分也非必要'": "neither sufficient nor necessary" in t2,
        "不再说'符号相反'": "does not determine the sign of the downstream" not in t2,
        "不再出现 $+0.0004$ 的'略升'表述": "leaves the energy essentially unchanged ($+0.0004$)" not in t2,
    }
    ok = True
    for k, v in checks.items():
        print(f"  {'✅' if v else '🔴'} {k}")
        ok = ok and v
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
