# -*- coding: utf-8 -*-
r"""核 A1 的关键词、highlights、引用样式与文档类（Neural Networks 合规）（2026-10-10）。

    python tools\_p102_a1_compliance_probe.py
"""
from __future__ import annotations

import io
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
M = REPO / "paper_a1" / "main.tex"
H = REPO / "paper_a1" / "highlights.tex"


def main() -> int:
    t = io.open(M, encoding="utf-8", errors="replace").read()

    print("=== ① 文档类 ===")
    for m in re.finditer(r"\\documentclass(\[[^\]]*\])?\{([^}]*)\}", t):
        print(f"  \\documentclass{m.group(1) or ''}{{{m.group(2)}}}")

    print("\n=== ② 引用相关宏包 ===")
    for m in re.finditer(r"\\usepackage(\[[^\]]*\])?\{([^}]*)\}", t):
        if any(k in m.group(2) for k in ("natbib", "cite", "biblatex", "hyperref")):
            print(f"  \\usepackage{m.group(1) or ''}{{{m.group(2)}}}")

    print("\n=== ③ 关键词 ===")
    m = (re.search(r"\\keywords\{(.*?)\}", t, re.S)
         or re.search(r"\\begin\{keyword\*?\}(.*?)\\end\{keyword\*?\}", t, re.S)
         or re.search(r"\\begin\{highlights\}(.*?)\\end\{highlights\}", t, re.S))
    if m:
        print("  ", " ".join(m.group(1).split())[:400])
    else:
        print("  ❌ 未找到关键词环境/命令")

    print("\n=== ④ 引用命令的使用（判样式）===")
    for cmd in ("\\cite{", "\\citep{", "\\citet{", "\\upcite{", "\\bibitem"):
        n = t.count(cmd)
        if n:
            print(f"  {cmd:<12} {n} 次")
    print(f"  thebibliography 环境: {'有' if 'thebibliography' in t else '无'}")
    print(f"  \\bibliography{{: {'有' if '\\bibliography{' in t else '无'}")

    print("\n=== ⑤ highlights ===")
    if H.exists():
        h = io.open(H, encoding="utf-8", errors="replace").read()
        items = re.findall(r"\\item\s+(.+)", h)
        print(f"  条目数: {len(items)}（要求 3–5）")
        for it in items:
            s = " ".join(it.split())
            print(f"   • [{len(s)} 字符] {s[:100]}")
        over = [len(" ".join(i.split())) for i in items if len(" ".join(i.split())) > 85]
        print(f"  超 85 字符的条目: {len(over)} 个 {'❌' if over else '✅'}")
    else:
        print("  ❌ 缺 highlights.tex")

    print("\n=== ⑥ 摘要词数（复核）===")
    m = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", t, re.S)
    if m:
        b = re.sub(r"\\[a-zA-Z]+", " ", m.group(1))
        b = re.sub(r"[{}$\\]", " ", b)
        print(f"  {len(b.split())} 词（限 250）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
