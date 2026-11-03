# -*- coding: utf-8 -*-
r"""提取 Neural Networks 的 Guide for Authors 关键约束（2026-10-10）。

路径：桌面 PDF（操作者提供）。**所有字段取自 Guide 原文，未提及者写"未提及"，
不填第三方数字**（项目规则）。

    python tools\_p100_nn_guide.py [--apply]
"""
from __future__ import annotations

import io
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PDF = Path(r"C:\Users\hongr\Desktop\Guide for authors - Neural Networks - ISSN 0893-6080 _ ScienceDirect.com by Elsevier.pdf")
OUT = REPO / "期刊指南" / "_guide_neuralnetworks.txt"

KEYS = [
    ("open access", r"open access|APC|article publishing charge|hybrid|subscription"),
    ("abstract", r"abstract[^.]{0,200}"),
    ("highlights", r"highlights[^.]{0,260}"),
    ("keywords", r"keywords?[^.]{0,200}"),
    ("title page", r"title page[^.]{0,200}"),
    ("declaration", r"declaration of (competing )?interest[^.]{0,200}"),
    ("AI", r"generative AI[^.]{0,260}"),
    ("data", r"research data[^.]{0,240}"),
    ("reference", r"reference style[^.]{0,240}"),
    ("length", r"(page|word) limit[^.]{0,200}"),
]


def main() -> int:
    apply = "--apply" in sys.argv
    if not PDF.exists():
        print(f"  ❌ 找不到 PDF: {PDF}")
        return 1
    r = subprocess.run(["pdftotext", "-layout", str(PDF), "-"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    txt = r.stdout or ""
    print(f"=== 提取：{len(txt)} 字符 ｜ {len(txt.splitlines())} 行 ===")
    if apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="\n").write(txt)
        print(f"  ✅ 已存 {OUT.relative_to(REPO)}")

    for tag, pat in KEYS:
        print(f"\n── {tag} ──")
        hits = list(re.finditer(pat, txt, re.I))
        if not hits:
            print("   （Guide 未提及）")
            continue
        seen = set()
        for m in hits[:3]:
            s = " ".join(txt[max(0, m.start() - 160):m.start() + 300].split())
            if s[:80] in seen:
                continue
            seen.add(s[:80])
            print(f"   • {s[:330]}")

    # 明示找 APC 金额与 hybrid 判定
    print("\n── APC / hybrid 原文 ──")
    for m in re.finditer(r"[^.]{0,200}(APC|article publishing charge|USD|open access journal)[^.]{0,240}\.", txt, re.I):
        s = " ".join(m.group(0).split())
        if any(k in s.lower() for k in ("usd", "apc", "charge", "hybrid", "subscription")):
            print(f"   • {s[:330]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
