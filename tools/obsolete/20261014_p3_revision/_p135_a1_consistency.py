# -*- coding: utf-8 -*-
r"""A1 投稿件一致性终检（2026-10-10）。

检查**所有** A1 投稿件里是否还有：
- 旧标题（`Order Preservation Governs Zero-Shot Robustness`）
- 旧刊名（`Neurocomputing`）
- 错误邮箱（`hrw1n24@soton.ac.uk`）
- 旧日期（`16 September 2026`）

    python tools\_p135_a1_consistency.py
"""
from __future__ import annotations

import glob
import io
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
A1 = REPO / "paper_a1"

STALE = [
    ("Order Preservation Governs Zero-Shot Robustness", "旧标题"),
    ("Neurocomputing", "旧刊名"),
    ("hrw1n24@soton.ac.uk", "我写错的邮箱"),
    ("16 September 2026", "旧日期"),
    ("The Modality Gap Is Not a Universal Health Metric: Order\\", "旧标题（换行写法）"),
]
TEX = ["main.tex", "cover_letter.tex", "declaration.tex", "highlights.tex",
       "abstract.tex", "related_work.tex"]


def main() -> int:
    print(f"=== 逐份投稿件扫描（{A1.name}/）===")
    bad_total = 0
    for name in TEX:
        f = A1 / name
        if not f.exists():
            print(f"  {name:<22} （不存在）")
            continue
        t = io.open(f, encoding="utf-8", errors="replace").read()
        hits = []
        for pat, tag in STALE:
            n = t.count(pat)
            if n:
                hits.append(f"{tag}×{n}")
        status = "✅ 干净" if not hits else "❌ " + " ｜ ".join(hits)
        if hits:
            bad_total += 1
        print(f"  {name:<22} {status}")

    print("\n=== 新版关键内容是否到位 ===")
    cl = io.open(A1 / "cover_letter.tex", encoding="utf-8", errors="replace").read()
    for k, tag in (("Neural Networks", "刊名"),
                   ("Zero-Overhead", "新标题关键词"),
                   ("not yet submitted", "披露（姊妹稿未投）"),
                   ("PR-D-26-10149", "P1 投 PR 的事实"),
                   ("Prior consideration", "曾投他刊声明"),
                   ("contact@example.com", "正确邮箱"),
                   ("10 October 2026", "日期")):
        print(f"  {'✅' if k in cl else '❌'} {tag}: {k}")

    print("\n=== 所有投稿件的 PDF 是否比 tex 新 ===")
    for name in ("main", "cover_letter", "declaration", "highlights"):
        tex, pdf = A1 / f"{name}.tex", A1 / f"{name}.pdf"
        if tex.exists() and pdf.exists():
            newer = pdf.stat().st_mtime >= tex.stat().st_mtime
            print(f"  {name:<16} {'✅ PDF 最新' if newer else '⚠️ PDF 比 tex 旧，需重编译'}")

    print(f"\n=== 结论：{len(TEX) - bad_total}/{len(TEX)} 份干净 ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
