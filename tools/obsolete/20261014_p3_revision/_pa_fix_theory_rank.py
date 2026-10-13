# -*- coding: utf-8 -*-
r"""修正理论章节两处被新结果否定的声称，并让机制解释对齐自家的 β 数据（2026-10-03）。

## 两个问题

**问题 A（本次实验造成）**：`theory.tex:102` 与 `:4` 仍称 "lower LoRA rank preserves
alignment better"，而严格冻结 rank sweep 显示**相反**（text-only 单调：r32 −0.0754 vs r4 −0.0285）。

**问题 B（原稿既有，与本次实验无关）**：`theory.tex:102` 的机制解释称

> "the net effect favors restoration (**$\beta$ increases moderately with rank** while $\alpha$ remains
> negative)"

但 **`tab:phase2` 自家数据**（text-only，5-seed 均值）：

| rank | 8 | 16 | 32 |
|---|---|---|---|
| $\beta$ | 0.167 | 0.140 | **0.119** |

**$\beta$ 随 rank 递减，不是递增**。而严格冻结下 rank 越高间隙压得越低 —— 与"$\beta$ 更小"方向一致
（$\beta$ 是间隙的**恢复**系数，越小则间隙压得越低）。故机制解释应改为**与数据同向**。

    python tools\_pa_fix_theory_rank.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "paper合" / "sections" / "theory.tex"

OLD_102 = ("\\textbf{LoRA rank effects.} Section~\\ref{sec:empirical} found that lower LoRA rank preserves "
           "alignment better. The ODE explains this through the rank-dependence of $\\beta$: lower ranks "
           "restrict the parameter subspace available for both perturbation and restoration, but the net "
           "effect favors restoration ($\\beta$ increases moderately with rank while $\\alpha$ remains "
           "negative). We verify this prediction quantitatively in Section~\\ref{sec:validation}.")

NEW_102 = ("\\textbf{LoRA rank effects.} The ODE locates the rank effect in the ratio of the two "
           "coefficients rather than in the capacity of the adapter. In the fits of "
           "Table~\\ref{tab:phase2}, $\\alpha$ stays negative and roughly flat across ranks, while $\\beta$ "
           "falls as rank grows ($0.167$ at $r{=}8$, $0.140$ at $r{=}16$, $0.119$ at $r{=}32$, text-only): "
           "a smaller restoring coefficient means the trajectory settles further from its starting gap. "
           "The direction of the rank effect is therefore inherited from $\\beta$, and because $\\beta$ is "
           "itself a property of the protocol rather than of rank alone, the effect changes sign between "
           "protocols. Section~\\ref{sec:validation} tests this and reports both regimes.")

OLD_4 = ("Why does text-only training preserve alignment, why does lower LoRA rank provide better "
         "protection, and what determines the gap trajectory?")
NEW_4 = ("Why does adapting one side rather than the other change the trajectory, why does the effect of "
         "adapter rank depend on what else is being trained, and what determines the gap trajectory?")


def main() -> int:
    apply = "--apply" in sys.argv
    t = io.open(F, encoding="utf-8").read()
    n = 0
    for old, new, why in ((OLD_102, NEW_102, "theory:102 机制解释对齐 β 实测数据"),
                          (OLD_4, NEW_4, "theory:4 动机陈述去掉被否定的前提")):
        c = t.count(old)
        if c == 1:
            print(f"  ✅ {why}")
            if apply:
                t = t.replace(old, new, 1)
            n += 1
        else:
            print(f"  ⚠ {why}：未唯一命中（{c} 次）")
    if apply and n == 2:
        io.open(F, "w", encoding="utf-8", newline="").write(t)
        t2 = io.open(F, encoding="utf-8").read()
        assert "lower LoRA rank preserves alignment better" not in t2, "断言失败：旧声称仍在"
        assert "increases moderately with rank" not in t2, "断言失败：错误机制解释仍在"
        assert "0.119$ at $r{=}32$" in t2, "断言失败：β 数据未写入"
        assert "changes sign between" in t2, "断言失败：约定依赖未写入"
        print("\n  ✅ 已改 2 处并断言通过")
    else:
        print(f"\n  {n}/2 处可改" + ("（预演）" if not apply else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
