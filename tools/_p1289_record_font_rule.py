# -*- coding: utf-8 -*-
r"""Write the standing figure-font rule into the project instruction files and record today's fix.

Operator instruction (2026-10-18): every text item inside generated figures must be Times New Roman, and this applies to
all future figures. The rule is appended to AGENTS.md and CLAUDE.md so a fresh session reads it before plotting, and the
fix (fig5 + graphical abstract were DejaVu Sans) is recorded in HANDOFF, the map and the novelty log.

    python tools/_p1289_record_font_rule.py [--apply]
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

RULE = """
## 🔴 生图字体规则（用户明确要求，2026-10-18 立，长期有效）

> **"图片的字体也得是 times new roman，以后生图里面的文字都得是这个字体"** —— 操作者原话

**所有生成图（论文插图、graphical abstract、示意图、补充材料图）里的文字一律 Times New Roman**，数学符号用 STIX
（Times 兼容字形）。这条规则对**今后所有新图**生效，不只是当前稿件的图。

**matplotlib 统一设置（每个生图脚本开头必须加）：**

```python
import matplotlib as mpl
mpl.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "Times", "STIXGeneral", "DejaVu Serif"],
    "mathtext.fontset": "stix",
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
    "axes.unicode_minus": False,
})
```

**交付前检查（硬判据）**：`pdffonts figure.pdf` 只应出现 `TimesNewRoman*`（数学允许 `STIXGeneral*`）。
出现 `DejaVu*`、`Arial*`、`Helvetica*` 即未达标，必须重生成。

**已按此修复（2026-10-18）**：`tools/_p1210_figure_matched_gap.py`（fig5）与 `tools/_p1276_graphical_abstract.py`
（graphical abstract）原本用 DejaVu Sans，已由 `tools/_p1288_fix_figure_fonts.py` 插入样式块并重生成；
fig1–fig4 本来就是 Times New Roman，未改。核验结果：六张图（含裁边版）只含 TimesNewRoman 与 STIXGeneral。
"""

NOVSEC = """

---

## 第 12 步（2026-10-18 20:35）：图内字体统一 Times New Roman（长期规则）

**操作者要求**：图里的字必须 Times New Roman，**以后所有生图都照此**。

- **核查**：`pdffonts` 显示 fig1–fig4 本已是 TimesNewRomanPSMT（数学 STIX），但 **fig5_matched_gap 与 graphical_abstract
  用的是 DejaVu Sans**。
- **修复**：`tools/_p1288_fix_figure_fonts.py` 给 `_p1210_figure_matched_gap.py` 与 `_p1276_graphical_abstract.py`
  插入统一样式块（serif + Times New Roman + `mathtext.fontset=stix` + `pdf.fonttype=42`），重生成并重裁边
  （`*_crop.pdf`）。
- **复验**：六张图（含裁边版）`pdffonts` 仅含 **TimesNewRomanPSMT / TimesNewRomanPS-BoldMT / STIXGeneral**，无 DejaVu。
- **规则落盘**：已写入 `AGENTS.md` 与 `CLAUDE.md`（新会话生图前必读）。

A1 编译 **55 页**、0/0/0；三台账 97/97、96/96、76/76 全过；审计 `a1_paa` READY/A。
"""

ENT = """> **🔤 2026-10-18 20:35 —— 图内字体统一 Times New Roman（长期规则已落盘）**
>
> 操作者要求图内文字一律 Times New Roman，且**今后所有生图**都照此。核查发现：fig1–fig4 本已达标（TimesNewRoman + STIX），
> 但 **fig5_matched_gap 与 graphical_abstract 是 DejaVu Sans**。已由 `_p1288` 给两个生图脚本插入统一样式块
> （`font.family=serif` + Times New Roman + `mathtext.fontset=stix` + `pdf.fonttype=42`），重生成并重裁边；
> `pdffonts` 复验六图仅含 TimesNewRoman 与 STIXGeneral。
>
> **规则已写入 `AGENTS.md` 与 `CLAUDE.md`**：交付前用 `pdffonts` 检查，出现 DejaVu/Arial/Helvetica 即未达标。
> A1 **55 页**、0/0/0；审计 READY/A；三台账全过。
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
        if "生图字体规则" in t:
            print(f"  {f.name}: rule already present")
            continue
        io.open(f, "w", encoding="utf-8", newline="").write(t.rstrip("\n") + "\n" + RULE)
        print(f"  {f.name}: rule appended")

    n = io.open(NOVDOC, encoding="utf-8").read()
    if "第 12 步" not in n:
        io.open(NOVDOC, "w", encoding="utf-8", newline="").write(n.rstrip("\n") + NOVSEC)
        print("  novelty doc appended")

    h = io.open(HANDOFF, encoding="utf-8").read()
    if "图内字体统一 Times New Roman" not in h:
        i = h.find("# 项目交接文档")
        j = h.find("\n", i)
        io.open(HANDOFF, "w", encoding="utf-8", newline="").write(h[: j + 1] + "\n" + ENT.replace("\\n", "\n") + h[j + 1:])
        print("  handoff added")

    m = io.open(MAP, encoding="utf-8").read()
    row = ("89. 🔤 **图内字体统一 Times New Roman（2026-10-18 20:35）** —— fig1–fig4 本已达标；"
           "**fig5 与 graphical abstract 原用 DejaVu Sans**，已由 `_p1288` 给生图脚本插入统一样式块并重生成+重裁边；"
           "`pdffonts` 复验六图仅含 TimesNewRoman/STIXGeneral；**规则已写入 `AGENTS.md` 与 `CLAUDE.md`（今后所有图适用）**。\n")
    if "图内字体统一 Times New Roman" not in m:
        anchor = "88. 🖼️ **A1 图放大"
        idx = m.find(anchor)
        if idx >= 0:
            end = m.find("\n", idx)
            io.open(MAP, "w", encoding="utf-8", newline="").write(m[: end + 1] + row + m[end + 1:])
            print("  map row added")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
