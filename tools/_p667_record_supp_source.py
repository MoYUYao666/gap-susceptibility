# -*- coding: utf-8 -*-
r"""Record the inclusion of the supplementary source in the archive.

    python tools/_p667_record_supp_source.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **📦 2026-10-14 16:00 —— 源包纳入补充材料的 LaTeX 源（操作者要求）**
>
> ### 一、操作者要求
>
> > **"Supplementary 的 LaTeX 源也要包含进去"**
>
> ### 二、✅ 新源包结构（17 成员 / **227,864 字节**，原 12 成员 / 128,804）
>
> ```
> main.tex                        main.bbl                    references.bib
> sections/{introduction,related_work,theory,experiments,discussion,conclusion}.tex
> figures/fig1_phase_transition.png      figures/fig2_counterfactual.png
> supplementary/supplementary.tex        supplementary/supplementary.bbl
> supplementary/references.bib
> supplementary/figures/fig3_ers.png     supplementary/figures/fig4_E_trajectory.png
> README_compile.txt
> ```
>
> **⇒ 两个文档各自独立编译**（正文在根目录、补充材料在 `supplementary/` 内），**各带 `.bbl` 故都不需要 bibtex**。
>
> ### 三、🔴 过程中查出的三个真问题
>
> | # | 问题 | 详述 |
> |---|---|---|
> | **1** | **补充材料缺 `.bbl`** | 它**有 6 个 `\cite`**（`adalora2023`、`halora2025`、`hu2025loralimits`、`igulora2025`、`sharegpt2023`、`wan2026gap`），但 `supplementary.bbl` **不存在** ⇒ 编辑部若不跑 bibtex，**参考文献会空或成 `[?]`** |
> | **2** | 我第一次修**修错了** | 在 `supplementary/` 里跑 bibtex ⇒ **它在那里找不到 `references.bib`（在上级）** ⇒ 产出**空 `.bbl`** ⇒ 随后 pdflatex **致命错误**（`Something's wrong--perhaps a missing \item`，空的 `thebibliography` 没有 `\\bibitem`）<br>**⇒ 正确修法：把 `references.bib` 复制到 `supplementary/` 旁边** ⇒ bibtex rc=0、`.bbl` 6 条、**0 未定义引用** |
> | **3** | **两个"残包生成器"互相覆盖** | `_p624`（只打 4 个文件、**不含 supplementary**）与新的完整构建器冲突；`_p651` 调的正是旧的 ⇒ **完整包被残包覆盖**（128,804 而非 227,864）<br>**⇒ 已把 `_p624` 改名为 `.SUPERSEDED_BY_p666`，`_p651` 改调 `_p666`** |
>
> ### 四、⚠️ 顺带纠正一处我先前的**误判**
>
> 我早先报告"正文引用了补充材料的 label ⇒ 可能有 `??`"。**实测是误报**：
> `tab:gamma_detail`、`tab:gamma_rank` **在 `appendix.tex` 里也有定义** ⇒
> **正文 `main.pdf` 未定义引用 0、`??` 0**。补充材料**完全不引用正文**（`\ref` 目标 0 个）⇒ **两个文档确实可以各自独立编译**。
>
> **另修正我自己的一个检查口径错误**：先前用 `'undefined'` 计数会把**字体警告**
> （`Font shape \`OT1/ptm/m/scit' undefined`，LaTeX 自动回退、无害）算成问题
> ⇒ 改为**只计真实的未定义引用/引用**（`undef-refs` / `undef-cites`）。
>
> ### 五、✅ 从干净解压的完整验证
>
> | 文档 | 页数 | 错误 | 未定义引用 | 未定义引用 | `??` |
> |---|---|---|---|---|---|
> | `main.pdf` | **10** | 0 | **0** | **0** | **0** |
> | `supplementary.pdf` | **5** | 0 | **0** | **0** | — |
>
> **四份交付 PDF 一同复核**（`tools/_p665`）：`main` / `supplementary` / `cover_letter` / `title_page`
> ⇒ **全部 0 错误、0 未定义引用、0 未定义引用、0 个 `??`** ✅
>
> ### 六、✅ 源码微调（已入 git，保持可见）
>
> `supplementary.tex` 的图引用由 `../figures/fig3_ers.png` 改为 **`figures/fig3_ers.png`**（本地），
> 并把 `fig3_ers.png`、`fig4_E_trajectory.png` 复制进 `supplementary/figures/`
> ⇒ **包内每个文档按自己的注释路径即可编译**，且不必嵌套重复目录。
>
> ### 七、上传区现状（源包已更新）
>
> | 字节 | 文件 |
> |---|---|
> | **227,864** | `P3_PRLETTERS-D-26-02378_LaTeX_Source.zip` ← **已换为完整包** |
> | 414,938 / 131,184 / 266,021 | Manuscript / Cover Letter / Supplementary |
> | 69,123 / 51,358 / 411 | Title Page / Highlights.pdf / Highlights.txt |
> | 8,781 / 8,563 / 26,831 | Response Reviewer1 / 2 / 3 |
>
> **暂存件与权威源 sha256 全部一致** ✅
>
> ### 八、剩余
>
> ① 上传 10 项 ② 粘三个回复框 ③ 表单：新标题 + DOI + 新 highlights ④ **Authorship Confirmation 是否重传（待操作者定）** ⑤ 提交
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not a.apply:
        print("  (dry run)")
        return 0
    hp = REPO / "HANDOFF.md"
    t = io.open(hp, encoding="utf-8").read()
    if "源包纳入补充材料的 LaTeX 源" in t:
        print("  already recorded")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("源包纳入补充材料的 LaTeX 源", "227,864", "空 `.bbl`", "残包生成器", "误判"):
        print(f"  {'OK ' if k in t2 else 'BAD'} {k}")
    print(f"  HANDOFF lines = {len(t2.splitlines())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
