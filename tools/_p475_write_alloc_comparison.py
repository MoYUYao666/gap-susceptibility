# -*- coding: utf-8 -*-
r"""定稿 P3 稿中的"同预算分配比较"段（P1+P2+P3 全部完成后的最终口径）（2026-10-13）。

## 已核实的全部数字（`tools/_p474`，我独立实现 Welch t 分布双侧 p）

| 方案 | n | 均值 | sd | 逐 run |
|---|---|---|---|---|
| **`exp`（Γ-guided）** | 6 | **+1477.5** | 1563.3 | −1053.0 / 782.4 / 1002.2 / 2192.5 / 2705.5 / 3234.9 |
| **`uniform`** | 6 | **+5047.5** | 1899.9 | 2841.6 / 3403.0 / 4800.3 / 5491.0 / 5543.6 / 8205.7 |
| `corner` | 6 | +2343.9 | 2426.1 | −1741.4 / 570.5 / 3143.9 / 3518.4 / 4159.4 / 4412.6 |
| `inverse`（反序） | 6 | +2470.2 | 4111.2 | −1237.2 / −528.7 / 893.3 / 1557.3 / 4225.1 / 9911.5 |
| **独立随机池** | 30 | **+3347.4** | 4771.2 | （10 方案 × 3 seed） |

**Welch（我独立实现）**：
- **`exp` vs `uniform`：t=−3.554, df=9.6, p=0.0055** ✅ **过 Bonferroni×3（0.0167）**
- `corner` vs `uniform`：t=−2.149, p=0.0587 ❌
- **`inverse` vs `uniform`：t=−1.394, p=0.2057** ❌（**3-seed 时是 0.037 ⇒ 小样本假象**）

**池的离散分解**：**组内 sd 中位数 3196.6 > 组间 sd 3010.1**（混合 4771.2）
⇒ **噪声主要来自同一分配内的 seed 波动**
**Γ-guided 在池中分位 46.7%（14/30 更低）**；**3/10 个随机方案均值更优**
**所需 n = 11–28 每方案**（σ 取 3010→11.2、3197→12.6、4111→20.8、4771→28.0；Δ=3570.1）

## 必须写出的张力（诚实处理）

**Γ-guided 优于 uniform（p=0.0055，过校正）｜但与随机不可区分（46.7%）｜且反序也不比 uniform 差（p=0.21）**
⇒ **能主张"这个分配比均匀好"，不能主张"是 Γ 的排序在起作用"。**

    python tools\_p475_write_alloc_comparison.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import re
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
EX = REPO / "paper3" / "paper_ieee" / "sections" / "experiments.tex"

# 找到我先前写的 provisional 段（以 "and it does not beat" 起，到 "Reversing the rule" 后）
START = "and it does not beat"
END = "($+2225 \\\\pm 1763$)."


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(EX, encoding="utf-8", errors="replace").read()
    i = t.find(START)
    j = t.find("Reversing the rule", i)
    if i < 0 or j < 0:
        print(f"  🔴 锚点未命中（i={i}, j={j}）")
        return 1
    k = t.find("($+2225 \\pm 1763$).", j)
    if k < 0:
        print("  🔴 找不到段尾")
        return 1
    end = k + len("($+2225 \\pm 1763$).")
    old = t[i:end]
    print(f"  将替换 {len(old)} 字符的段（{old[:70]!r} …）")

    NEW = (
        "and, in a capacity-matched comparison run with six seeds per arm, the\n"
        "$\\Gamma$-guided allocation reaches $\\Delta E = +1478 \\pm 1563$ against\n"
        "$+5048 \\pm 1900$ for uniform (Welch $t = -3.55$, $\\mathrm{df} = 9.6$,\n"
        "$p = 0.0055$, which survives a Bonferroni correction for the three plans\n"
        "compared). The rule therefore beats the uniform-rank baseline it was designed to\n"
        "replace. Two further controls keep us from reading more into it than the data\n"
        "supports, and both go against the stronger interpretation. First, the same\n"
        "comparison against a random allocation of an identical parameter budget---thirty\n"
        "runs over ten distinct feasible allocations---does not separate: the pool averages\n"
        "$+3347 \\pm 4771$ and the $\\Gamma$-guided mean sits at its $47$th percentile, with\n"
        "three of the ten random allocations averaging lower. Second, reversing the rule---\n"
        "giving the largest rank to the \\emph{least} coupled block---no longer differs from\n"
        "uniform once the sample is doubled ($+2470 \\pm 4111$, $p = 0.21$); at three seeds\n"
        "it had appeared to ($p = 0.037$), which we record as a small-sample artefact rather\n"
        "than a result. The honest summary is therefore narrow: \\emph{this} allocation beats\n"
        "the uniform-rank baseline, but we cannot show that it is the \\emph{ordering} that\n"
        "does the work, because neither the reversed ordering nor a random draw is\n"
        "reliably worse. The design does not have the resolution to settle that question:\n"
        "with the between-plan spread at $3010$ and the within-plan seed spread at $3197$,\n"
        "distinguishing plans separated by $3570$ would need roughly $11$ to $28$ seeds per\n"
        "arm, of which we report six. What we can state without qualification is the shape\n"
        "of the noise: it is dominated by seed-to-seed variation \\emph{within} a fixed\n"
        "allocation rather than by differences \\emph{between} allocations.")

    if not a.apply:
        print("  （预演）")
        return 0
    bak = EX.with_suffix(".tex.bak_p475")
    if not bak.exists():
        shutil.copy2(EX, bak)
    io.open(EX, "w", encoding="utf-8", newline="").write(t[:i] + NEW + t[end:])
    t2 = io.open(EX, encoding="utf-8", errors="replace").read()
    checks = {
        "含 6-seed 的 exp vs uniform p=0.0055": "$p = 0.0055$" in t2,
        "含过 Bonferroni": "survives a Bonferroni correction" in t2,
        "含随机池不可区分": "$+3347 \\pm 4771$" in t2 and "47$th percentile" in t2,
        "含 3 个随机分配更优": "three of the ten random allocations averaging lower" in t2,
        "含反序不再显著": "$p = 0.21$" in t2,
        "含小样本假象的更正": "small-sample artefact" in t2,
        "含所需 n = 11–28": "roughly $11$ to $28$ seeds" in t2,
        "含噪声主要来自组内": "dominated by seed-to-seed variation" in t2,
        "不再有旧 provisional 段": "provisional rather than as a result" not in t2,
    }
    ok = True
    for k2, v in checks.items():
        print(f"  {'✅' if v else '🔴'} {k2}")
        ok = ok and v
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
