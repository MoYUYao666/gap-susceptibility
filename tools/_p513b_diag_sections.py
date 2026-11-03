# -*- coding: utf-8 -*-
"""诊断：按段落列出 P3 四个压缩目标的字符分布（只读，2026-10-13）。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _p513_compress_p3_sections as m  # noqa: E402

for nm, blk, tgt in (("THEORY", m.THEORY, m.TARGETS["paper3/paper_ieee/sections/theory.tex"]),
                     ("INTRO", m.INTRO, m.TARGETS["paper3/paper_ieee/sections/introduction.tex"]),
                     ("DISC", m.DISCUSSION, m.TARGETS["paper3/paper_ieee/sections/discussion.tex"]),
                     ("CONCL", m.CONCLUSION, m.TARGETS["paper3/paper_ieee/sections/conclusion.tex"])):
    total = sum(len(x) for x in blk) + len(blk) - 1
    print("=" * 92)
    print(f"{nm}: {len(blk)} lines, {total:,} chars, target {tgt:,}, need to cut {total-tgt:,}")
    print("=" * 92)
    cur, acc, first = "(head)", 0, ""
    idx = 0
    for x in blk:
        if x.startswith("\\subsection") or x.startswith("\\section"):
            if acc:
                print(f"  [{idx:>2}] {acc:>5,}  {first[:62]}")
            idx += 1
            cur, acc, first = x, len(x), x
        else:
            if not acc:
                first = x
            acc += len(x) + 1
    if acc:
        print(f"  [{idx:>2}] {acc:>5,}  {first[:62]}")
