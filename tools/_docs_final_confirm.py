# -*- coding: utf-8 -*-
r"""最终确认阶段的记录（2026-10-05）：修 3 处计数/摘要问题 + 全量验证通过。

    python tools\_docs_final_confirm.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENTRY = r"""> **✅ 2026-10-05 —— 最终确认：修 3 处计数问题，全量验证通过**
>
> 操作者要求："**最后再确认一遍**"。逐项复核中发现并修正 **3 处真问题**。
>
> ### 修正 ①（重要）：摘要里残留旧计数 278
>
> `main_nc.tex` 与 `main_springer.tex` 的**摘要**仍写
> "Validation spans **278** experiments" —— 这是**上一轮计数更正时漏掉的**：
> 当时只改了 `sections/*.tex`，**没改两版 `main*.tex` 的摘要**。
> 已改为 **374**（全文 `278` 残留现为 **0 处**）。
>
> ### 修正 ②（重要）：目录表 Total 与表内求和不符
>
> 上一轮把目录表 `Total` 由 **117** 改成 **374**，用的是**全文口径**（117+162 ODE+95）。
> **但那张表只列按类别的实验目录，不含 ODE 拟合** → **各类求和 212 ≠ Total 374**。
>
> | 版本 | 各类求和 | 表中 Total | 自洽 |
> |---|---|---|---|
> | 改动前 | 117 | 117 | ✅ |
> | 上一轮改动后 | **212**（117+95） | **374** | **❌** |
> | **本次修正后** | **212** | **212** | ✅ |
>
> **并更正附录构成说明**：上一轮写的"117 mechanism + 162 ODE + 95 strict-freezing"**把严格冻结
> 既算进目录又单列，重复计数**。正确构成为：
>
> | 组 | 数 |
> |---|---|
> | 附录目录（13 类机理 + 第 XIV 类严格冻结） | **212** |
> | ODE 拟合（`validation.tex`） | 162 |
> | **全文合计** | **374** |
>
> 全文其余各处的 **374**（摘要、introduction、empirical、conclusion、validation）用全文口径，**正确，未动**。
>
> 核算脚本：`tools/_check_catalog_sum.py`（会断言"求和 = Total"）、
> `tools/_verify_experiment_counts.py`；修正脚本 `tools/_pa_fix_catalog_total.py`。
>
> ### 修正 ③（次要）：摘要计数在两版之间的一致性
>
> 两版（Elsevier / Springer）摘要现已一致（均为 374）。
>
> ### 排查过但**不是**问题的两项（如实记录）
>
> | 现象 | 结论 |
> |---|---|
> | `main_nc.log` 有 2 处 `Overfull \hbox`（60.96pt / 20.70pt，指向摘要区） | **无实际越界**：把 page 10 渲染成图目视核对，图、图注、文字**都在页边内**；`pdftotext -bbox` 实测文字最右 **477.5pt** < 右边距起点 540pt。属 LaTeX 对浮动体盒子的度量告警 |
> | 我以为"图片溢出" | 经算：图被缩放到 **303.6pt**（= 0.88×345），**未超 textwidth**。我先前的公式推导有误，**已放弃该假设** |
>
> ### 全量验证结果（复跑命令见 `docs/PAPERA_PREFLIGHT_AUDIT.md`）
>
> | 项 | 结果 |
> |---|---|
> | 编译（从零，两版） | NC **43 页** / Springer **32 页**，**0 错误、0 未定义引用** |
> | 引用 | cites **44** = bib **44**，缺失 0、未使用 0 |
> | 结构 | 悬空 `\ref` **0**、重复 label **0**、占位符 **0**、图文件缺 **0** |
> | 编号 | 图 12/12、表 8/8 label 一致 |
> | 摘要 | **244 词** ≤ 250；NC/Springer 一致 |
> | 声明 | 5 节齐备且位于参考文献之前 |
> | Highlights | 5 条，最长 59 字符 |
> | 核心主张复算 | 严格冻结 5-seed 方向与排序 ✅；`R² > 0.96` ✅ |
> | 实验计数 | 目录表求和 = Total = **212**；全文 **374**；`278`/旧 `117` 残留 **0** |
> | 图来源 | **12/12** 有生成脚本与源 JSON（`docs/PAPERA_FIGURE_PROVENANCE.md`） |
> | k | 全稿无 `k=0.043`；改为实测区间（10% vs √r 预测 8 倍） |
> | 投稿包 | 已重建，`tools/_pa_final_check_nc.py` **全绿** |
>
> ### 结论
>
> **Paper A 可以投稿。** 唯一未决变量仍是 **P1（`PR-D-26-10149`）的决定**——
> 它决定本稿的投稿时点与定位（见本日 P1 状态条目）。

"""


def main() -> int:
    apply = "--apply" in sys.argv
    p = REPO / "HANDOFF.md"
    t = io.open(p, encoding="utf-8").read()
    if "最终确认：修 3 处计数问题" in t:
        print("  已记录，跳过")
        return 0
    anchor = "> **🖼️ 2026-10-05 —— 图来源重绘"
    i = t.find(anchor)
    if i < 0:
        print("  ⚠ 未找到锚点")
        return 1
    if apply:
        io.open(p, "w", encoding="utf-8", newline="").write(t[:i] + ENTRY + t[i:])
        t2 = io.open(p, encoding="utf-8").read()
        for k in ("修 3 处计数问题", "212", "Overfull", "可以投稿"):
            assert k in t2, f"断言失败：缺 {k}"
        print(f"  ✅ HANDOFF 已追加（{len(t2.splitlines())} 行）")
    else:
        print("  （预演）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
