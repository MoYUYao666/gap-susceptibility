# -*- coding: utf-8 -*-
r"""核验修订包目录结构（含 `_superseded/` 是否正确建立）（2026-10-13）。

    python tools\_p545_verify_package_tree.py
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
D = REPO / "SUBMISSION" / "P3_PRL_revision"


def main() -> int:
    print(f"  目标 {D.relative_to(REPO)} ｜ 存在 {D.exists()}")
    print()
    print("=" * 92)
    print("逐层树（带完整相对路径）")
    print("=" * 92)
    n = 0
    tot = 0
    for p in sorted(D.rglob("*")):
        if p.is_file():
            rel = p.relative_to(D)
            n += 1
            tot += p.stat().st_size
            print(f"  {str(rel):<58} {p.stat().st_size:>9,} B")
    print()
    print(f"  ⇒ {n} 个文件 / {tot/1024:.1f} KB")

    print()
    print("=" * 92)
    print("关键项定位")
    print("=" * 92)
    checks = [
        ("投稿件（10 页）", D / "manuscript" / "main.pdf"),
        ("补充材料（5 页）", D / "manuscript" / "supplementary.pdf"),
        ("完整版（13 页）", D / "manuscript" / "main_full.pdf"),
        ("LaTeX 源目录", D / "manuscript" / "latex_source"),
        ("33 条回复信", D / "response" / "P3_RESPONSE_LETTER.md"),
        ("过期件目录", D / "_superseded"),
        ("过期件本体", D / "_superseded" / "main_REVISING.pdf"),
        ("**过期件不应在**", D / "manuscript" / "main_REVISING.pdf"),
    ]
    for label, p in checks:
        ex = p.exists()
        bad = label.startswith("**过期件不应在")
        flag = "🔴" if (bad == ex) else "✅"
        kind = "目录" if p.is_dir() else ("文件" if p.exists() else "—")
        print(f"  {flag} {label:<22} {kind:<4} {'存在' if ex else '不存在'}")

    print()
    print("=" * 92)
    print("顶层条目")
    print("=" * 92)
    for p in sorted(D.iterdir()):
        kind = "目录" if p.is_dir() else "文件"
        cnt = sum(1 for _ in p.rglob("*") if _.is_file()) if p.is_dir() else ""
        print(f"  {p.name:<20} {kind}  {cnt}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
