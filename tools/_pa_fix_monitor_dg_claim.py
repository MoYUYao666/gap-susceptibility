# -*- coding: utf-8 -*-
r"""按实验 ⑤ 的结果，收紧论文设计原则 ③ 的措辞（2026-10-07）。

## 实验结论（`outputs/analysis/monitor_dg_check{2,3}.json`）

| 检验 | 结果 | 支持什么 |
|---|---|---|
| **初始 $DG^*$ → 末态 R@1** | **r = −0.708**（p≈0, n=96） | ✅ **DG 是有效健康信号**（预测检索质量） |
| epoch-1 $DG^*$ 相对变化 → R@1 | r = −0.151（p≈0.14） | ❌ 首步变化无预测力 |
| **DG 与 CG 的 argmin epoch 一致率** | **42%**（40/96） | ❌ **不能替代任务指标作停止准则** |
| 5 种**可实现**早停规则 vs 不早停 | **0/5 更优**（R1 88/94 更差） | ❌ 早停无收益 |

## 论文原文（`discussion.tex` 原则 ③）

> "**Monitor DG as an alignment health signal.** … **DG-based early stopping** or learning rate scheduling
> are **principled applications** of this insight."

**问题**：前半句（监控 DG）**有证据**；后半句（DG 早停/调度）**未被证据支持**，属**从状态变量外推**。
把两者并列会使**未验证的推论看起来像已验证的结论**。

## 改法

**拆成两句**：① 监控 DG 作诊断（附 r=−0.71 的证据）；② 明确说明**以 DG 作停止准则未获支持**，
并给出负面证据（42% 一致率 / 5 规则 0 胜）。

    python tools\_pa_fix_monitor_dg_claim.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "paper合" / "sections" / "discussion.tex"

OLD = (r"    \item \textbf{Monitor DG as an alignment health signal.} The ODE establishes DG as the natural "
       r"state variable for alignment dynamics. DG-based early stopping or learning rate scheduling are "
       r"principled applications of this insight.")

NEW = (r"    \item \textbf{Monitor DG as an alignment health signal.} The ODE establishes DG as the natural "
       r"state variable for alignment dynamics, and DG correlates with retrieval quality across the archived "
       r"runs (initial $DG^*$ against final R@1: $r = -0.71$, $n=96$). It follows that DG is worth tracking as "
       r"a diagnostic. What does not follow is that DG should replace the task metric as the quantity a "
       r"training loop is stopped on: across the same runs the epoch minimising DG and the epoch minimising "
       r"the centroid gap agree only $42\%$ of the time, and each of five realisable stopping rules derived "
       r"from the DG trajectory --- including plateau detection and a fixed early cut-off --- ends at a "
       r"centroid gap worse than training to convergence in at least $88$ of $94$ comparable runs. Monitoring "
       r"DG and stopping on DG are therefore different claims, and only the first is supported here.")


def main() -> int:
    apply = "--apply" in sys.argv
    t = io.open(F, encoding="utf-8").read()
    if "Monitoring\nDG and stopping on DG are therefore different claims" in t or \
       "only the first is supported here" in t:
        print("  已改，跳过")
        return 0
    c = t.count(OLD)
    print(f"  命中 {c} 次")
    if c != 1:
        i = t.find("Monitor DG as an alignment health signal")
        print("  实际:", repr(t[max(0, i - 80):i + 260]) if i > 0 else "（未找到）")
        return 1
    if not apply:
        print("  （预演）")
        return 0
    io.open(F, "w", encoding="utf-8", newline="").write(t.replace(OLD, NEW, 1))
    t2 = io.open(F, encoding="utf-8").read()
    for k in ("$r = -0.71$", "$42\\%$", "at least $88$ of $94$ comparable runs",
              "only the first is supported here"):
        assert k in t2, f"断言失败：缺 {k}"
    print("  ✅ 已改并断言通过")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
