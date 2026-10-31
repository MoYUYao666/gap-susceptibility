# -*- coding: utf-8 -*-
r"""落账 Paper A 封面信（2026-10-07）。

交付件：`paper合/cover_letter.tex` + `cover_letter.pdf`（2 页，0 错误）。

**要点**：
1. **主题与贡献**（三段式：实证刻画 → 梯度流理论 → 跨架构验证）；
2. **点出最值得编辑注意的结果**（text-only 的"保护性"在 SigLIP 上反转；7 配置下由 patch size 决定）；
3. **与先前工作的关系**（引 AdaLoRA / LoRA-GA / CLIP-LoRA 三条已发表文献，说明边界）；
4. **披露三篇相关稿件**（P1 在 PR、综述在 PRL、A2 在 IEEE JOE）——**这是本信的关键**；
5. **可复现性**（每个数字有归档文件 + 脚本；每张图有断言脚本）；
6. **合规**（Highlights 5 条 / 摘要 238 词 / 关键词 6 / 五项声明）。

    python tools\_docs_cover_letter.py [--apply]
"""
from __future__ import annotations

import io
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = r"""> **✉️ 2026-10-07 —— Paper A 封面信已起草（操作者要求）**
>
> **交付件**：**`paper合/cover_letter.tex`** + `cover_letter.pdf`（**2 页、0 错误**）。
>
> ### 内容结构（六段）
>
> 1. **主题与贡献**：三段式——**实证刻画**（n=204；DG r=−0.71 vs CG r=−0.59；位置 > 配置）→
>    **梯度流理论**（Gap Susceptibility、一阶 ODE、R²=0.986）→ **跨架构验证**（383 实验 / 5 架构 / 3 种 PEFT / 2 数据集）；
> 2. **点出最值得编辑注意的结果**：text-only 的"保护性"**在 SigLIP 上反转**；**7 个严格冻结配置下由 patch size 决定，无例外**；
> 3. **与先前工作的关系**：引 **AdaLoRA / LoRA-GA / CLIP-LoRA** 三条**已发表**文献，
>    说明其边界（单骨干单语料）→ 我们把排序当**待检验假设**跨 7 骨干测；
> 4. **🔑 披露三篇相关稿件**（本信关键）：
>    - **P1** 在 *Pattern Recognition*（**前身**；本稿为其扩展与取代版）；
>    - **综述** 在 *Pattern Recognition Letters*（**文献综述、无自有实验**；与其共享**一条**结论——
>      位置主导预算分配——但**来源不同**：它是文献归纳，本稿是直接测量）；
>    - **A2** 在 *IEEE Journal of Oceanic Engineering*（**题材无关**）。
> 5. **可复现性**：每个数字有归档结果文件 + 命名脚本；**每张图由断言过其主张的脚本生成**；发表后公开；
> 6. **合规**：Highlights **5 条**（最长 **61** 字符）｜摘要 **238 词**｜关键词 **6** 个｜五项声明齐备。
>
> ### 核对（逐项与稿件实测比对，全部一致）
>
> | 项 | 封面信 | 实测 |
> |---|---|---|
> | 摘要词数 | 238 | **238** ✅ |
> | 关键词 | 6 | **6** ✅ |
> | Highlights | 5 条、最长 61 | **5 条、最长 61** ✅ |
> | 页数 | 49 | **49** ✅ |
> | n=204 / r=−0.71 / r=−0.59 | 有 | 稿件 8 / 8 / 4 处 ✅ |
> | R²=0.986 / 0.00 / 0.946 | 有 | 稿件 10 / 5 / 4 处 ✅ |
> | 383 实验 / 5 架构 / 3 方法 / 7 配置 | 有 | 稿件 9 / 3 / 3 / 2 处 ✅ |
>
> ### ⚠️ 投稿前必办
>
> **替换占位符**：`paper合/cover_letter.tex` 第 6 行
> `\newcommand{\journal}{[TARGET JOURNAL — replace before submission]}`
> → 填入目标刊名（CVIU 或 ESWA）并**重编译**。
"""


def main() -> int:
    apply = "--apply" in sys.argv
    if not apply:
        print("  （预演）")
        return 0

    p = REPO / "paper合" / "cover_letter.tex"
    assert p.exists(), "封面信不存在"
    t = io.open(p, encoding="utf-8").read()
    for k in ("Relation to prior work", "Related manuscripts by the same author",
              "Reproducibility and data", "Compliance", "AdaLoRA", "TARGET JOURNAL"):
        assert k in t, f"封面信缺 {k}"
    print("  ✅ 封面信结构完整（含三篇相关稿件披露）")

    hp = REPO / "HANDOFF.md"
    h = io.open(hp, encoding="utf-8").read()
    if "Paper A 封面信已起草" not in h:
        anchor = "> **✅ 2026-10-07 —— `site dominates allocation`"
        i = h.find(anchor)
        assert i > 0, "未找到 HANDOFF 锚点"
        io.open(hp, "w", encoding="utf-8", newline="").write(h[:i] + ENT + "\n" + h[i:])
        h2 = io.open(hp, encoding="utf-8").read()
        for k in ("cover_letter.tex", "披露三篇相关稿件", "TARGET JOURNAL", "238"):
            assert k in h2, f"HANDOFF 断言失败：缺 {k}"
        print(f"  ✅ HANDOFF 已追加（{len(h2.splitlines())} 行）")

    fp = REPO / "文件地图.md"
    fm = io.open(fp, encoding="utf-8").read()
    if "cover_letter.tex" not in fm:
        old = "   **⏭ 下一个待办 = 操作者确认选刊（ESWA 或 CVIU）**"
        if old in fm:
            fm = fm.replace(old, old + "\n   **✉️ 封面信已起草**：`paper合/cover_letter.tex`（2 页，含**三篇相关稿件披露**）；"
                                   "投稿前**替换 `[TARGET JOURNAL]` 占位符**并重编译。", 1)
            io.open(fp, "w", encoding="utf-8", newline="").write(fm)
            print("  ✅ 文件地图.md 已更新")
        else:
            print("  ⚠ 文件地图锚点未命中")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
