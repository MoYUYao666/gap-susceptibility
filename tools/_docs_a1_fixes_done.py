# -*- coding: utf-8 -*-
r"""落账：A1 写作修正 6 项完成（2026-10-12）。

    python tools\_docs_a1_fixes_done.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **✍️ 2026-10-12 —— A1 写作修正 6 项完成（标题去掉 "Monitor"；组内证据入库；全套残留归零）**
>
> ### 依据
>
> 操作者选 ①②后：E-A 查清 τ 的**组内跟踪成立**（n=30 Fisher **+0.840**，单 seed **+0.945**）；
> E-B 查清 τ 的**决策价值不成立**（τ 达峰与"固定停 ep1"逐位相同：59.44/+0.05/8-of-10）。
> → 标题不得称 "Monitor"，须承诺"跟踪/诊断"。
>
> ### 改动明细（全部走 `tools/` 幂等脚本）
>
> | # | 改动 | 脚本 | 前 → 后 |
> |---|---|---|---|
> | 1 | 标题 | `_p222` | *Order Preservation as a **Zero-Overhead Monitor** …* → *Order Preservation **Tracks Zero-Shot Accuracy** …* |
> | 2 | `highlights` r=1.000 | `_p222`/`_p233` | *matches measurements with r = 1.000* → *is an identity, not independent validation* |
> | 3 | "four decimals" | `_p222` | → *three decimals*（实测残差 0.0019） |
> | 4 | `main.tex:308` 监控器句 | `_p222` | "zero-overhead training-time monitor" → "diagnostic…rather than a decision rule" + 四条停止准则对照 |
> | 5 | 新增 `sec:epoch_sweep` 小节 | `_p229` | 组内 n=30 证据（+0.670/+0.970/+0.915/+0.397，Fisher +0.840；单 seed 0.688→0.575 vs 60.14→58.14） |
> | 6 | 摘要首句 | `_p222` | "Only the second **governs** … is free to **monitor**" → "**tracks** … is free to **compute**"（+ 组内证据） |
> | 7 | 摘要词数 | `_p230` | 262 → **249**（限 250） |
> | 8 | `highlights` 3 条 | `_p233` | 2 条超 85 字符 + 1 条与结论冲突 → 全部 ≤85 字符 |
> | 9 | `abstract.tex` | `_p225` | 半成品（新标题 + 旧摘要）→ 已与 `main.tex` 同步 |
> | 10 | `cover_letter.tex` / `declaration.tex` | `_p232` | 旧标题 → 新标题（3 处） |
> | 11 | `docs/A1_VENUE_DECISION.md` | `_p228` | 加 10-10 拒稿更正（原文仍写 *Submitted to Journal*） |
>
> ### 顺带修掉一个**我造成的悬空引用**
>
> `_p222` 的正文里写了 `\\ref{sec:epoch_sweep}`，但其**小节插入**因幂等检查被跳过
> → 论文只有 `\\ref` 没有 `\\label`（会渲染成 `??`）。
> `tools/_p229_insert_epoch_section.py` 已补上小节定义；
> 复编译：**0 undefined**（此前若编译会是 1 个）。
>
> ### 最终核验（`tools/_final_review.py`）
>
> ```
> A1：6 份干净 ｜ 摘要 249 词 ｜ 关键词 5 ｜ highlights 5 条（最长 69 字符）｜ 文献 56 条
>     main 42 页 ｜ cover_letter 2 ｜ declaration 1 ｜ highlights 1 ｜ abstract 1 —— 全部 0 错误
> paper合：门禁 80/80 ｜ 统计审核 20/20 ｜ 旧数字残留 0 ｜ Springer 41 页 ｜ NC 56 页
> 检查结论：✅ 全部通过
> ```
>
> **`tools/_p231_scan_a1_stale.py`：A1 全套旧主张残留 = 0。**
>
> ### 当前 A1 的真实定位
>
> | 主张 | 状态 |
> |---|---|
> | τ 在一个数据集内跟踪 zero-shot 准确率 | ✅ **强支撑**（+0.84～+0.945） |
> | 模态差不是通用健康指标 | ✅ 支撑（34 条件 + 17 检查点） |
> | 闭式偏置场 | ⚠️ **恒等式/自洽检查**（已如实降级） |
> | τ 可用于训练决策（监控器） | 🔴 **已删除该主张**（E-B 证明无优势） |
>
> **证据**：`outputs/a1_epoch_sweep.json`、`outputs/analysis/a1_epoch_sweep_analysis.json`、
> `a1_monitor_baseline.json`、`a1_monitor_decision.json`
"""


def main() -> int:
    if "--apply" not in sys.argv:
        print("  （预演）")
        return 0
    hp = REPO / "HANDOFF.md"
    t = io.open(hp, encoding="utf-8").read()
    if "A1 写作修正 6 项完成" in t:
        print("  已记录")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("A1 写作修正 6 项完成", "Tracks Zero-Shot Accuracy", "249", "悬空引用",
              "旧主张残留 = 0"):
        assert k in t2, f"断言失败：缺 {k}"
    print(f"  ✅ HANDOFF 已追加（{len(t2.splitlines())} 行）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
