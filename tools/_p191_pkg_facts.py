# -*- coding: utf-8 -*-
r"""取投稿包 README 需要的当前实测值（2026-10-11）。

    python tools\_p191_pkg_facts.py
"""
from __future__ import annotations

import io
import re
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
LS = REPO / "paper合" / "NC_submission" / "latex_source"
PDF = LS / "main_nc.pdf"


def main() -> int:
    t = io.open(LS / "main_nc.tex", encoding="utf-8", errors="replace").read()
    secs = "".join(io.open(f, encoding="utf-8", errors="replace").read()
                   for f in sorted((LS / "sections").glob("*.tex")))

    print("=== ① 摘要词数（从 tex，三种口径）===")
    m = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", t, re.S)
    if m:
        b = m.group(1)
        for tag, pat in (("字面", r"\\[a-zA-Z]+\{[^}]*\}"),):
            x = len(re.sub(pat, " ", b).split())
            print(f"  {tag}: {x}")
        x2 = re.sub(r"\\[a-zA-Z]+", " ", b)
        x2 = len(re.sub(r"[{}$\\]", " ", x2).split())
        print(f"  标准（删命令）: {x2}")
        x3 = re.sub(r"\$[^$]*\$", " MATH ", b)
        x3 = re.sub(r"\\[a-zA-Z]+", " ", x3)
        x3 = len(re.sub(r"[{}\\$]", " ", x3).split())
        print(f"  最严（数学算 1 词）: {x3}")

    print("\n=== ② 参考文献条数 ===")
    n_bib = len(re.findall(r"\\bibitem", secs))
    print(f"  \\bibitem 共 {n_bib} 条")
    if (LS / "references.bib").exists():
        nb = io.open(LS / "references.bib", encoding="utf-8",
                     errors="replace").read()
        print(f"  references.bib 里 @ 条目: {len(re.findall(r'^@', nb, re.M))} 条")

    print("\n=== ③ Highlights ===")
    hf = REPO / "paper合" / "NC_submission" / "Highlights.txt"
    if hf.exists():
        lines = [l.strip() for l in io.open(hf, encoding="utf-8",
                                            errors="replace").read().splitlines()
                 if l.strip()]
        print(f"  {len(lines)} 行")
        for l in lines:
            print(f"    [{len(l):>3} 字符] {l[:90]}")

    print("\n=== ④ PDF 页数 ===")
    if PDF.exists():
        o = subprocess.run(["pdfinfo", str(PDF)], capture_output=True,
                           encoding="utf-8", errors="replace").stdout or ""
        m2 = re.search(r"Pages:\s+(\d+)", o)
        print(f"  Manuscript.pdf: {m2.group(1) if m2 else '?'} 页")

    print("\n=== ⑤ 标题 ===")
    mt = re.search(r"\\title\{(.*?)\}\s*\n", t, re.S)
    if mt:
        print("  " + " ".join(mt.group(1).split()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
