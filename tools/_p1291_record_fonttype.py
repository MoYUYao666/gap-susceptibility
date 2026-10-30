# -*- coding: utf-8 -*-
r"""Extend the figure-font rule with the embedding-type requirement and record the legacy fix.

fig1-fig4 were embedded as Type 3 fonts (the two legacy generators set the family but not the PDF font type). They were
regenerated with pdf.fonttype=42 and re-cropped; every figure now embeds CID TrueType. The rule in AGENTS.md and
CLAUDE.md gains the explicit Type 3 prohibition.

    python tools/_p1291_record_fonttype.py [--apply]
"""
from __future__ import annotations

import argparse
import io
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
AGENTS = REPO / "AGENTS.md"
CLAUDE = REPO / "CLAUDE.md"
HANDOFF = REPO / "HANDOFF.md"
MAP = REPO / "文件地图.md"
NOVDOC = REPO / "docs" / "A1_NOVELTY_STEP1_2026-10-18.md"

RULE_ADD = """
**嵌入类型要求（同日追加）**：字体必须嵌为 **CID TrueType**（`pdf.fonttype=42`）；**Type 3 不被接受**——
出版社排版会拒收 Type 3。`pdffonts` 检查时同时看 `type` 列，出现 `Type 3` 即需重生成。

**已按此修复的第二批（2026-10-18 晚间）**：fig1–fig4 原为 **Type 3**（`clip_a1_figures.py` / `clip_a1_fig4.py`
只设了字体族、未设 `pdf.fonttype`），已由 `tools/_p1290_regen_legacy_figures.py` 插入样式块并重生成；
六张图（含裁边版）现均为 **CID TrueType**：TimesNewRomanPSMT / TimesNewRomanPS-BoldMT / STIXGeneral。
"""

NOVSEC = """

---

## 第 13 步（2026-10-18 21:00）：字体嵌入类型统一 CID TrueType

字体族已统一 Times New Roman 后，`pdffonts` 进一步暴露：**fig1–fig4 是 Type 3 嵌入**（旧生成脚本只设字体族、
未设 `pdf.fonttype`），出版社排版会拒收。

- 给 `tools/clip_a1_figures.py`（fig1/2/4）与 `tools/clip_a1_fig4.py`（fig3）插入同款样式块
  （`pdf.fonttype=42`），重生成并重裁边（脚本 `_p1290`）。
- 复验六图（`*_crop.pdf`）：**TimesNewRomanPSMT / TimesNewRomanPS-BoldMT / STIXGeneral 全部 CID TrueType**。
- 规则文档（`AGENTS.md`、`CLAUDE.md`）追加"Type 3 不接受"的硬判据。
- A1 重编译 **55 页**、0/0/0；A1/Main/PaperA 三台账 97/97、96/96、76/76 全过；审计 `a1_paa` **READY/A**。
"""

ENT = """> **🔤 2026-10-18 21:00 —— 图的字体嵌入类型统一为 CID TrueType（fig1–fig4 原是 Type 3）**
>
> 字体族统一 Times New Roman 之后，`pdffonts` 进一步发现 **fig1–fig4 是 Type 3 嵌入**（旧脚本只设字体族、未设
> `pdf.fonttype`）。已由 `_p1290` 给 `clip_a1_figures.py` / `clip_a1_fig4.py` 插入样式块并重生成 + 重裁边。
> 现六张图全部 **CID TrueType**：TimesNewRomanPSMT / TimesNewRomanPS-BoldMT / STIXGeneral。
>
> 规则（`AGENTS.md`、`CLAUDE.md`）已补："字体须 CID TrueType，**Type 3 不接受**"。
> A1 **55 页**、0/0/0；三台账全过；审计 **READY grade A：pass=61 fail=0 warn=0**。
>

"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not a.apply:
        print("  (dry run)")
        return 0

    for f in (AGENTS, CLAUDE):
        t = io.open(f, encoding="utf-8").read()
        if "Type 3 不被接受" in t or "Type 3 不接受" in t:
            print(f"  {f.name}: type requirement already present")
            continue
        io.open(f, "w", encoding="utf-8", newline="").write(t.rstrip("\n") + "\n" + RULE_ADD)
        print(f"  {f.name}: type requirement appended")

    n = io.open(NOVDOC, encoding="utf-8").read()
    if "第 13 步" not in n:
        io.open(NOVDOC, "w", encoding="utf-8", newline="").write(n.rstrip("\n") + NOVSEC)
        print("  novelty doc appended")

    h = io.open(HANDOFF, encoding="utf-8").read()
    if "图的字体嵌入类型统一为 CID TrueType" not in h:
        i = h.find("# 项目交接文档")
        j = h.find("\n", i)
        io.open(HANDOFF, "w", encoding="utf-8", newline="").write(h[: j + 1] + "\n" + ENT.replace("\\n", "\n") + h[j + 1:])
        print("  handoff added")

    m = io.open(MAP, encoding="utf-8").read()
    row = ("90. 🔤 **字体嵌入类型统一 CID TrueType（2026-10-18 21:00）** —— fig1–fig4 原为 **Type 3**（出版社拒收），"
           "由 `_p1290` 给旧生图脚本插样式块并重生成+重裁边；六图现全部 **CID TrueType**（TimesNewRoman/STIX）。"
           "规则文档补「Type 3 不接受」硬判据；A1 **55 页**、审计 READY/A。\n")
    if "字体嵌入类型统一 CID TrueType" not in m:
        anchor = "89. 🔤 **图内字体统一 Times New Roman"
        idx = m.find(anchor)
        if idx >= 0:
            end = m.find("\n", idx)
            io.open(MAP, "w", encoding="utf-8", newline="").write(m[: end + 1] + row + m[end + 1:])
            print("  map row added")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
