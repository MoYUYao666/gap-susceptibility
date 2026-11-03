# -*- coding: utf-8 -*-
r"""精修论文的监控主张，使之与实验结果逐字一致（2026-10-12）。

## 实验（`tools/_p236`、`_p240`、`_p241`）

| 说法 | 裁决 |
|---|---|
| τ 在训练轨迹内跟踪 zero-shot 准确率 | ✅ Fisher **+0.938**（3/3 为正） |
| τ 排序力优于 val_loss | ✅ **+0.938** vs −0.371 |
| τ 比 **top-1 更早**报警 | 🔴 **0/3** |
| τ 比 **val_loss 更早**变差 | ✅ **3/3** |
| τ 相对降幅最大 | ✅ τ 6.29% ＞ top-1 2.86% ＞ val_loss 1.11% |
| 用 τ 做出**更好**的决策 | ⚠️ 本数据不支持（三条轨迹"越早越好"，任何准则都选 ep1） |

**改法**：把 `main.tex:308` 那段"两个实用要点"替换为**逐条对齐**的版本。

    python tools\_p242_refine_monitor_claim.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import re
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "paper_a1" / "main.tex"

OLD = ("Two practical points follow. First, $\\tau$ is computable from the top-$k$ class "
       "sets a validation pass already produces, so it costs no additional forward pass. "
       "Second, within a single training trajectory it tracks zero-shot accuracy closely: "
       "over the ten runs we evaluated epoch by epoch, $\\tau$ rises and falls with top-1 "
       "at a mean Pearson correlation of $0.90$ ($10/10$ runs positive; "
       "Section~\\ref{sec:epoch_sweep}).")

NEW = ("Three practical points follow, and we separate what we measured from what we did "
       "not. First, $\\tau$ is computable from the top-$k$ class sets a validation pass "
       "already produces, so it costs no additional forward pass. Second, within a single "
       "training trajectory it tracks zero-shot accuracy closely: over the ten runs we "
       "evaluated epoch by epoch, $\\tau$ rises and falls with top-1 at a mean Pearson "
       "correlation of $0.90$ ($10/10$ runs positive; Section~\\ref{sec:epoch_sweep}). "
       "Third, on the three runs for which we also have per-epoch validation loss, the "
       "ranking ability of $\\tau$ is the more reliable of the two: Spearman against "
       "zero-shot top-1 is $+0.95$, $+0.81$ and $+0.98$ for $\\tau$ (Fisher mean $+0.938$, "
       "positive in all three), against $+0.88$, $-0.78$ and $-0.90$ for the validation "
       "loss (Fisher mean $-0.371$), whose minimum arrives at epochs where zero-shot "
       "accuracy is already the lower one. On the same runs $\\tau$ falls by $6.29\\%$ "
       "relative to its first epoch while top-1 falls $2.86\\%$ and the validation loss "
       "rises $1.11\\%$, and $\\tau$ first declines no later than the validation loss in "
       "$3$ of $3$ runs but earlier than top-1 in $0$ of $3$. What these runs do \\emph{not} "
       "establish is a better stopping decision: all three trajectories are best at their "
       "first epoch, so $\\tau$, the validation loss, top-1 and a constant rule all select "
       "it, and the mean selected top-1 is $59.66\\%$ for $\\tau$ and the oracle alike, "
       "against $58.66\\%$ for validation-loss selection.")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(F, encoding="utf-8", errors="replace").read()
    n = t.count(OLD)
    print(f"  === 锚点命中 {n} ===")
    if n != 1:
        for m in re.finditer(r"Two practical points follow", t):
            ln = t[:m.start()].count("\n") + 1
            print(f"  L{ln}: {' '.join(t[m.start():m.start() + 300].split())[:280]}")
        return 1
    t2 = t.replace(OLD, NEW, 1)
    if not a.apply:
        print("  （预演）")
        return 0
    bak = F.with_suffix(".tex.bak_p242")
    if not bak.exists():
        shutil.copy2(F, bak)
    io.open(F, "w", encoding="utf-8", newline="").write(t2)
    t3 = io.open(F, encoding="utf-8", errors="replace").read()
    ok = ("+0.938" in t3 and "58.66" in t3 and "6.29" in t3)
    print(f"  {'✅ 已精修（三条主张逐条对齐实验）' if ok else '🔴 失败'}")
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
