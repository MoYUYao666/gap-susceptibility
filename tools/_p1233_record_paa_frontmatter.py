# -*- coding: utf-8 -*-
r"""Correct the keyword claim and record the PAA front-matter work.

My earlier record said A1 had no keywords. That was wrong: I searched for the `\keywords{}` macro, but A1 uses the
elsarticle `\begin{keyword} ... \end{keyword}` environment, and the PDF renders five keywords. The volume is therefore
already compliant with PAA's 4-6 requirement; the guard in the fix script skipped the insertion for the same reason.

    python tools/_p1233_record_paa_frontmatter.py [--apply]
"""
from __future__ import annotations

import argparse
import io
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
VENUE = REPO / "docs" / "A1_VENUE_DECISION.md"
HANDOFF = REPO / "HANDOFF.md"
MAP = REPO / "文件地图.md"

FIX = """

### 13.2 更正 + 已完成的 PAA 改造（2026-10-18 15:00）

**更正**：13.1 记"A1 关键词缺失"是**错的**。A1 用的是 elsarticle 的 `\\begin{keyword}...\\end{keyword}` 环境，
而不是 `\\keywords{}` 宏；PDF 实测渲染为 **5 个关键词**：
`modality gap, zero-shot classification, order preservation, cross-modal alignment, fine-tuning`
⇒ **已满足 PAA 的 4–6 要求**，无需新增。

**本轮实际改动**（`paper_a1/main.tex`）：

| 改动 | 内容 | 验证 |
|---|---|---|
| 声明规范化 | 原 4 个 Neural-Networks 风格 `\\section*{...}`（Competing interest / Funding / Data availability / GenAI）合并为单个 `\\section*{Declarations}`，内含 Funding、Competing interests、Ethics approval and consent、Consent for publication、Data and code availability、Authors' contributions、Use of artificial-intelligence tools | PDF 中 `Declarations`、`Use of artificial-intelligence tools`、`Data and code availability` 均命中；旧节已不存在 |
| 单独 title page | 新建 `paper_a1/title_page.tex` → `title_page.pdf`（**1 页**）：标题、作者、单位、通讯邮箱 + 完整 Declarations | 编译 0/0/0；PDF 含 `Declarations` |
| AI 使用写入 Methods | 在 Setup 节末补一句：AI 辅助工具用于稿件准备与部分代码，作者负全责（PAA 要求写在 Methods 或替代位置）| PDF 命中 `AI-assisted tools` |
| 编译 | `main.pdf` **45 页** | 0 错误 / 0 未定义 / 0 Overfull |

**PAA 合规清单（当前状态）**：摘要 239 词（150–250 ✅）｜关键词 5 个（4–6 ✅）｜正文无长度上限 ✅｜LaTeX ✅｜
Declarations 单节 + 单独 title page ✅｜AI 使用已入 Methods ✅。
"""

ENT = """> **✅ 2026-10-18 15:00 —— A1 按 PAA 规范补齐：Declarations 合并 + 单独 title page + AI 使用入 Methods（并更正关键词误记）**
>
> **更正**：之前记"A1 缺关键词"是我查错了宏——A1 用 `\\begin{keyword}` 环境，PDF 实测**已有 5 个关键词**
> （modality gap, zero-shot classification, order preservation, cross-modal alignment, fine-tuning）⇒ PAA 的 4–6 已满足。
>
> 本轮实际改动：
> 1. 4 个 NN 风格的声明节合并为单个 **`\\section*{Declarations}`**（Funding / Competing interests / Ethics approval /
>    Consent / Data & code availability / Authors' contributions / Use of AI）；
> 2. 新建 **`paper_a1/title_page.tex` → `title_page.pdf`**（1 页，含完整 Declarations），满足 PAA"单独 title page"要求；
> 3. PAA 要求 AI 使用写在 Methods（或替代位置）⇒ 在 **Setup 节末**补一句并指向 Declarations；
> 4. `main.pdf` 重建 **45 页**、**0 错误 / 0 未定义 / 0 Overfull**。
>
> PAA 合规现状：摘要 239 词（150–250 ✅）、关键词 5（4–6 ✅）、无正文长度上限 ✅、LaTeX ✅、Declarations+title page ✅、AI 入 Methods ✅。
> 详见 `docs/A1_VENUE_DECISION.md` §13.2。
>

"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not a.apply:
        print("  (dry run)")
        return 0
    v = io.open(VENUE, encoding="utf-8").read()
    if "13.2 更正" not in v:
        io.open(VENUE, "w", encoding="utf-8", newline="").write(v.rstrip("\n") + FIX)
        print("  venue doc updated")
    h = io.open(HANDOFF, encoding="utf-8").read()
    if "A1 按 PAA 规范补齐" not in h:
        i = h.find("# 项目交接文档")
        j = h.find("\n", i)
        io.open(HANDOFF, "w", encoding="utf-8", newline="").write(h[: j + 1] + "\n" + ENT + h[j + 1:])
        print("  handoff added")
    m = io.open(MAP, encoding="utf-8").read()
    row = ("75. ✅ **A1 按 PAA 规范补齐（2026-10-18 15:00）** —— 声明合并为单 `Declarations` 节（Springer 子项齐全）；"
           "新建 **title_page.tex/pdf（1 页）**；AI 使用写入 Setup（PAA 要求）；main **45 页 0/0/0**。"
           "**更正**：A1 早有 5 个关键词（`\\begin{keyword}`），PAA 4–6 已满足。"
           "PAA 合规：摘要 239/150–250、无正文长度上限、LaTeX 可投。\n")
    if "A1 按 PAA 规范补齐" not in m:
        anchor = "74. 👁️ **EDGE 读取 PAA 政策"
        idx = m.find(anchor)
        if idx >= 0:
            end = m.find("\n", idx)
            io.open(MAP, "w", encoding="utf-8", newline="").write(m[: end + 1] + row + m[end + 1:])
            print("  map row added")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
