# -*- coding: utf-8 -*-
r"""核 Neural Networks 对各类声明的要求（2026-10-10）。

    python tools\_p133_nn_declarations.py
"""
from __future__ import annotations

import io
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
G = REPO / "期刊指南" / "_guide_neuralnetworks.txt"


def find(txt: str, pat: str, n: int = 2, w: int = 460):
    out = []
    for m in re.finditer(pat, txt, re.I):
        s = " ".join(txt[max(0, m.start() - 100):m.start() + w].split())
        if s[:60] not in [o[:60] for o in out]:
            out.append(s)
        if len(out) >= n:
            break
    return out


def main() -> int:
    t = io.open(G, encoding="utf-8", errors="replace").read()
    checks = [
        ("Declaration of competing interests", r"Declaration of competing interests.{0,600}"),
        ("Declaration of generative AI（正文用）", r"Declaration of generative AI in scientific writing.{0,700}"),
        ("AI 用于图/图像", r"Generative AI[^.]{0,80}figures, images.{0,500}"),
        ("Funding sources", r"Funding sources.{0,500}"),
        ("Submission declaration（未在他刊）", r"Submission declaration and verification.{0,600}"),
        ("Cover letter / 投稿信", r"cover letter.{0,400}"),
        ("Highlights 具体规则", r"Highlights.{0,260}(3 to 5|85 characters).{0,260}"),
        ("Title page 内容", r"Title page.{0,500}"),
        ("Author contributions (CRediT)", r"CRediT.{0,500}"),
    ]
    for tag, pat in checks:
        print(f"\n{'=' * 64}\n{tag}\n{'=' * 64}")
        hits = find(t, pat)
        if not hits:
            print("  （Guide 未按此措辞提及）")
        for h in hits:
            print("  • " + h[:520])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
