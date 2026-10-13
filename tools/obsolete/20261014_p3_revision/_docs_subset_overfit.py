# -*- coding: utf-8 -*-
r"""落账：我的 0.679 舍入错 + "子集匹配不构成来源"的量化（2026-10-12）。

    python tools\_docs_subset_overfit.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **🔴 2026-10-12（续）—— 修正我自己的 0.679 舍入错；并量化「子集匹配不构成来源」**
>
> ### 我错了（队友 model-coverage 指出，我实测确认）
>
> `strict_freeze_rank/r4/both` 逐 seed = **0.6770 / 0.6800 / 0.6820** → 均值 **0.6796667**：
> `round(…,3)` = **0.680**，**只有截断**才得 0.679。
> → 我上一版 caption 把 `round` 的结果写成 0.679，**错**。已改。
>
> 替代者（队友给出，我实测成立）：`strict_freeze_b32_r4/both` 的 seeds **42/123/456**
> → 0.680 / 0.685 / 0.673 → 均值 **0.6793333 → round = 0.679** ✅（且与该行**同树**）。
>
> ### 但「允许 3-seed 子集 ⇒ 三格全可达」是**统计假象**（我量化后驳回）
>
> `tools/_p330_subset_overfit_check.py`：
>
> | 目标 | 命中它的 3-seed 子集候选数 |
> |---|---|
> | 0.679 | **43** |
> | 0.651 | **39** |
> | 0.621 | **17** |
>
> 全部 3-seed 子集候选数 = **4581**，均值范围 **[0.0002, 0.7137]**，
> `round(…,3)` 后覆盖 **299** 个不同三位小数值
> → **约 1% 的候选会随机命中任何给定值**。
> **→ "能找到 3-seed 子集命中"对三个目标都成立 ⇒ 该判据筛不出任何东西，不构成溯源证据。**
>
> 队友的**自我更正方向对**（"无来源"太绝对），但**不能反向过头**成"其实有来源"。
> 最终三类：`own_tree_exact 6` / `another_tree_explains 3` /
> **`unreproducible_at_printed_precision 3`**。
>
> ### caption 最终写法（已编译、提交 `8c9e743`）
>
> > 94 个 n≥3 组的**完整 seed 集**均值**没有任何组**四舍五入到 0.651 或 0.679；
> > 能找到四舍五入到这两个值的 3-seed 子集，但**不作为来源**——4581 个子集中
> > 39 个命中 0.651、43 个命中 0.679，**亚组匹配在此精度无证据力**。
> > 该表的比较建立在 **ΔCG 列**，**12 格全部精确复现**。
>
> ### 本阶段我的错（累计 5 个，全部已修并留档）
>
> | # | 错 | 被谁发现 |
> |---|---|---|
> | 1 | PowerShell 内联写 LaTeX 吞 `$` → 编译错 | 编译器 |
> | 2 | `\\item` 插进散文小节 → `Lonely \\item` | 编译器 |
> | 3 | 替换串写成 `\\$R^2\\$` → 6 个编译错 | 编译器 |
> | 4 | 压摘要删掉混合效应（R1.2 的答复） | 我自己的审计脚本 |
> | 5 | **0.679 舍入写成 round 结果**（实为 trunc） | 队友 model-coverage |
>
> **共性**：**未穷举 / 粒度不对 / 未核舍入口径就下结论**。
> 本阶段已因此被队友纠正两次（另一个是"88 of 94 无归档"）。
> **纪律**：凡"X 无来源""X 无匹配"这类**全称否定**，必须先穷举 + 固定精度口径 + 说明判据。
>
> ### 状态
>
> | 稿 | 页数 | 错误 | 未定义 | Overfull |
> |---|---|---|---|---|
> | `main_nc` | **60** | 0 | 0 | 0 |
> | `main_springer` | **44** | 0 | 0 | 0 |
> | 投稿包 | **60** | 0 | 0 | — |
>
> **仍在跑**：task-7（更全 lr 网格，GPU 7.7/8.2 GB）｜task-8（DINOv2 等卡）
"""


def main() -> int:
    if "--apply" not in sys.argv:
        print("  （预演）")
        return 0
    hp = REPO / "HANDOFF.md"
    t = io.open(hp, encoding="utf-8").read()
    if "修正我自己的 0.679 舍入错" in t:
        print("  已记录")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("修正我自己的 0.679 舍入错", "0.6796667", "4581", "43", "trunc"):
        assert k in t2, f"断言失败：缺 {k}"
    print(f"  ✅ HANDOFF 已追加（{len(t2.splitlines())} 行）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
