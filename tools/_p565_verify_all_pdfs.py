# -*- coding: utf-8 -*-
r"""核验全部 PDF：页数 / 错误 / 未定义 / 断头残留（2026-10-14）。

    python tools\_p565_verify_all_pdfs.py
"""
from __future__ import annotations

import io
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PI = REPO / "paper3" / "paper_ieee"
PDFS = [
    ("main（投稿件）", PI / "main.pdf", PI / "main.log"),
    ("main_full（完整版）", PI / "main_full.pdf", PI / "main_full.log"),
    ("supplementary（补充）", PI / "supplementary" / "supplementary.pdf",
     PI / "supplementary" / "supplementary.log"),
    ("cover letter", PI / "cover_letter_prl.pdf", PI / "cover_letter_prl.log"),
    ("title page", PI / "title_page_prl.pdf", PI / "title_page_prl.log"),
    ("highlights", PI / "PRL_submission" / "highlights.pdf",
     PI / "PRL_submission" / "highlights.log"),
]


def pages(p: Path):
    r = subprocess.run(["pdfinfo", str(p)], capture_output=True)
    for ln in r.stdout.decode("utf-8", errors="replace").splitlines():
        if ln.startswith("Pages:"):
            return ln.split(":", 1)[1].strip()
    return "?"


def text(p: Path):
    r = subprocess.run(["pdftotext", "-layout", str(p), "-"], capture_output=True)
    return r.stdout.decode("utf-8", errors="replace")


def main() -> int:
    print(f"  {'文件':<24} {'页数':>4} {'错误':>5} {'未定义':>6} {'oindent/abla':>13}")
    ok = True
    for label, pdf, log in PDFS:
        if not pdf.exists():
            print(f"  🔴 {label}: 缺 PDF")
            ok = False
            continue
        pg = pages(pdf)
        t = text(pdf)
        er = len(re.findall(r"^!", io.open(log, encoding="utf-8", errors="replace").read(), re.M)) if log.exists() else -1
        un = t.count("??")
        sev = len(re.findall(r"\boindent|\babla\b", t))
        flag = "✅" if (er == 0 and sev == 0) else "🔴"
        ok = ok and er == 0 and sev == 0
        print(f"  {flag} {label:<22} {pg:>4} {er:>5} {un:>6} {sev:>13}")
    print()
    print("  说明：「未定义」列用 PDF 文本里的 `??` 计数（LaTeX 未解析引用会印成 `??`）；")
    print("        `oindent`/`abla` 计数 = **PDF 里是否印出错字**（断头命令的直接证据）。")
    print()
    print(f"  **判定：{'✅ 全部干净' if ok else '🔴 有问题'}**")
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
