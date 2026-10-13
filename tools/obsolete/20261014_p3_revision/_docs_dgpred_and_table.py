# -*- coding: utf-8 -*-
r"""落账：`dg_pred` 写进 limitation + 表格改 3-seed 均值 + 门禁 46/46（2026-10-10）。

    python tools\_docs_dgpred_and_table.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **📝 2026-10-10 —— `dg_pred` 进 limitation；`tab:position_strict` 改 3-seed 均值；门禁 46/46**
>
> ### ① `dg_pred` 偏差写进 `discussion.tex`（新 **Sixth** limitation）
>
> 操作者要求把 `dg_pred` 的问题写进 limitation。**实测数据**（`tools/_p88_dg_pred_bias.py`）：
>
> | 量 | 实测 |
> |---|---|
> | 实测 / 预测 中位比 | **2.44×**（系统性偏低） |
> | 预测极差 / 实测极差 | **0.223 / 0.067 = 3.33×**（变化被高估） |
> | `corr(dg_pred, dg_actual)` | **+0.225** |
> | 变化方向一致 | **2/5** |
>
> **处置**：在 Fifth（`α`/`β` 为拟合而非预测）**之后**插入 **Sixth**，
> 写明"框架捕捉了扰动的**方向**与**粗略量级**（`α` 同号、中位相对误差 34%），
> **但不提供稳态的定量预测**，故全篇报告**拟合系数**而非闭式预测"。
> **原 Sixth（轨迹为子集）顺延为 Seventh。**
>
> ### ② 发现并修掉一处**口径不一致**（自查发现）
>
> **门禁跑出 10 条失败**，查清是：**`tab:position_strict` 的 `r4` 两行用的是**单个 seed**，
> 而表注却写 *"single-seed runs"*——但我在 2026-10-09 已把每个 r4 补到 3 seed。**
>
> **处置**：**表格改用 3-seed 均值**（更稳健），表注同步改为 *"three-seed means"*：
>
> | (骨干, 臂) | 原（单 seed） | **现（3-seed 均值）** |
> |---|---|---|
> | B/32 r4 text_only | −0.0297 / 0.625 | **−0.0288 / 0.621** |
> | B/32 r4 both | −0.0186 / 0.680 | **−0.0188 / 0.679** |
> | B/32 r4 vision_only | +0.0124 / 0.668 | **+0.0127 / 0.670** |
> | B/16 r4 text_only | −0.0190 / 0.642 | **−0.0172 / 0.651** |
> | B/16 r4 both | +0.0150 / 0.696 | **+0.0107 / 0.707** |
> | B/16 r4 vision_only | +0.0433 / 0.677 | **+0.0313 / 0.686** |
>
> **排序不变**（三骨干仍 `text_only` 最保护）✅
>
> ### ③ 门禁修到 **46/46 通过**（退出码 0）
>
> 顺带修掉两处会导致门禁失败的问题：
> 1. 台账的 r4 断言从"第一个 seed"改为"**全目录 seed 均值**"；
> 2. 台账读 Qwen 的路径补上 `4bit/` 子目录（4-bit 结果被我移到该目录后路径失配）。
> **并新增 6 条主张**（`dg_pred` 的 2.44 / 3.33 / 0.223 / 0.067 / 0.225 与 `α` 的 34%）。
>
> ### ④ 编译
>
> | 版本 | 页数 | 错误 | 未定义 | Overfull |
> |---|---|---|---|---|
> | Springer | **40** | 0 | 0 | 0 |
> | NC | **54** | 0 | 0 | 0 |
>
> ### 下一条（操作者已定）
>
> **A1（`paper_a1/`）不接转投，先完善再投** —— 待办见下一条目。
"""


def main() -> int:
    apply = "--apply" in sys.argv
    if not apply:
        print("  （预演）")
        return 0
    hp = REPO / "HANDOFF.md"
    t = io.open(hp, encoding="utf-8").read()
    if "`dg_pred` 偏差写进 `discussion.tex`" in t:
        print("  已记录，跳过")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("`dg_pred` 偏差写进 `discussion.tex`", "2.44×", "3.33×", "口径不一致",
              "46/46 通过", "three-seed means"):
        assert k in t2, f"断言失败：缺 {k}"
    print(f"  ✅ HANDOFF 已追加（{len(t2.splitlines())} 行）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
