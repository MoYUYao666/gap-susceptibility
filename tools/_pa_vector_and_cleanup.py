# -*- coding: utf-8 -*-
r"""B-3 清理未引用图 + B-4 LaTeX 切矢量 PDF（2026-10-06）。

## B-3：15 张未引用的图 → `figures/_superseded/`

`paper合/figures/` 有 **31 张 PNG**，正文只用 **16 张**。未引用的 15 张
（`fig11_gsnr`、`fig13_vitl_layered`、`fig5`、`fig6`、`fig7`、`fig8a_weight_norms` 等）
**来自 ap3 阶段**，`paper合` 从不引用。**只移不删**，保留可回溯。

## B-4：`\includegraphics{.png}` → `.pdf`（矢量）

**为什么**：PDF 矢量**任意缩放不糊**，期刊排版偏好矢量；PNG 在放大时会有栅格化痕迹。
16 张图**均已出 PDF 矢量版**（`save()` 同时写 PNG+PDF）。

**风险控制**：
- 切换后**重新编译**，确认 0 错误；
- 用 `pdffonts` 抽查图内字体仍嵌入；
- **PNG 保留**（`save()` 两者都写），只是 LaTeX 改用 PDF。

    python tools\_pa_vector_and_cleanup.py [--apply]
"""
from __future__ import annotations

import glob
import io
import os
import re
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
FIGDIR = REPO / "paper合" / "figures"
ARCH = FIGDIR / "_superseded"
SECTIONS = sorted(glob.glob(str(REPO / "paper合" / "sections" / "*.tex")))


def used_names() -> set[str]:
    used = set()
    for f in SECTIONS:
        t = io.open(f, encoding="utf-8").read()
        used |= set(re.findall(r"includegraphics(?:\[[^\]]*\])?\{figures/([^}]+)\}", t))
    return used


def main() -> int:
    apply = "--apply" in sys.argv
    used = used_names()
    have = {os.path.basename(p) for p in glob.glob(str(FIGDIR / "*.png"))}
    unused = sorted(have - used)

    print(f"=== B-3 清理 ===")
    print(f"  figures/ PNG {len(have)} 张 ｜ 正文引用 {len(used)} 张 ｜ 未引用 {len(unused)} 张")
    for f in unused:
        print(f"    {f}")

    print(f"\n=== B-4 切矢量 ===")
    missing_pdf = [f for f in sorted(used)
                   if not (FIGDIR / (os.path.splitext(f)[0] + ".pdf")).exists()]
    if missing_pdf:
        print(f"  ❌ 缺 PDF：{missing_pdf} —— **不切换**（先出齐 PDF）")
        return 1
    print(f"  16/16 图均有 PDF 矢量版 ✅")

    if not apply:
        print("\n  （预演，加 --apply）")
        return 0

    # ── B-3
    ARCH.mkdir(exist_ok=True)
    moved = 0
    for f in unused:
        base = os.path.splitext(f)[0]
        for ext in (".png", ".pdf"):
            p = FIGDIR / (base + ext)
            if p.exists():
                shutil.move(str(p), str(ARCH / p.name))
                moved += 1
    print(f"  ✅ 已移入 _superseded/：{moved} 个文件")

    # ── B-4
    n = 0
    for f in SECTIONS:
        t = io.open(f, encoding="utf-8").read()
        o = t
        for fig in sorted(used):
            if fig.endswith(".png"):
                t = t.replace("figures/" + fig, "figures/" + os.path.splitext(fig)[0] + ".pdf")
        if t != o:
            io.open(f, "w", encoding="utf-8", newline="").write(t)
            n += 1
    print(f"  ✅ 已把 {n} 个 section 文件的 includegraphics 改为 .pdf")

    # 核对
    left = 0
    for f in SECTIONS:
        left += io.open(f, encoding="utf-8").read().count(".png}")
    print(f"  残留 '.png}}' 引用: {left} {'✅' if left == 0 else '❌'}")

    print(f"\n  figures/ 现有 PNG {len(glob.glob(str(FIGDIR / '*.png')))} 张"
          f" ｜ PDF {len(glob.glob(str(FIGDIR / '*.pdf')))} 个")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
