# -*- coding: utf-8 -*-
r"""Record the visual rendering check and the float-placement fix.

The check rendered all pages at 72 dpi and flagged blank pages, ink outside the margins and internal white gaps; it found no
blank pages and no overflow, but two layout defects: the graphical abstract was pushed to its own page (leaving ~330 pt of
whitespace on the preceding page) and several [H] floats forced page breaks. Switching figures and tables to [t] and
shrinking the graphical abstract to 0.84 textwidth reduced the manuscript from 55 to 53 pages with no trailing gap above
250 pt except the reference list's last page.

    python tools/_p1296_record_visual_check.py [--apply]
"""
from __future__ import annotations

import argparse
import io
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HANDOFF = REPO / "HANDOFF.md"
MAP = REPO / "文件地图.md"
WHICH = REPO / "哪篇是哪篇.md"
NOVDOC = REPO / "docs" / "A1_NOVELTY_STEP1_2026-10-18.md"

NOVSEC = """

---

## 第 14 步（2026-10-18 21:30）：全页目视渲染检查 + 浮动排版修正，A1 **53 页**

**方法**：把 55 页全部渲染成 72 dpi 图，逐页统计墨迹覆盖率、左右/上下越界、页内最大空白与页尾空白；
再对关键页（标题页、图 2、图 5、附录表页、GA 页、参考文献末页）做 100 dpi 目视抽查。

**发现**：

| 项 | 结果 |
|---|---|
| 空白页 | **0** |
| 内容越界（左右/上边距） | **0** |
| 字体 | 六图均 CID TrueType（TimesNewRoman/STIX），正文 Times |
| **graphical abstract 被挤到独立页** | p51 留白 **331 pt**，图被推到 p52 |
| **`[H]` 强制定位造成页尾空白** | p32 300 pt、p16 261 pt、p29 243 pt、p50 224 pt |

**修正**：
1. 所有 figure/table 的 `[H]` 改为 `[t]`（顶部浮动，让正文回填）；
2. graphical abstract 宽度 0.98 → **0.84**\\textwidth，使其与说明段同页；
3. 重扫：**页数 55 → 53**；页尾留白 >250 pt 的仅剩最后一页（参考文献结束，正常）；
4. 目检：图 2（p17）、图 5（p32）、GA（p51）、附录表 A.18/A.19（p49）排版正常，表列不越界、图例可读。

A1 **53 页**、0 错误 / 0 未定义 / 0 Overfull；三台账 97/97、96/96、76/76 全过；审计 `a1_paa` **READY/A**。
"""

ENT = """> **👁️ 2026-10-18 21:30 —— A1 全页目视检查：无空白页/无越界/字体合格；修掉 GA 挤页与 [H] 页尾空白，**55 → 53 页**，审计 READY/A**
>
> 全 55 页渲染后逐页统计：**空白页 0、内容越界 0、字体全 CID TrueType**；发现两类排版问题并修正：
> ① **graphical abstract 被推到独立页**（前一页留白 331pt）→ GA 宽度 0.98→**0.84**，与说明段同页；
> ② **`[H]` 强制定位**造成 p32/p16/p29 页尾留白 300/261/243pt → 全部改 `[t]` 浮动，正文回填。
> 重扫结果：**53 页**，页尾留白 >250pt 仅剩参考文献末页（正常）。目检图 2/图 5/GA/附录表均正常。
> 三台账 97/97、96/96、76/76 全过；审计 **READY grade A：pass=61 fail=0 warn=0**。
>

"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not a.apply:
        print("  (dry run)")
        return 0
    n = io.open(NOVDOC, encoding="utf-8").read()
    if "第 14 步" not in n:
        io.open(NOVDOC, "w", encoding="utf-8", newline="").write(n.rstrip("\n") + NOVSEC)
        print("  novelty doc appended")
    h = io.open(HANDOFF, encoding="utf-8").read()
    if "A1 全页目视检查" not in h:
        i = h.find("# 项目交接文档")
        j = h.find("\n", i)
        io.open(HANDOFF, "w", encoding="utf-8", newline="").write(h[: j + 1] + "\n" + ENT.replace("\\n", "\n") + h[j + 1:])
        print("  handoff added")
    w = io.open(WHICH, encoding="utf-8").read()
    old = "附录化（含 GA 图）+ Prop 5 + 五骨干匹配 gap** | 55 + 1 title page |"
    new = "附录化（含 GA 图）+ Prop 5 + 五骨干匹配 gap + 排版修正** | 53 + 1 title page |"
    print(f"  which row: {w.count(old)}")
    if w.count(old) == 1:
        io.open(WHICH, "w", encoding="utf-8", newline="").write(w.replace(old, new, 1))
    m = io.open(MAP, encoding="utf-8").read()
    row = ("91. 👁️ **A1 全页目视检查 + 浮动修正（2026-10-18 21:30）** —— 55 页逐页渲染：**空白页 0、越界 0、字体全 CID TrueType**；"
           "修正 GA 被挤页（宽度 0.98→0.84）与 `[H]` 造成的页尾留白（全改 `[t]`）；**55 → 53 页**，页尾留白 >250pt 仅末页。"
           "审计 **READY/A pass=61 fail=0 warn=0**；三台账全过。\n")
    if "A1 全页目视检查" not in m:
        anchor = "90. 🔤 **字体嵌入类型统一 CID TrueType"
        idx = m.find(anchor)
        if idx >= 0:
            end = m.find("\n", idx)
            io.open(MAP, "w", encoding="utf-8", newline="").write(m[: end + 1] + row + m[end + 1:])
            print("  map row added")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
