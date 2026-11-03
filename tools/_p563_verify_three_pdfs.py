# -*- coding: utf-8 -*-
r"""核查 cover letter / title page / highlights 三份 PDF 的内容与口径（2026-10-14）。

    python tools\_p563_verify_three_pdfs.py
"""
from __future__ import annotations

import io
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PI = REPO / "paper3" / "paper_ieee"
PDFS = {
    "cover letter": PI / "cover_letter_prl.pdf",
    "title page": PI / "title_page_prl.pdf",
    "highlights": PI / "PRL_submission" / "highlights.pdf",
}
BAN = [("the unique scalar", "unique 主张"),
       ("phase transition with a critical rank", "sharp 相变"),
       ("A critical rank separates", "critical rank"),
       ("190 runs", "旧计数"),
       ("30\\times", "30x"),
       ("architectural differences", "架构差异"),
       ("allocation uncertainty", "不确定性"),
       ("School of Electronics", "院系")]


def text(p: Path) -> str:
    r = subprocess.run(["pdftotext", "-layout", str(p), "-"], capture_output=True)
    return r.stdout.decode("utf-8", errors="replace")


def main() -> int:
    ok = True
    for label, p in PDFS.items():
        if not p.exists():
            print(f"  🔴 缺 {label}: {p.name}")
            ok = False
            continue
        t = text(p)
        n_page = subprocess.run(["pdfinfo", str(p)], capture_output=True)
        pages = ""
        for ln in n_page.stdout.decode("utf-8", errors="replace").splitlines():
            if ln.startswith("Pages:"):
                pages = ln.split(":", 1)[1].strip()
        print("=" * 96)
        print(f"{label} ｜ {p.name} ｜ {pages} 页 ｜ 提取 {len(t):,} 字符")
        print("=" * 96)
        # 打印前若干行
        lines = [x.rstrip() for x in t.splitlines() if x.strip()]
        for l in lines[:16]:
            print("  " + l[:104])
        print()
        # 禁用串检查
        for bad, bl in BAN:
            n = t.count(bad)
            if n:
                print(f"  🔴 {bl}: {n} 处")
                ok = False
        # 关键要素
        for need, nl in (("Pattern Recognition Letters", "期刊名"),
                         ("University of Southampton", "单位"),
                         ("hw4c24@soton.ac.uk", "邮箱")):
            v = need in t
            if not v:
                print(f"  🔴 缺 {nl}")
                ok = False
        print("  ✅ 禁用串与必需项检查完成")
        print()
    print(f"  **判定：{'✅ 三份 PDF 口径正确' if ok else '🔴 有问题'}**")
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
