# -*- coding: utf-8 -*-
r"""量出 PRL 稿件里"正文/图/表/参考文献/前置块"各占多少页，用于决定砍哪里。

    python tools/_measure_prl_layout.py
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "paper_review_prl"
PDF = OUT / "main_prl.pdf"


def page_words(p: int) -> int:
    out = subprocess.run(["pdftotext", "-f", str(p), "-l", str(p), str(PDF), "-"],
                         capture_output=True).stdout.decode("utf-8", "ignore")
    return sum(len(l.split()) for l in out.splitlines() if l.strip())


def main() -> int:
    info = subprocess.run(["pdfinfo", str(PDF)], capture_output=True).stdout.decode("utf-8", "ignore")
    pages = int(re.search(r"Pages:\s+(\d+)", info).group(1))
    print(f"总页数: {pages}\n")

    # 找正文结束页（Conclusions 结束）与参考文献开始页
    ref_start = None
    body_end = None
    for p in range(1, pages + 1):
        t = subprocess.run(["pdftotext", "-f", str(p), "-l", str(p), str(PDF), "-"],
                           capture_output=True).stdout.decode("utf-8", "ignore")
        if ref_start is None and re.search(r"References\s*$", t.strip()) or (ref_start is None and "References" in t):
            ref_start = p
        if body_end is None and "References" in t:
            body_end = p
    for p in range(1, pages + 1):
        w = page_words(p)
        tag = ""
        if p == ref_start:
            tag = "  ← 参考文献自此开始"
        print(f"  第 {p} 页: {w:4d} 词{tag}")

    # 统计参考文献条目数与正文词数
    tex = (OUT / "main_prl.tex").read_text(encoding="utf-8")
    n_refs = tex.count("\\bibitem")
    body_tex = tex.split("\\begin{thebibliography}")[0]
    body_words = len([w for w in re.findall(r"[A-Za-z']+", body_tex)])
    print(f"\n参考文献 {n_refs} 条 ｜ 正文（含标题/摘要/图注）约 {body_words} 词")
    if ref_start:
        print(f"参考文献约 {pages - ref_start + 1} 页；正文+前置约 {ref_start - 1} 页")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
