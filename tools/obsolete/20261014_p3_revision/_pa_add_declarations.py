# -*- coding: utf-8 -*-
r"""给 Paper A 的 elsarticle 版补齐 Neurocomputing 要求的声明块（放在参考文献之前）。

## 依据

`_guide_neurocomputing.txt`：
- **声明须在参考文献之前**（"before the references list" / "before the reference list"）；
- CRediT 角色表（14 项官方角色）；
- 生成式 AI 声明的**固定标题与句式**：
  「Declaration of generative AI and AI-assisted technologies in the manuscript preparation process.」
  —「During the preparation of this work the author(s) used [TOOL] in order to [REASON]. After using
  this tool/service, the author(s) reviewed and edited the content as needed and take(s) full
  responsibility for the content of the published article.」

## 措辞来源（已由操作者确认，2026-10-02）

照抄本项目既有且经确认的口径（`备选/06_归档稿件/paper_ap3/main.tex:77–81`、`paper3/paper_ieee/main.tex`）：
使用 **Claude (Anthropic) 与 DeepSeek V4**，用途为**起草与修订正文、准备实验代码与图**。

## 补入的四节

1. Data availability（改为与 ap3 同口径的完整表述，替代原先一句）
2. Funding（无资助）
3. Declaration of competing interests
4. Declaration of generative AI and AI-assisted technologies in the manuscript preparation process

    python tools\_pa_add_declarations.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "paper合" / "main_nc.tex"

OLD = r"""\section*{Data availability}
Data will be made available on request.

\section*{Declaration of competing interest}
The author declares no competing financial interests or personal relationships that could have appeared
to influence the work reported in this paper.

\bibliographystyle{elsarticle-harv}"""

NEW = r"""\section*{Data availability}
All datasets and model releases used in this study are public. Every result JSON cited in this
manuscript --- including the per-epoch monitoring trajectories, the strict-freezing controls and the
cross-architecture sweeps --- together with the analysis scripts that compute the reported statistics and
the training configurations, is archived in the project repository, which is currently private and will
be made public upon publication (available to the reviewers on request). No new data were generated that
requires deposit in an external repository, and no datum used here is restricted.

\section*{Funding}
This research did not receive any specific grant from funding agencies in the public, commercial, or
not-for-profit sectors.

\section*{Declaration of competing interests}
The author declares that he has no known competing financial interests or personal relationships that
could have appeared to influence the work reported in this paper.

\section*{CRediT authorship contribution statement}
\textbf{Hongrui Wan:} Conceptualization, Methodology, Formal analysis, Investigation, Software,
Validation, Visualization, Writing -- original draft, Writing -- review and editing.

\section*{Declaration of generative AI and AI-assisted technologies in the manuscript preparation process}
During the preparation of this work the author used Claude (Anthropic) and DeepSeek V4 in order to draft
and revise the manuscript text and to prepare experimental code and figures. After using these tools, the
author reviewed and edited the content as needed and takes full responsibility for the content of the
published article.

\bibliographystyle{elsarticle-harv}"""


def main() -> int:
    apply = "--apply" in sys.argv
    t = io.open(F, encoding="utf-8").read()
    c = t.count(OLD)
    if c != 1:
        print(f"  ⚠ 未命中（出现 {c} 次）")
        return 1
    print("  ✅ 命中待替换的声明块")
    if apply:
        io.open(F, "w", encoding="utf-8", newline="").write(t.replace(OLD, NEW, 1))
        t2 = io.open(F, encoding="utf-8").read()
        for need in ("CRediT authorship contribution statement",
                     "Declaration of generative AI and AI-assisted technologies",
                     "Declaration of competing interests", "\\section*{Funding}"):
            assert need in t2, f"断言失败：缺 {need}"
        # 声明必须在参考文献之前
        i_decl = t2.find("Declaration of generative AI")
        i_bib = t2.find("\\bibliographystyle")
        assert 0 < i_decl < i_bib, "断言失败：声明不在参考文献之前"
        print("  ✅ 已补入 5 节声明并断言通过（含位置检查）")
    else:
        print("  （预演，加 --apply 生效）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
