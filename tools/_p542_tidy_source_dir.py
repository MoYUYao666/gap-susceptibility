# -*- coding: utf-8 -*-
r"""整理 `paper3/paper_ieee/` 顶层：构建产物、测试件、过期交付件分层归档（2026-10-13）。

## 分类（顶层 46 个文件）

| 类 | 件数 | 处置 |
|---|---|---|
| **源文件**（`main*.tex`、`references.bib`、`cover_letter_prl.tex`、`title_page_prl.tex`、`audit_*.py`） | 10 | **留在顶层** |
| **PDF 交付件**（`main.pdf`、`main_full.pdf`、`cover_letter_prl.pdf`、`title_page_prl.pdf`） | 4 | **留在顶层** |
| **LaTeX 构建产物**（`.aux/.log/.out/.bbl/.blg/.fls/.fdb_latexmk/.spl`） | 22 | → **`_build/`** |
| **测试件**（`main_els_test.*` 5 个 + `_p3.txt` + 两个 `compile_*.log`） | 8 | → **`_scratch/`** |
| **过期交付件**（`main_submission_old.zip`） | 1 | → **`_superseded/`** |
| **疑似非本稿**（`Reviewer.pdf` 1.3 MB） | 1 | **标注待核，不移动** |

**⚠️ 纪律**：**所有移动都是"归档 + 记账"，不删除**；移动前确认目标路径。
**⚠️ `Reviewer.pdf` 1.3 MB 来源不明** ⇒ **只标注，不处置**（可能是审稿意见扫描件或他稿材料）。

    python tools\_p542_tidy_source_dir.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PI = REPO / "paper3" / "paper_ieee"

BUILD_EXT = {".aux", ".log", ".out", ".bbl", ".blg", ".fls", ".fdb_latexmk", ".spl", ".toc", ".synctex.gz"}
SCRATCH_NAMES = {"_p3.txt", "compile_p3.log", "compile_p513.log"}
SUPERSEDED_NAMES = {"main_submission_old.zip"}
KEEP_STEMS = {"main", "main_full", "main_10pp", "main_body_full", "main_els_test",
              "cover_letter_prl", "title_page_prl"}


def classify(p: Path) -> str:
    n = p.name
    if p.suffix in BUILD_EXT and not n.startswith("main_els_test"):
        return "build"
    if n.startswith("main_els_test"):
        return "scratch"
    if n in SCRATCH_NAMES:
        return "scratch"
    if n in SUPERSEDED_NAMES:
        return "superseded"
    return "keep"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    files = [p for p in PI.iterdir() if p.is_file()]
    groups = {"keep": [], "build": [], "scratch": [], "superseded": []}
    for p in files:
        groups[classify(p)].append(p)
    print("=" * 96)
    print(f"顶层 {len(files)} 个文件")
    print("=" * 96)
    for g in ("keep", "build", "scratch", "superseded"):
        tot = sum(p.stat().st_size for p in groups[g])
        print(f"  {g:<12} {len(groups[g]):>3} 个 ｜ {tot/1024:>9.0f} KB")
    print()
    print("  明细：")
    for g in ("keep", "build", "scratch", "superseded"):
        names = ", ".join(sorted(p.name for p in groups[g])[:10])
        more = " …" if len(groups[g]) > 10 else ""
        print(f"     {g:<12} {names}{more}")

    # 疑似非本稿
    rv = PI / "Reviewer.pdf"
    print()
    if rv.exists():
        print(f"  ⚠️ `Reviewer.pdf`（{rv.stat().st_size/1024:.0f} KB）**来源不明，只标注不移动**")
        print(f"     ⇒ 待核：是本稿的审稿意见扫描件，还是他稿材料？")

    if not a.apply:
        print()
        print("  （预演）")
        return 0
    mapping = {"build": "_build", "scratch": "_scratch", "superseded": "_superseded"}
    for g, sub in mapping.items():
        ps = groups[g]
        if not ps:
            continue
        dst_dir = PI / sub
        dst_dir.mkdir(exist_ok=True)
        for p in ps:
            # ⚠️ 移动前确认目标绝对路径
            tgt = (dst_dir / p.name).resolve()
            assert str(tgt).startswith(str(PI.resolve())), f"目标越界：{tgt}"
            shutil.move(str(p), str(tgt))
        print(f"  ✅ {len(ps):>3} 个 → {sub}/")

    print()
    print("  复核（顶层剩余）：")
    left = sorted(p for p in PI.iterdir() if p.is_file())
    print(f"     {len(left)} 个文件")
    for p in left:
        print(f"       {p.name:<30} {p.stat().st_size:>9,} B")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
