# -*- coding: utf-8 -*-
r"""Neural Networks Guide 的关键约束逐条核对（2026-10-10）。

针对 A1 的合规检查：摘要词数、关键词数、参考文献样式、LaTeX 类、ATS 保留、
以及"同期不得在他刊审稿"的声明要求。

    python tools\_p101_nn_compliance.py
"""
from __future__ import annotations

import io
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
G = REPO / "期刊指南" / "_guide_neuralnetworks.txt"


def find(txt: str, pat: str, n: int = 3, w: int = 420):
    out = []
    for m in re.finditer(pat, txt, re.I):
        s = " ".join(txt[max(0, m.start() - 120):m.start() + w].split())
        if s[:60] not in [o[:60] for o in out]:
            out.append(s)
        if len(out) >= n:
            break
    return out


def main() -> int:
    t = io.open(G, encoding="utf-8", errors="replace").read()

    checks = [
        ("摘要长度上限", r"abstract should not exceed|abstract .{0,60}words|no more than \d+ words"),
        ("Open access / APC", r"open access.{0,300}"),
        ("Article Transfer Service", r"Article Transfer Service.{0,300}"),
        ("LaTeX 类文件", r"(elsarticle|cas-|els-cas|LaTeX).{0,220}"),
        ("APA 引用样例", r"American Psychological Association.{0,400}"),
        ("同期不得在他刊审稿", r"not (be )?(published|under (review|consideration)).{0,200}"),
        ("Highlights 条数与字数", r"Highlights.{0,120}(3 to 5|85 characters|maximum).{0,220}"),
        ("Figures 要求", r"(TIFF|EPS|300 dpi|1000 dpi).{0,200}"),
        ("Supplementary", r"Supplementary material.{0,220}"),
    ]
    for tag, pat in checks:
        print(f"\n── {tag} ──")
        hits = find(t, pat)
        if not hits:
            print("   （Guide 中未按此措辞提及）")
        for h in hits:
            print(f"   • {h[:400]}")

    # 关键词与声明
    print("\n── 关键词数量 ──")
    for h in find(t, r"required to provide \d+ to \d+ keywords"):
        print(f"   • {h[:200]}")

    print("\n── 投稿声明（Submission declaration）──")
    for h in find(t, r"Submission declaration.{0,500}", n=1):
        print(f"   • {h[:520]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
