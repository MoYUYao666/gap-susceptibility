# -*- coding: utf-8 -*-
r"""测量 PDF 的**真实版心宽度**，并找出**真正越界**的元素（2026-10-06）。

## 为什么不用 LaTeX 日志

日志的 `Overfull \hbox` 会误报（本项目已确认两次）：它报的是浮动体盒子的度量，
而目视 PDF 时内容**并未越界**。故改用**像素法**：
把页面渲染成位图，量非白像素的最小/最大 x，得到**真实的内容范围**。

## 判据

- 正文页：内容应落在 `[left, right]` 内，`right` 即版心右边界。
- 若无页面越界，则那些 `Overfull` 全是度量噪声 → **表格本身没溢出**。

    python tools\_measure_textblock.py
"""
from __future__ import annotations

import re
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PDF = REPO / "paper合" / "main_nc.pdf"
DPI = 100          # 100 dpi → 1 pt = 100/72 px


def page_ink_bounds(png: Path) -> tuple[int, int, int, int] | None:
    from PIL import Image
    import numpy as np
    with Image.open(png) as im:
        a = np.asarray(im.convert("L"))
    ink = a < 240
    if not ink.any():
        return None
    cols = np.where(ink.any(axis=0))[0]
    rows = np.where(ink.any(axis=1))[0]
    return int(cols[0]), int(cols[-1]), int(rows[0]), int(rows[-1])


def main() -> int:
    n_pages = int(re.search(rb"Pages:\s+(\d+)",
                            subprocess.run(["pdfinfo", str(PDF)], capture_output=True).stdout).group(1))
    print(f"=== {PDF.name}：{n_pages} 页 ｜ 渲染 {DPI} dpi（1 pt = {DPI/72:.4f} px）===")
    px_per_pt = DPI / 72.0

    body = []
    over = []
    with tempfile.TemporaryDirectory() as td:
        for pg in range(1, n_pages + 1):
            subprocess.run(["pdftoppm", "-f", str(pg), "-l", str(pg), "-r", str(DPI),
                            "-png", str(PDF), str(Path(td) / f"p{pg:03d}")],
                           capture_output=True)
            cands = sorted(Path(td).glob(f"p{pg:03d}*.png"))
            if not cands:
                continue
            b = page_ink_bounds(cands[0])
            if not b:
                continue
            x0, x1, y0, y1 = b
            body.append((pg, x0 / px_per_pt, x1 / px_per_pt))

    rights = [r for _, _, r in body]
    lefts = [l for _, l, _ in body]
    # 版心右界 = 各页右界的**众数区间**（多数页没有越界）
    import statistics as st
    r_typ = st.median(rights)
    l_typ = st.median(lefts)
    print(f"  版心估计：左 {l_typ:.1f} pt ｜ 右 {r_typ:.1f} pt ｜ **宽 {r_typ-l_typ:.1f} pt**")
    print(f"  右界范围：{min(rights):.1f} ~ {max(rights):.1f} pt")
    print()
    print("=== 右界明显超出中位数的页（可能真越界）===")
    for pg, l, r in body:
        if r > r_typ + 2:
            over.append((pg, r))
            print(f"  第 {pg:} 页: 右界 {r:.1f} pt（超出 {r-r_typ:+.1f}）")
    if not over:
        print("  ✅ **无页越界** —— 那些 `Overfull \\hbox` 是 LaTeX 对浮动体盒子的度量噪声")
    else:
        print(f"\n  ⚠ {len(over)} 页存在越界，需修（最大超出 {max(r for _, r in over)-r_typ:.1f} pt）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
