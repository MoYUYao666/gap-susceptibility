# -*- coding: utf-8 -*-
r"""把两处**理论否证**写进 `discussion.tex` 的 limitation（2026-10-10）。

## ① `f(DG₀)` 的绝对预测失败（`tools/_p86`）

| 量 | 实测 |
|---|---|
| `f(DG₀)` 高精度（30 批 × 2 seed × 3 位置） | **+66.71 ± 4.82** |
| 归档 `α_fit = −2.7743e−3` → 对应 `f_fit` | **−27.74** |
| 覆盖？ | ❌ **不覆盖**（**符号相反**、量级差 **2.4×**） |
| 三位置的 `f` | +66.63 / +67.22 / +66.28（**极差 1.4%**，CI ±8.3 远大于差异） |
| 单批 SNR | **0.37–1.04** |

**但**：`prospective_results.json` 里 `α_pred` 与 `α_obs` **6/6 同号**、中位相对误差 **34%**
（`α` 的范围：pred 0.034–0.065｜obs 0.042–0.074）→ **相对次序可预测，绝对标定不行**。

## ② 驱动项**排序**不成立（`tools/_p81`）

| 臂 | 轨迹平均驱动项 | 实测 CGΔ |
|---|---|---|
| `text_only` | **+10.83** | **−0.0465**（最好） |
| `vision_only` | +10.24 | +0.0106（最差） |
| `both` | **+9.16** | −0.0258 |

→ 理论排序 `text_only > vision_only > both`｜实测排序 `text_only > both > vision_only`
→ **只有最好的那个位置被预测对，其余两个顺序错了**（极差 16.5% vs 实测 277%）。

## 改动

插入 **Seventh**（绝对预测）与 **Eighth**（排序），原 Seventh → Ninth。

    python tools\_pa_limitation_falsification.py [--apply]
"""
from __future__ import annotations

import io
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "paper合" / "sections" / "discussion.tex"

ANCHOR = "Seventh, the trajectories analysed here are a subset"

NEW = r"""Seventh, the absolute value of the driving coefficient is not predicted
correctly by the gradient identity. Estimating
$f(DG_0)=\langle\nabla_\theta DG^*,\nabla_\theta\mathcal{L}\rangle$ from thirty batches
at each of the three positions and two seeds gives $+66.7\pm4.8$, whereas the $\alpha$
fitted to the archived trajectories implies $-27.7$: the two disagree in sign and by a
factor of $2.4$, and the discrepancy is not sampling noise, since the standard error of
the estimate is $4.8$. The identity therefore holds as a per-step statement, verified
against the change an actual optimiser step produces, but it does not supply the
coefficient. The sign and rough magnitude of $\alpha$ are nevertheless reproduced by the
separate closed-form route of Section~\ref{sec:theory}, which agrees with the fitted
values in sign across all six pilot configurations at a median relative error of $34\%$;
what fails is the absolute calibration, not the relative ordering.
Eighth, the ordering of the three adaptation positions is not reproduced by the
trajectory-averaged driving coefficient. Averaging over an epoch of training gives $+10.8$
for text-only, $+10.2$ for vision-only and $+9.2$ for the both-position arm, a spread of
$16.5\%$, whereas the measured gap changes span $277\%$ of their mean and order the arms
differently, placing both-position ahead of vision-only. The coefficient therefore
identifies the best position but does not rank the other two, and the ordering we report
rests on the measured gap changes rather than on this quantity. """


def main() -> int:
    apply = "--apply" in sys.argv
    t = io.open(F, encoding="utf-8").read()
    if "does not supply the\ncoefficient" in t or "does not supply the coefficient" in t or "$2.4$" in t:
        print("  已写，跳过")
        return 0
    if t.count(ANCHOR) != 1:
        print(f"  ❌ 锚点未唯一命中（{t.count(ANCHOR)}）")
        return 1
    t = t.replace(ANCHOR, NEW + "Ninth, the trajectories analysed here are a subset", 1)
    if not apply:
        print("  （预演）")
        return 0
    io.open(F, "w", encoding="utf-8", newline="").write(t)
    t2 = io.open(F, encoding="utf-8").read()
    i = t2.find("Several limitations"); j = t2.find("Several extensions")
    ords = re.findall(r"(First|Second|Third|Fourth|Fifth|Sixth|Seventh|Eighth|Ninth),", t2[i:j])
    print(f"  序号现为: {ords}")
    assert len(ords) == len(set(ords)), "序号有重复"
    for k in ("$+66.7\\pm4.8$", "$-27.7$", "$16.5\\%$", "$277\\%$", "Ninth, the trajectories"):
        assert k in t2, f"断言失败：缺 {k}"
    print("  ✅ 已加 Seventh（绝对预测失败）与 Eighth（排序不成立），原 Seventh → Ninth")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
