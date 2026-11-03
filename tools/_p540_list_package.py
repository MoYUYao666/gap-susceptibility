# -*- coding: utf-8 -*-
r"""列出 P3 修订包与相关目录的完整树（2026-10-13）。

    python tools\_p540_list_package.py
"""
from __future__ import annotations

import io
import os
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def tree(root: Path, prefix: str = ""):
    if not root.exists():
        print(f"  🔴 不存在：{root}")
        return 0, 0
    n_files = 0
    total = 0
    items = sorted(root.iterdir(), key=lambda p: (p.is_file(), p.name.lower()))
    for i, p in enumerate(items):
        last = (i == len(items) - 1)
        br = "└── " if last else "├── "
        if p.is_dir():
            print(f"  {prefix}{br}{p.name}/")
            a, b = tree(p, prefix + ("    " if last else "│   "))
            n_files += a
            total += b
        else:
            sz = p.stat().st_size
            mt = time.strftime("%m-%d %H:%M", time.localtime(p.stat().st_mtime))
            extra = ""
            if p.suffix == ".pdf":
                extra = "  [PDF]"
            elif p.suffix in (".tex", ".bib"):
                extra = "  [LaTeX]"
            elif p.suffix == ".json":
                extra = "  [JSON]"
            print(f"  {prefix}{br}{p.name:<52} {sz:>9,} B  {mt}{extra}")
            n_files += 1
            total += sz
    return n_files, total


def main() -> int:
    print("=" * 104)
    print("① 修订包（提交用）")
    print("=" * 104)
    for d in ("SUBMISSION/P3_PRL_revision",):
        p = REPO / d
        print(f"  {d}/")
        n, t = tree(p, "")
        print(f"\n  ⇒ {n} 个文件 / {t/1024:.1f} KB")

    print()
    print("=" * 104)
    print("② SUBMISSION/ 下的其他目录（看是否需归类）")
    print("=" * 104)
    sd = REPO / "SUBMISSION"
    if sd.exists():
        for p in sorted(sd.iterdir()):
            if p.is_dir():
                cnt = sum(1 for _ in p.rglob("*") if _.is_file())
                print(f"  {p.name + '/':<40} {cnt:>5} 个文件")
            else:
                print(f"  {p.name:<40} {p.stat().st_size:>9,} B")

    print()
    print("=" * 104)
    print("③ paper3/paper_ieee/ 现状（源目录）")
    print("=" * 104)
    pi = REPO / "paper3" / "paper_ieee"
    for name in ("main.tex", "main.pdf", "main_full.tex", "main_full.pdf",
                 "main_10pp.tex", "main_els_test.tex", "main_els_test.pdf"):
        p = pi / name
        if p.exists():
            print(f"  {name:<28} {p.stat().st_size:>9,} B")
    for sub in ("sections", "sections_full", "supplementary", "figures", "PRL_submission"):
        p = pi / sub
        if p.is_dir():
            cnt = sum(1 for _ in p.rglob("*") if _.is_file())
            print(f"  {sub + '/':<28} {cnt:>5} 个文件")
    # 备份文件
    baks = sorted(pi.rglob("*.bak*"))
    print(f"  **备份文件（.bak*）: {len(baks)} 个**")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
