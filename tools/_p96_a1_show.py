# -*- coding: utf-8 -*-
r"""显示 A1 改后的标题与摘要首段（并编译验证）（2026-10-10）。

    python tools\_p96_a1_show.py
"""
from __future__ import annotations

import io
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "paper_a1" / "main.tex"


def main() -> int:
    t = io.open(F, encoding="utf-8", errors="replace").read()
    m = re.search(r"\\title\{(.+?)\}\s*\n\\", t, re.S)
    print("=== 标题 ===")
    print(" ", " ".join(m.group(1).split()) if m else "(未找到)")

    m2 = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", t, re.S)
    print("\n=== 摘要首段（新写的两句）===")
    if m2:
        body = m2.group(1)
        plain = " ".join(re.sub(r"\\[a-zA-Z]+\{[^}]*\}", " ", body).split())
        # 打印到第一个 "The modality gap" 之后 200 字符
        k = plain.find("The modality gap")
        print(" ", plain[:k + 220] if k > 0 else plain[:700])
        print(f"\n  （摘要共 {len(body.split())} 词）")
    else:
        print("  (未找到 abstract)")

    print("\n=== 关键保留声明是否仍在 ===")
    for s in ("necessary, not sufficient", "self-consistency check",
              "we claim this for no other families", "not independent validation"):
        print(f"  {'✅' if s in t else '❌'} {s}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
