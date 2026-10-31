# -*- coding: utf-8 -*-
r"""把 `main_full.tex` 文件头的中文注释改为英文（2026-10-14）。

## 操作者要求

> **"注意要全英文"**

## 现状

`paper3/paper_ieee/main_full.tex` 前 7 行是中文注释（**72 个中文字符**），
该文件会随 LaTeX 源包交给编辑部 ⇒ **必须全英文**。

    python tools\_p590_english_main_full.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
P = REPO / "paper3" / "paper_ieee" / "main_full.tex"

OLD_MARK = "% ============================================================================"

NEW_HEAD = r"""% ============================================================================
% main_full.tex -- the FULL version (13 pages), archived so that the complete
% argument and every number remain available (for the response letter and for
% reviewers who ask for them).
%
%   The journal's Mandatory Submission Requirements specify a two-column
%   manuscript of at most 7 pages, so this file is NOT the submission. The
%   submission is main.tex (10 pages), with the axiom derivation, full proofs,
%   protocol details, per-run tables and additional figures in supplementary/.
%
%   This file inputs sections_full/..., which is independent of the sections/
%   tree used by main.tex, so editing one does not affect the other.
% ============================================================================
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(P, encoding="utf-8", errors="replace").read()
    i = t.find(OLD_MARK)
    j = t.find("\\documentclass", i) if i >= 0 else -1
    print(f"  文件 {len(t):,} 字符 ｜ 头部注释区间 i={i}, j={j}")
    if i < 0 or j < 0:
        print("  🔴 锚点未命中")
        return 1
    old = t[i:j]
    print(f"  旧头部 {len(old)} 字符（含中文 {len([c for c in old if '\u4e00' <= c <= '\u9fff'])} 个）")
    if not a.apply:
        print("  （预演）")
        return 0
    bak = P.with_suffix(".tex.bak_p590")
    if not bak.exists():
        shutil.copy2(P, bak)
    io.open(P, "w", encoding="utf-8", newline="").write(NEW_HEAD + t[j:])
    t2 = io.open(P, encoding="utf-8", errors="replace").read()
    import re
    cjk = re.findall(r"[\u4e00-\u9fff]", t2)
    print(f"  ✅ 已改写：{len(t2):,} 字符 ｜ 残留中文 **{len(cjk)}** 个")
    print("  新头部前 12 行：")
    for l in t2.splitlines()[:12]:
        print("     " + l[:100])
    return 0 if not cjk else 2


if __name__ == "__main__":
    raise SystemExit(main())
