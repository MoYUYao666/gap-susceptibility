# -*- coding: utf-8 -*-
r"""Record the Pattern Analysis and Applications submission policy as read from the operator's open Edge tab.

Source: https://link.springer.com/journal/10044/submission-guidelines (read 2026-10-18 via CDP from the Edge session the
operator already had open). Facts below are quoted from that page, not inferred.

    python tools/_p1231_record_paa_guide.py [--apply]
"""
from __future__ import annotations

import argparse
import io
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
VENUE = REPO / "docs" / "A1_VENUE_DECISION.md"
HANDOFF = REPO / "HANDOFF.md"
MAP = REPO / "文件地图.md"

SEC = """

### 13.1 PAA 投稿政策已核（2026-10-18，读自操作者 Edge 中已打开的官网页面）

来源：`https://link.springer.com/journal/10044/submission-guidelines`（Springer, journal 10044），经 CDP 读取页面正文 52,388 字符。

| 条款 | 官方原文/事实 | A1 现状 | 判定 |
|---|---|---|---|
| 摘要 | "Please provide an abstract of **150 to 250 words**" | **239 词**（审计工具计数器）| ✅ 合规 |
| 关键词 | "Please provide **4 to 6 keywords**" | **缺失**（`main.tex` 无 `关键词` 字段）| ❌ **必须补** |
| 正文长度 | 全文检索不到任何正文页数/字数上限（`page limit`/`should not exceed`/`no more than N` 均 0 命中）| 45 页 / 约 14k 词 | ✅ 无硬限 |
| 稿件格式 | "submit in common word processing formats such as **.docx or LaTeX**"；另有面向 Word 的排版建议 | elsarticle + LaTeX | ✅ 可投（若被要求可用 Springer 模板重排）|
| 声明 | 要求**单独 title page** 上的 "Declarations" 节，含 Funding / Competing interests / Ethics / Consent / Data, Materials and/or Code availability / Authors' contribution | Funding、Competing interests、Data availability 已有，但**未合并为 Declarations 节**，也未单独成 title page | ⚠️ 需整理 |
| LLM 使用 | 须在 Methods（或替代位置）说明；"AI assisted copy editing" 可免声明 | 已有生成式 AI 声明 | ⚠️ 需按 PAA 措辞核对位置 |
| 图件 | 字体 Helvetica/Arial、终尺寸 8–12 pt；文件上限 2 GB | 未核 | 待核 |

**结论**：PAA 与 A1 **结构兼容**（无正文长度上限、摘要已合规、LaTeX 可投）。
**投稿前必做三件**：① 补 **4–6 个关键词**；② 把声明合并为 `Declarations` 节并放到**单独的 title page**；
③ 按 PAA 措辞核对 AI 使用声明的位置。
"""

ENT = """> **👁️ 2026-10-18 14:45 —— 从操作者 Edge 读到 PAA 投稿政策：结构兼容，缺关键词**
>
> 经 CDP 读取操作者已打开的 `link.springer.com/journal/10044/submission-guidelines`（52,388 字符），核实：
> - 摘要 **150–250 词**：A1 现 **239 词** ✅；
> - 关键词 **4–6 个**：A1 **缺失** ❌（`main.tex` 无 keywords 字段）；
> - **正文无页数/字数上限**（全文无 `page limit`/`should not exceed`/`no more than N` 命中）⇒ 45 页/14k 词可投；
> - 稿件格式接受 **LaTeX 或 .docx**；
> - 需**单独 title page** 上的 `Declarations` 节（Funding / Competing interests / Ethics / Consent / Data & Code /
>   Authors' contribution）；A1 的声明目前分散、未合并；
> - LLM 使用须在 Methods 或替代位置说明（纯语言润色可免）。
>
> **投稿前必做**：① 补 4–6 关键词；② 声明合并成 `Declarations` 并置于单独 title page；③ 核对 AI 声明措辞。
> 详见 `docs/A1_VENUE_DECISION.md` §13.1。
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
    if "13.1 PAA 投稿政策已核" not in v:
        io.open(VENUE, "w", encoding="utf-8", newline="").write(v.rstrip("\n") + SEC)
        print("  venue doc updated")
    h = io.open(HANDOFF, encoding="utf-8").read()
    if "从操作者 Edge 读到 PAA 投稿政策" not in h:
        i = h.find("# 项目交接文档")
        j = h.find("\n", i)
        io.open(HANDOFF, "w", encoding="utf-8", newline="").write(h[: j + 1] + "\n" + ENT + h[j + 1:])
        print("  handoff added")
    m = io.open(MAP, encoding="utf-8").read()
    row = ("74. 👁️ **EDGE 读取 PAA 政策（2026-10-18 14:45）** —— CDP 读取操作者已开页面：摘要 **150–250 词**（A1 239 ✅）、"
           "关键词 **4–6**（A1 **缺失，必须补**）、**正文无页数/字数上限**、接受 LaTeX、需单独 title page 的 `Declarations`、"
           "LLM 使用须在 Methods 说明。A1 结构兼容，投稿前须补关键词并整理声明。详见 `docs/A1_VENUE_DECISION.md` §13.1。\n")
    if "EDGE 读取 PAA 政策" not in m:
        anchor = "73. 📮 **A1 选刊修正"
        idx = m.find(anchor)
        if idx >= 0:
            end = m.find("\n", idx)
            io.open(MAP, "w", encoding="utf-8", newline="").write(m[: end + 1] + row + m[end + 1:])
            print("  map row added")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
