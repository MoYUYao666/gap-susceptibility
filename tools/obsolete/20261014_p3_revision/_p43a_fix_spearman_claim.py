# -*- coding: utf-8 -*-
r"""修正我写进 P3 的那句（第 18 个错）：把整体相关说成了单调关系（2026-10-12）。

## 我错在哪

我在 `experiments.tex` 写了：
> *"Across all 79 runs the rank correlation between ΔE_test and ΔR@1 is −0.3819:
> improving the energy is associated with worse retrieval."*

**这与 `p3-downstream` 刚更正过的错误同型**：**把整体相关当成了子集内的单调关系**。
**实测四个口径**（`tools/_p439b`，我独立重算）：

| 口径 | Spearman | n |
|---|---|---|
| **ΔE_train vs ΔR@1**（论文 ΔE 的直接类比） | **+0.4778** | 78 |
| **ΔE_test vs ΔR@1（全体）** | **−0.3742** | 78 |
| **ΔE_test vs ΔR@1（仅 ΔE_test<0）** | **+0.1715** | 54 |
| ΔE_test vs ΔR@1（仅 real） | −0.6912 | 39 |
| ΔE_test vs ΔR@1（仅 blank） | −0.6385 | 39 |

⇒ **在"能量下降"的 54 个 run 内部几乎无关（+0.17）** ⇒ 全体 −0.374 **主要来自 real/blank 两簇的结构差异**，
**不是"降得越多、下游越差"的单调关系**。

## 配对比较（最干净，比它报的更强）

同 rank / 同 n / 同 seed，**real → blank**：

| 训练量 | 对数 | Δ(ΔE_test) 均值 | **Δ(ΔR@1) 均值** | R@1 范围 |
|---|---|---|---|---|
| **n=16** | 21 | **−0.00641**（blank 能量更降） | **+0.00651** | [+0.0027, +0.0099] |
| **n=1024** | 18 | **+0.00039**（blank 能量略升） | **−0.02244** | **[−0.0346, −0.0081]** |

⇒ **n=16 与 n=1024 的配对结论方向相反** → **更强的否证**：
**同一操作（换成 blank）在两种训练量下，能量变化与下游变化的关系不同** ⇒ 能量无法预测下游。

## 修法

把稿中那句改为**分层汇报四个口径**，并以**配对比较**为主证据（不依赖簇结构），
同时**明确声明"能量下降子集内几乎无关"**。

    python tools\_p43a_fix_spearman_claim.py [--apply]
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
    "Across all $79$ runs the rank correlation\n"
    "between $\\Delta E_{\\mathrm{test}}$ and $\\Delta R@1$ is $-0.3819$: improving the\n"
    "energy is associated with \\emph{worse} retrieval. Runs with $\\Delta E < 0$ average\n"
    "$\\Delta R@1 = +0.0056$ against $-0.0027$ for $\\Delta E > 0$, but that contrast is\n"
    "confounded with the image condition---almost every $\\Delta E < 0$ run is a real-image\n"
    "run---so we do not read it as causal, and the same-condition comparison above is the\n"
    "one we rely on. The conclusion we draw is negative and we state it as such: "
    "minimising $E$ does not reliably improve downstream retrieval, and $E$ should be read\n"
    "as a diagnostic of representation geometry rather than a proxy for task accuracy.")

NEW = (
    "The correlations have to be read carefully, because a\n"
    "coefficient computed over both conditions at once is dominated by the difference\n"
    "between them rather than by any trend within either. Pooled over all $78$ runs,\n"
    "$\\Delta E_{\\mathrm{test}}$ and $\\Delta R@1$ correlate at $-0.374$; restricted to the\n"
    "$54$ runs whose energy actually falls---the only ones about which a\n"
    "``lower energy, better task'' claim could be made---the correlation is $+0.172$,\n"
    "which is to say there is essentially no relationship. The training-condition energy,\n"
    "the quantity closest to the $\\Delta E$ this paper reports, correlates at $+0.478$: a\n"
    "larger energy reduction goes with a \\emph{smaller} downstream gain. The cleanest\n"
    "evidence is paired and does not depend on how the two conditions cluster: at\n"
    "$n = 16$ replacing real images with blank ones lowers the energy further by $0.0064$\n"
    "on average and \\emph{raises} $R@1$ by $0.0065$, while at $n = 1024$ the same\n"
    "replacement leaves the energy essentially unchanged ($+0.0004$) and lowers $R@1$ by\n"
    "$0.0224$ (range $-0.0081$ to $-0.0346$). The sign of the energy change therefore\n"
    "does not determine the sign of the downstream change even when the intervention is\n"
    "held fixed. The conclusion we draw is negative and we state it as such: minimising\n"
    "$E$ does not reliably improve downstream retrieval, and $E$ should be read as a\n"
    "diagnostic of representation geometry rather than a proxy for task accuracy.")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(EX, encoding="utf-8", errors="replace").read()
    n = t.count(OLD)
    print(f"  锚点命中 {n}")
    if n != 1:
        print("  🔴 锚点未命中")
        return 1
    if not a.apply:
        print("  （预演）")
        return 0
    bak = EX.with_suffix(".tex.bak_p43a")
    if not bak.exists():
        shutil.copy2(EX, bak)
    io.open(EX, "w", encoding="utf-8", newline="").write(t.replace(OLD, NEW))
    t2 = io.open(EX, encoding="utf-8", errors="replace").read()
    checks = {
        "不再有 −0.3819": "$-0.3819$" not in t2,
        "含四个口径": "$-0.374$" in t2 and "$+0.172$" in t2 and "$+0.478$" in t2,
        "明确 ΔE<0 子集内几乎无关系": "essentially no relationship" in t2,
        "含配对 n=16 与 n=1024": "$0.0064$" in t2 and "$0.0224$" in t2,
        "明确符号不决定下游符号": "does not determine the sign of the downstream" in t2,
        "保留否证性结论": "does not reliably improve downstream retrieval" in t2,
    }
    ok = True
    for k, v in checks.items():
        print(f"  {'✅' if v else '🔴'} {k}")
        ok = ok and v
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
