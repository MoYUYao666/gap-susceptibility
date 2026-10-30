# -*- coding: utf-8 -*-
r"""Record the figure-size fix and the embedded graphical abstract.

    python tools/_p1287_record_figfix.py [--apply]
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

## 第 11 步（2026-10-18 20:10）：图放大 + graphical abstract 入正文，A1 **55 页**

**问题**：A1 五张图宽度为 0.55 / 0.62 / 0.55 / **0.45 / 0.48**，后两张（训练轨迹、任务敏感谱）明显偏小；
graphical abstract 此前只是包内独立 PDF，**正文里找不到**。

**处理**：

| 项 | 处理前 | 处理后 |
|---|---|---|
| Fig. 1 `fig1_lambda` | 0.55\\textwidth | **0.78**（`__crop` 版） |
| Fig. 2 `fig5_matched_gap` | 0.62 | **0.92** |
| Fig. 3 `fig2_tau_top1` | 0.55 | **0.78** |
| Fig. 4 `fig3_trajectory` | **0.45** | **0.74** |
| Fig. 5 `fig4_spectrum` | **0.48** | **0.78** |
| Graphical abstract | 仅包内独立文件 | **附录 Figure A.6（第 52 页）**，宽度 0.98\\textwidth |

- 新增 `paper_a1/figures/*_crop.pdf`（`pdfcrop` 裁掉图内白边），`main.tex` 改用裁剪版；
- graphical abstract 以独立小节 + `figure` 环境置于附录（`Figure A.6`），同时**仍保留**包内独立文件
  `Graphical Abstract.pdf`（门户可选上传项）；
- 编译：**55 页**、0 错误 / 0 未定义 / 0 Overfull；审计 `a1_paa` **READY/A pass=61 fail=0 warn=0**。
"""

ENT = """> **🖼️ 2026-10-18 20:10 —— A1 图放大（后两张 0.45/0.48 → 0.74/0.78）+ graphical abstract 进正文（附录 Figure A.6），**55 页**，审计 READY/A**
>
> - 五张图统一放大并改用 `pdfcrop` 裁边版：0.78 / 0.92 / 0.78 / **0.74** / **0.78**（原为 0.55 / 0.62 / 0.55 / **0.45** / **0.48**）；
> - **graphical abstract 之前只在包内**（所以正文找不到）→ 现作为**附录 Figure A.6（第 52 页）**入 PDF，0.98 宽；
>   包内独立 `Graphical Abstract.pdf` 仍保留作门户上传项；
> - A1 **55 页**、0/0/0；A1/Main/PaperA 三台账 **97/97、96/96、76/76** 全过；审计 **READY grade A：pass=61 fail=0 warn=0**。
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
    if "第 11 步" not in n:
        io.open(NOVDOC, "w", encoding="utf-8", newline="").write(n.rstrip("\n") + NOVSEC)
        print("  novelty doc appended")
    h = io.open(HANDOFF, encoding="utf-8").read()
    if "A1 图放大" not in h:
        i = h.find("# 项目交接文档")
        j = h.find("\n", i)
        io.open(HANDOFF, "w", encoding="utf-8", newline="").write(h[: j + 1] + "\n" + ENT.replace("\\n", "\n") + h[j + 1:])
        print("  handoff added")
    w = io.open(WHICH, encoding="utf-8").read()
    old = "5 基准复现 + 附录化 + Prop 5 + 五骨干匹配 gap** | 53 + 1 title page |"
    new = "5 基准复现 + 附录化（含 GA 图）+ Prop 5 + 五骨干匹配 gap** | 55 + 1 title page |"
    print(f"  which row: {w.count(old)}")
    if w.count(old) == 1:
        io.open(WHICH, "w", encoding="utf-8", newline="").write(w.replace(old, new, 1))
    m = io.open(MAP, encoding="utf-8").read()
    row = ("88. 🖼️ **A1 图放大 + GA 入正文（2026-10-18 20:10）** —— 五图宽度 0.78/0.92/0.78/**0.74**/**0.78**（原 0.55/0.62/0.55/**0.45**/**0.48**），"
           "改用 `pdfcrop` 裁边版；**graphical abstract 现为附录 Figure A.6（第 52 页）**，包内独立 PDF 仍保留。A1 **55 页**、"
           "审计 READY/A pass=61 fail=0 warn=0；三台账全过。\n")
    if "A1 图放大 + GA 入正文" not in m:
        anchor = "87. 🧾 **A1 合规收尾"
        idx = m.find(anchor)
        if idx >= 0:
            end = m.find("\n", idx)
            io.open(MAP, "w", encoding="utf-8", newline="").write(m[: end + 1] + row + m[end + 1:])
            print("  map row added")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
