# -*- coding: utf-8 -*-
r"""把 `dg_pred` 的偏差写进 `discussion.tex` 的 limitation（2026-10-10）。

## 实测（`tools/_p88_dg_pred_bias.py` → `outputs/analysis/dg_pred_bias.json`）

6 个 pilot 配置的预测 `DG*` 与实际 `DG*`：

| 量 | 实测 |
|---|---|
| 实测 / 预测 中位比 | **2.44×**（系统性偏低） |
| 预测极差 / 实测极差 | **0.223 / 0.067 = 3.33×**（变化被高估） |
| `corr(dg_pred, dg_actual)` | **+0.225** |
| 变化方向一致 | **2/5** |

## 改动

在 Fifth 之后插入 **Sixth**（`dg_pred` 的样本外偏差），原 Sixth 顺延为 **Seventh**。

    python tools\_pa_limitation_dgpred.py [--apply]
"""
from __future__ import annotations

import io
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "paper合" / "sections" / "discussion.tex"

ANCHOR = "Sixth, the trajectories analysed here are a subset"

NEW_SIXTH = r"""Sixth, the ODE reproduces the shape of individual trajectories well, but its
absolute prediction of the converged gap is biased and its configuration ordering
is not reliable. Across the six pilot configurations for which both quantities were
recorded, the predicted final $DG^*$ is systematically below the measured value, by
a median factor of $2.44$; the spread of predictions across configurations is
$3.33$ times the spread actually measured ($0.223$ against $0.067$); the correlation
between predicted and measured values is $+0.225$; and the predicted change between
configurations moves in the same direction as the measured change in only two of
five comparisons. The sign of $\alpha$ is predicted correctly and its magnitude to
within a median relative error of $34\%$, so the framework captures the direction
and rough size of the perturbation; what it does not yet deliver is a quantitative
forecast of the steady state, and we therefore report the fitted coefficients rather
than the closed-form prediction throughout Section~\ref{sec:validation}. """


def main() -> int:
    apply = "--apply" in sys.argv
    t = io.open(F, encoding="utf-8").read()
    if "median factor of $2.44$" in t:
        print("  已写，跳过")
        return 0
    if t.count(ANCHOR) != 1:
        print(f"  ❌ 锚点未唯一命中（{t.count(ANCHOR)}）")
        return 1
    t = t.replace(ANCHOR, NEW_SIXTH + "Seventh, the trajectories analysed here are a subset", 1)
    if not apply:
        print("  （预演）")
        return 0
    io.open(F, "w", encoding="utf-8", newline="").write(t)
    t2 = io.open(F, encoding="utf-8").read()
    i = t2.find("Several limitations"); j = t2.find("Several extensions")
    lim = t2[i:j]
    ords = re.findall(r"(First|Second|Third|Fourth|Fifth|Sixth|Seventh|Eighth),", lim)
    print(f"  序号现为: {ords}")
    assert len(ords) == len(set(ords)), "序号有重复"
    for k in ("median factor of $2.44$", "+0.225", "two of\nfive comparisons" if "\n" in t2 else "five comparisons",
              "median relative error of $34\\%$", "Seventh, the trajectories"):
        assert k in t2, f"断言失败：缺 {k}"
    print("  ✅ discussion.tex 已加 Sixth（dg_pred 偏差），原 Sixth → Seventh")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
