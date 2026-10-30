# -*- coding: utf-8 -*-
r"""Record that both Pattern Recognition gaps are now closed.

    python tools/_p1190_record_gaps_closed.py [--apply]
"""
from __future__ import annotations

import argparse
import io
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DOC = REPO / "docs" / "PAPERA_PR_REVIEW_COVERAGE_2026-10-17.md"
HANDOFF = REPO / "HANDOFF.md"

APPEND = """

## 五点五、缺口已闭合（2026-10-17 23:10）

| 缺口 | 处理 | 证据 |
|---|---|---|
| **R2-W4 替代解释未明说** | 局限节新增 **Thirteenth** 条：承认正则化强度与模态特定优化动力学可能产生同一排序；明确指出保留的两条证据（梯度信噪比、有效秩变化）是**相关性**证据；并说明设计用来分离二者的噪声实验已撤回 | `discussion.tex`（局限节）|
| **R1-Q2 配置差异缺对照表** | 补充新增 **A.1 节 + Table 9（`tab:config_groups`）**，四组 × 三列：Core LoRA / Route D / Layered / Strict-freezing，逐组给出 Settings 与"为何数字不可互换" | `supplement.tex` A.1 |
| **R1-W1 `+0.079` 的根因** | 由归档**逐字段核实**：`d1_alpha64_text_r8`（Route D）与 core `alpha_64` 同为 $r=8$、$\\alpha=64$、145,170,177 可训练参数，但验证损失 **2.331 vs 0.499**、R@1 **0.389 vs 0.637** ⇒ 是**退化拟合**，不是"另一种配置"。正文改判句已按此重写 | `outputs/route_d/d1_alpha64_text_r8/results.json`；`outputs/flickr30k/alpha_64/results.json`；`empirical.tex` |

**数值依据（可直接复核）**：Route D 全组 d1 +0.079 / d2 +0.183 / d3 +0.164 / d4 +0.188 / d5 +0.196；core $\\alpha$ 扫描
$\\alpha=4$ $-0.017$ → $\\alpha=64$ $-0.081$（验证损失 0.499–0.541）。复跑脚本：`tools/_p1184_diff_disputed_runs.py`。

**重建结果**：NC **70 页**、Springer **50 页**，均 0 错误 / 0 未定义 / 0 Overfull / 0 float-too-large；
投稿包已刷新并独立编译 **70 页一致**；台账 **76/76**、主台账 **96/96**。
"""

ENT = """> **🧩 2026-10-17 23:10 —— 补上 PR 审稿复审发现的两处缺口（Paper A）**
>
> 按操作者"补"的指示，把 `docs/PAPERA_PR_REVIEW_COVERAGE_2026-10-17.md` 里列出的两处缺口闭合：
>
> ### ① R2-W4 替代解释（已在局限节补 **Thirteenth** 条）
> 承认"正则化强度 / 模态特定优化动力学"可能产生同一排序；明确保留的两条证据（梯度信噪比、有效秩变化）是**相关性**证据；
> 并指出本可分离二者的噪声实验已主动撤回 ⇒ VF 是"与严格冻结对照最一致的**解释**"，非既定机制。
>
> ### ② R1-Q2 配置差异（补充新增 **A.1 节 + Table 9 `tab:config_groups`**）
> 四组并列：Core LoRA / Route D / Layered unfreezing / Strict-freezing，逐组给 Settings 与"为何数字不可互换"。
>
> ### ③ 顺带查清 `+0.079` 的真正根因（R1-W1 的核心）
> 归档逐字段对比：Route D 的 `d1_alpha64_text_r8` 与 core `alpha_64` **同名义配置**（$r=8$、$\\alpha=64$、145,170,177 参数），
> 但验证损失 **2.331 vs 0.499**、R@1 **0.389 vs 0.637** ⇒ **退化拟合**，不是"另一种配置"。
> 正文改判句已改写为如实表述（原句"belongs to a different configuration, $\\alpha=64$"会误导，已替换）。
>
> **重建**：NC **70 页** / Springer **50 页**（0 错误 / 0 未定义 / 0 Overfull / 0 float-too-large）；
> 投稿包独立编译 **70 页一致**；台账 **76/76**、主台账 **96/96**。
> 排版过程修了三次：array 包未加载（非法列语法）→ 去掉 `\\raggedright` 保持 `p` 列 → 最终改用 `\\parbox` + `\\raggedright`（无需包）。
>
> **脚本**：`_p1185`（两处补丁）｜`_p1186`–`_p1189`（表格重排三次）｜`_p1184`（争议 run 逐字段对比）｜`_p1190`（本条）。
>

"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not a.apply:
        print("  (dry run)")
        return 0
    t = io.open(DOC, encoding="utf-8").read()
    if "缺口已闭合" not in t:
        io.open(DOC, "w", encoding="utf-8", newline="").write(t.rstrip("\n") + APPEND)
        print("  coverage doc updated")
    hp = io.open(HANDOFF, encoding="utf-8").read()
    if "补上 PR 审稿复审发现的两处缺口" not in hp:
        i = hp.find("# 项目交接文档")
        j = hp.find("\n", i)
        io.open(HANDOFF, "w", encoding="utf-8", newline="").write(hp[: j + 1] + "\n" + ENT + hp[j + 1:])
        print("  handoff entry added")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
