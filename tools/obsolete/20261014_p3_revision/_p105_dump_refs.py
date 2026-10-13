# -*- coding: utf-8 -*-
r"""取 A1 全部 13 条参考文献的完整原文（供 APA 转换）（2026-10-10）。

    python tools\_p105_dump_refs.py [--apply]
"""
from __future__ import annotations

import io
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
M = REPO / "paper_a1" / "main.tex"
OUT = REPO / "outputs" / "analysis" / "a1_refs_original.json"


def main() -> int:
    apply = "--apply" in sys.argv
    t = io.open(M, encoding="utf-8", errors="replace").read()
    i = t.find("\\begin{thebibliography}")
    j = t.find("\\end{thebibliography}")
    print(f"  书目块: {i} → {j}（{j - i} 字符）")
    block = t[i:j]
    items = re.findall(r"\\bibitem(?:\[[^\]]*\])?\{([^}]*)\}\s*(.*?)(?=\\bibitem|$)",
                       block, re.S)
    print(f"  共 {len(items)} 条\n")
    rows = []
    for k, b in items:
        body = " ".join(b.split())
        print(f"── [{k}]")
        print(f"   {body}\n")
        rows.append({"key": k, "body": body})

    # 关键词与摘要位置（供后续改文档类）
    print("=== 其他需改的位置 ===")
    for pat, tag in ((r"\\documentclass(\[[^\]]*\])?\{[^}]*\}", "documentclass"),
                     (r"\\usepackage(\[[^\]]*\])?\{natbib\}", "natbib"),
                     (r"\\begin\{abstract\}", "abstract 起点")):
        m = re.search(pat, t)
        print(f"  {tag:<14} {'✅ ' + m.group(0) if m else '❌ 未找到'}")

    if apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps(rows, ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
