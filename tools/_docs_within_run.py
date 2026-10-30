# -*- coding: utf-8 -*-
r"""落账：逐 run 排序力（τ 是唯一稳定为正的信号）（2026-10-12）。

## 结果（`tools/_p241_within_run_rank.py`）

| run | ρ(τ, top1) | ρ(val_loss, top1) |
|---|---|---|
| seed123 | +0.9515 | +0.8788 |
| seed42 | +0.8061 | **−0.7818** |
| seed456 | +0.9758 | **−0.9030** |
| **Fisher** | **+0.9380** | **−0.3708** |

**排除 ep1**：τ **+0.9142** ｜ val_loss −0.5401

    python tools\_docs_within_run.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **📈 2026-10-12 —— 补：逐 run 排序力（τ 是三条轨迹里**唯一稳定为正**的信号）**
>
> ### 为什么补
>
> `_p236` 的停止准则对照显示 τ 与「固定 ep1」**平均 top-1 相同（59.66）**，
> 因为三条轨迹的 τ 与 top-1 都从 ep1 起单调下降 → 所有准则都选 ep1。
> **"选到同一个点"不等于"τ 无信息"**，故单独测**逐 run 内的排序力**。
>
> ### 结果（`tools/_p241_within_run_rank.py`，n=10 epoch/run）
>
> | run | ρ(τ, top-1) | ρ(val_loss, top-1) |
> |---|---|---|
> | seed123 | **+0.9515** | +0.8788 |
> | seed42 | **+0.8061** | **−0.7818** |
> | seed456 | **+0.9758** | **−0.9030** |
> | **Fisher 平均** | **+0.9380** | **−0.3708** |
>
> **排除 ep1（模拟训练继续）**：τ **+0.9142** ｜ val_loss **−0.5401**
>
> ### 解读
>
> - **τ 在 3/3 个 run 内都强正相关**（+0.81～+0.98）→ 能排序检查点
> - **val_loss 在 2/3 个 run 内为负**：它的最小值出现在 ep3（seed42/456）或 ep9（seed123），
>   而那些点的 ImageNet top-1 **更低** → **优化 Flickr30k 验证损失 ≠ 保住 zero-shot**
> - τ 与 val_loss 选点分歧：seed123 差 **+1.51 点**、seed42 **+0.92**、seed456 **+0.58**（均 τ 更好）
>
> ### 因此论文的监控主张应限定为
>
> | 说法 | 可否 |
> |---|---|
> | "τ 在训练轨迹内跟踪 zero-shot 准确率" | ✅ **可以说**（Fisher +0.938，3/3 为正） |
> | "τ 排序力优于 val_loss" | ✅ **可以说**（+0.938 vs −0.371） |
> | "τ 比 top-1 **更早**报警" | 🔴 **不可说**（`_p240`：0/3 成立） |
> | "τ 比 val_loss **更早**变差" | ✅ **可以说**（`_p240`：3/3 成立） |
> | "τ 相对降幅最大" | ✅ **可以说**（τ 6.29% ＞ top-1 2.86% ＞ val_loss 1.11%） |
> | "用 τ 能做出**更好**的训练决策" | ⚠️ **本数据无法支持**——三条轨迹都是"越早越好"，任何准则都选 ep1 |
>
> **证据**：`outputs/analysis/a1_within_run_rank.json`、`a1_monitor_final.json`、
> `a1_monitor_claims_check.json`
"""


def main() -> int:
    if "--apply" not in sys.argv:
        print("  （预演）")
        return 0
    hp = REPO / "HANDOFF.md"
    t = io.open(hp, encoding="utf-8").read()
    if "唯一稳定为正" in t:
        print("  已记录")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("唯一稳定为正", "+0.9380", "−0.3708", "0/3", "3/3"):
        assert k in t2, f"断言失败：缺 {k}"
    print(f"  ✅ HANDOFF 已追加（{len(t2.splitlines())} 行）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
