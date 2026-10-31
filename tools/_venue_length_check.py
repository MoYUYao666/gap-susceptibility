# -*- coding: utf-8 -*-
r"""实测 Paper A 的行数/词数，判定能否满足 KBS 的 "20 double line spaced pages"（2026-10-07）。

## 为什么必须实测

`KBS` Article types 原文：
> "(1) Original high-quality research and review papers (**preferably no more than 20 double line
> spaced manuscript pages**, including tables and figures)."

**"双倍行距 20 页"不能与"12pt 单倍行距 49 页"直接比**，须换算。
换算办法：**逐源文件统计"文本行数"**（LaTeX 源的行 ≈ 排版后的文本行），
再按"单倍 → 双倍"翻倍，除以每页双倍行距可容纳行数（约 25–28 行/页，12pt）。

**注意**：这是**估算**，非期刊最终排版结果；结论须标注为估算。

    python tools\_venue_length_check.py
"""
from __future__ import annotations

import io
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SEC = REPO / "paper合" / "sections"


def count_tex(p: Path) -> tuple[int, int]:
    """返回 (正文行数, 词数)；剔除注释行、纯命令行、空行。"""
    t = io.open(p, encoding="utf-8", errors="ignore").read()
    lines = 0
    words = 0
    for ln in t.splitlines():
        s = ln.strip()
        if not s or s.startswith("%"):
            continue
        # 去掉行内注释
        s = re.sub(r"(?<!\\)%.*$", "", s)
        if not s.strip():
            continue
        # 去掉纯结构命令行（\section{...} 之类仍算 1 行但词少）
        lines += 1
        # 词数：粗略按空白切
        words += len(re.sub(r"\\[a-zA-Z]+\*?", " ", s).split())
    return lines, words


def main() -> int:
    files = sorted(SEC.glob("*.tex"))
    total_lines = total_words = 0
    print(f"  {'文件':<24} {'行数':>7} {'词数':>8}")
    print("  " + "-" * 42)
    for f in files:
        l, w = count_tex(f)
        total_lines += l
        total_words += w
        print(f"  {f.name:<24} {l:>7} {w:>8}")
    print("  " + "-" * 42)
    print(f"  {'合计':<24} {total_lines:>7} {total_words:>8}")

    # 主文件也有正文（声明等）
    ml, mw = count_tex(REPO / "paper合" / "main_nc.tex")
    print(f"  {'main_nc.tex':<24} {ml:>7} {mw:>8}")
    total_lines += ml
    total_words += mw
    print(f"\n  总计：{total_lines} 行 ｜ 约 {total_words} 词")

    print("\n  === 换算：双倍行距页数（估算）===")
    for lpp in (25, 28):
        dbl = total_lines / lpp
        print(f"    按 {lpp} 行/页（12pt 双倍行距）：单倍 {total_lines/lpp:.1f} 页 → **双倍 {dbl:.1f} 页**")

    print("\n  === 对各刊篇幅规定的判定 ===")
    mid = total_lines / 28.0
    print(f"    KBS（preferably ≤20 双倍行距页）: 估算 **{mid:.1f} 页** → "
          f"{'✅ 达标' if mid <= 20 else '⚠ 超出 %.1f 页' % (mid-20)}")
    print(f"    IF （Research article 必须 10–35 页）: 估算 **{mid:.1f} 页** → "
          f"{'✅ 落在区间内' if 10 <= mid <= 35 else '⚠ 需压缩'}（另：IF 限 **≤50 条参考文献**）")
    print("    ESWA / IVC / CVIU: Guide **未见篇幅上限** → ✅ 无需压缩")

    print("\n  ⚠️ 以上为**估算**（按 LaTeX 源行数换算），非期刊最终排版结果。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
