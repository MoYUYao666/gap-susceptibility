# -*- coding: utf-8 -*-
r"""Verify the abstract text sync, register Abstract.txt in the package README, and record the step.

    python tools/_p1252_verify_abstract_txt.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import os
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PKG = REPO / "SUBMISSION" / "PaperA_Neurocomputing"
HANDOFF = REPO / "HANDOFF.md"
MAP = REPO / "文件地图.md"

ENT = """> **📋 2026-10-18 17:20 —— Paper A 提供"可直接复制"的摘要（`Abstract.txt`，245 词）**
>
> 操作者要求可直接复制的摘要版本。原 `PORTAL_TEXT.md` 的摘要带有 LaTeX 转换残留（`(r=-0.71 )` 之类的空格、
> 标题行混入 `(239 words)`）。新脚本 `tools/_p1251_copyable_abstract.py`：
>
> - 以 `paper合/abstract_nc.tex`（正文摘要的逐字副本）为唯一来源；
> - 显式宏映射：`--`→en dash、`$...$` 内数学做 **= < > ± × 间距、Unicode 减号、`R^2`→`R²`**；
> - 断言：无 LaTeX 残留、无双空格、标点前无空格、≤250 词、符号 β/±/R²/– 齐全 —— 全部通过；
> - 输出 `SUBMISSION/PaperA_Neurocomputing/Abstract.txt`（1 段、1,619 B、**245 词**），并同步刷新 `PORTAL_TEXT.md`。
>
> **词数口径**：空白切分 **245**（≤250 ✅）；审计工具"公式按一词计"口径 **231**（两份口径都合规）。
> 已改：包 README 的 Abstract 行同时列出 `.pdf` 与 `.txt`。
>

"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    txt = io.open(PKG / "Abstract.txt", encoding="utf-8").read().strip()
    portal = io.open(PKG / "PORTAL_TEXT.md", encoding="utf-8").read()
    m = re.search(r"## Abstract \(\d+ words\)\n\n(.*?)\n\n## Keywords", portal, re.S)
    assert m, "portal abstract section not found"
    same = m.group(1).strip() == txt
    print(f"  Abstract.txt words: {len(txt.split())} | portal in sync: {same}")

    readme = PKG / "README.md"
    r = io.open(readme, encoding="utf-8").read()
    old = "| Abstract | `Abstract.pdf` | 1 page; standalone abstract + keywords (Editorial Manager item) |"
    new = ("| Abstract | `Abstract.pdf`（+ `Abstract.txt`）| PDF 1 页；`.txt` 为纯文本可直接粘贴（**%d 词**）|"
           % len(txt.split()))
    if old in r:
        r = r.replace(old, new, 1)
        print("  README abstract row updated")
    else:
        print("  README abstract row already updated or layout changed")

    if not a.apply:
        print("  (dry run)")
        return 0
    io.open(readme, "w", encoding="utf-8", newline="").write(r)
    h = io.open(HANDOFF, encoding="utf-8").read()
    if "可直接复制" not in h:
        i = h.find("# 项目交接文档")
        j = h.find("\n", i)
        io.open(HANDOFF, "w", encoding="utf-8", newline="").write(h[: j + 1] + "\n" + ENT + h[j + 1:])
        print("  handoff added")
    mp = io.open(MAP, encoding="utf-8").read()
    row = ("81. 📋 **Paper A 可复制摘要 `Abstract.txt`（2026-10-18 17:20）** —— 由 `_p1251` 从 `abstract_nc.tex` 生成，"
           "显式宏映射 + 断言（无残留/无双空格/≤250 词/符号齐全）；**245 词**（审计口径 231）；同步刷新 `PORTAL_TEXT.md`；"
           "包 README 的 Abstract 行列出 `.pdf`+`.txt`。\n")
    if "可复制摘要" not in mp:
        anchor = "80. 📄 **Paper A 单独 Abstract 文件"
        idx = mp.find(anchor)
        if idx >= 0:
            end = mp.find("\n", idx)
            io.open(MAP, "w", encoding="utf-8", newline="").write(mp[: end + 1] + row + mp[end + 1:])
            print("  map row added")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
