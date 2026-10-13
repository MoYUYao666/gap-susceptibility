# -*- coding: utf-8 -*-
r"""落账：E-B 监控决策实验（结论：τ 在决策上无优势）（2026-10-12）。

## 结果（`tools/_p220`、`_p221`，100 个检查点 / 10 条轨迹）

| 准则 | 平均 top-1 | 平均损失 | 零损失轨迹 |
|---|---|---|---|
| **固定 epoch 1（无信号）** | **59.44** | **+0.05** | 8/10 |
| ★ **τ 达峰** | **59.44** | **+0.05** | 8/10 |
| top-1 达峰（需标签） | 59.49 | +0.00 | 10/10 |
| 训到 epoch 10 | 57.14 | +2.35 | 0/10 |

**D1（谁先报警）**：τ 首次下降更早的轨迹 **2/10** → **τ 不早于 top-1**

→ **τ 在组内跟踪准确率是真的；但在"何时停"的决策上，与"不看信号"无差别。**

    python tools\_docs_expB.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **📉 2026-10-12 —— E-B 监控决策实验：τ 在"何时停"上**无额外价值**（标题不能称 monitor）**
>
> ### 背景
>
> 操作者选 ①②后，补做 E-A（组内排序力）与 E-B（监控决策闭环）。
> E-A 更正为：**τ 组内跟踪良好**（n=30 Fisher **+0.840**，单 seed **+0.945**）。
> E-B（本条目）检验 **τ 能否用于训练决策**。
>
> ### E-B 数据
>
> `outputs/a1_epoch_sweep.json`（100 个检查点 = **10 条完整训练轨迹** × epoch1–10，
> 每条含逐 epoch 的 τ 与 ImageNet 5k top-1）。**无需新训练。**
>
> ### E-B 结果 ①：停止准则对照（`tools/_p221_monitor_baseline.py`）
>
> | 准则 | 平均 top-1 | 平均损失 vs 已知最优 | 零损失轨迹 |
> |---|---|---|---|
> | **固定 epoch 1（完全不看信号）** | **59.44** | **+0.05** | 8/10 |
> | ★ **τ 达峰（本方法）** | **59.44** | **+0.05** | 8/10 |
> | top-1 达峰（需 ImageNet 标签，非零开销） | 59.49 | +0.00 | 10/10 |
> | 固定 epoch 2 | 58.80 | +0.69 | 2/10 |
> | 固定 epoch 3 | 58.17 | +1.32 | 0/10 |
> | 训到 epoch 10 | 57.14 | +2.35 | 0/10 |
>
> **→ τ 达峰与「固定停在第 1 轮」逐位相同（59.44 / +0.05 / 8-of-10）**
> → **在"何时停"的决策上，τ 未显示超出"什么都不看"的价值。**
>
> ### E-B 结果 ②：谁先报警（`tools/_p220` D1 + `_p221` ④修正）
>
> 用「首次单调下降」（τ_e < τ_{e−1}）判据：**τ 更早的轨迹 2/10**。
> 原用"跌破起点 90%"的判据更差（6 条中仅 2 条更早）。
> → **τ 并不比 top-1 更早发现问题**（本数据上：两者多在 epoch 2 同时首降）。
>
> ### 结论（对标题的影响）
>
> | 论文/我的主张 | 实况 |
> |---|---|
> | τ 组内跟踪准确率 | ✅ **成立且强**（+0.84～+0.945） |
> | τ 是"更早/更敏感"的指示器 | 🔴 **本数据不支持**（2/10） |
> | τ 可用于训练决策（监控器） | 🔴 **与"不看信号"无差别** |
>
> **→ 标题不得称 "monitor"；应承诺"跟踪/诊断"，并把"决策价值未被证明"写成限制。**
>
> ### 诚实标注
>
> - 本实验**无逐 epoch 的验证损失**（归档里没有），故对照用 top-1；
>   这是本实验的限制，已写进 `outputs/analysis/a1_monitor_baseline.json`。
> - 10 条轨迹均为 **10 epoch** 的短训练；更长训练下结论可能不同——**未测，不主张**。
> - **E-A 更正**（见上一条目）：我此前"Simpson 悖论/推翻核心主张"的判断是 **n=3 噪声假象**。
>
> **证据**：`tools/_p218_eval_all_epochs.py`、`_p219_analyze_epoch_sweep.py`、
> `_p220_monitor_decision.py`、`_p221_monitor_baseline.py`；
> `outputs/analysis/a1_epoch_sweep_analysis.json`、`a1_monitor_decision.json`、
> `a1_monitor_baseline.json`
"""


def main() -> int:
    if "--apply" not in sys.argv:
        print("  （预演）")
        return 0
    hp = REPO / "HANDOFF.md"
    t = io.open(hp, encoding="utf-8").read()
    if "E-B 监控决策实验" in t:
        print("  已记录")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("E-B 监控决策实验", "59.44", "+0.840", "+0.945", "2/10",
              "标题不得称"):
        assert k in t2, f"断言失败：缺 {k}"
    print(f"  ✅ HANDOFF 已追加（{len(t2.splitlines())} 行）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
