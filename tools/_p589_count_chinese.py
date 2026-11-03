# -*- coding: utf-8 -*-
r"""清点发布库里的中文（2026-10-14）。

## 操作者要求

> **"注意要全英文"**

## 先判范围

| 候选范围 | 说明 |
|---|---|
| **A. GitHub 发布库**（`publish_clean/`） | 对外公开 → **必须全英文** |
| **B. 投稿件**（`main.tex` / 补充材料 / 回复信 / cover letter / highlights） | 给 PRL 与审稿人 → **必须全英文** |
| C. 内部文档（`HANDOFF.md` / `docs/` / `文件地图.md`） | 内部用 → 中文可留 |

**⇒ 本脚本按 A 与 B 分别清点。**

    python tools\_p589_count_chinese.py
"""
from __future__ import annotations

import collections
import io
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CJK = re.compile(r"[\u4e00-\u9fff]")
CJK_STRONG = re.compile(r"[\u4e00-\u9fff]{2,}")

PC = REPO / "publish_clean"
PI = REPO / "paper3" / "paper_ieee"
SUBM = REPO / "SUBMISSION" / "P3_PRL_revision"


def scan(root: Path, label: str, exts=None, limit=20):
    print("=" * 100)
    print(f"{label}")
    print("=" * 100)
    if not root.exists():
        print("  （不存在）")
        return {}
    per = collections.Counter()
    chars = collections.Counter()
    files = [p for p in root.rglob("*") if p.is_file() and ".git" not in p.parts]
    for p in files:
        if exts and p.suffix.lower() not in exts:
            continue
        try:
            t = io.open(p, encoding="utf-8", errors="strict").read()
        except Exception:
            continue
        n = len(CJK.findall(t))
        if n:
            per[p.relative_to(root).as_posix()] = n
            chars["总字符"] += n
    tot_files = len(per)
    tot_chars = sum(per.values())
    print(f"  含中文的文件：**{tot_files} / {len(files)}** ｜ 中文字符总数 **{tot_chars}**")
    print()
    print(f"  中文字符最多的 {limit} 个：")
    for f, n in per.most_common(limit):
        print(f"     {n:>6}  {f}")
    return per


def main() -> int:
    a = scan(PC, "A. GitHub 发布库（publish_clean/）—— 对外，必须全英文")
    print()
    b = scan(PI, "B1. 投稿件源（paper3/paper_ieee/，含 sections / supplementary）",
             exts={".tex", ".bib"})
    print()
    c = scan(SUBM, "B2. 修订包（SUBMISSION/P3_PRL_revision/，审稿人可见）")
    print()
    print("=" * 100)
    print("合计")
    print("=" * 100)
    print(f"  A 发布库      ：{len(a)} 个文件含中文（{sum(a.values())} 字符）")
    print(f"  B1 投稿件源   ：{len(b)} 个文件含中文（{sum(b.values())} 字符）")
    print(f"  B2 修订包     ：{len(c)} 个文件含中文（{sum(c.values())} 字符）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
