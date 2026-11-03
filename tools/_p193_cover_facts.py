# -*- coding: utf-8 -*-
r"""核对 cover letter 里的每个数字/主张与当前稿子（2026-10-11）。

    python tools\_p193_cover_facts.py
"""
from __future__ import annotations

import glob
import io
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "paper合"


def main() -> int:
    t = io.open(SRC / "main_nc.tex", encoding="utf-8", errors="replace").read()
    secs = "".join(io.open(f, encoding="utf-8", errors="replace").read()
                   for f in sorted((SRC / "sections").glob("*.tex")))
    allt = t + secs

    print("=== ① cover letter 里说 49 页 → 当前 ===")
    print("  实测 56 页（Manuscript.pdf）")

    print("\n=== ② 摘要词数（cover 说 238）===")
    m = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", t, re.S)
    if m:
        b = re.sub(r"\\[a-zA-Z]+", " ", m.group(1))
        print(f"  标准口径: {len(re.sub(r'[{}$\\\\]', ' ', b).split())} 词")

    print("\n=== ③ 关键词（cover 说 six）===")
    m = re.search(r"\\begin\{keyword\}(.*?)\\end\{keyword\}", t, re.S)
    if m:
        n = m.group(1).count(r"\sep") + 1
        print(f"  实测 {n} 个")

    print("\n=== ④ R² 值（cover 说 ODE 0.986 / baseline 0.00 / linear 0.946）===")
    for pat in (r"R\^2[^.]{0,120}", r"0\.98\d", r"0\.94\d"):
        for mm in list(re.finditer(pat, allt))[:3]:
            s = " ".join(allt[max(0, mm.start() - 150):mm.start() + 190].split())
            print("   • " + s[:300])

    print("\n=== ⑤ 实验计数（cover 说 n=204 / 383）===")
    for pat in (r"n\s*=\s*204", r"\b204\b", r"\b383\b", r"\b117\b", r"\b95\b"):
        hits = len(re.findall(pat, allt))
        print(f"  `{pat}`: {hits} 次")

    print("\n=== ⑥ patch size（cover 说 'seven configurations track patch size'）===")
    for mm in list(re.finditer(r"patch size", allt))[:4]:
        s = " ".join(allt[max(0, mm.start() - 300):mm.start() + 300].split())
        print("   • " + s[:360]); print()

    print("=== ⑦ 严格冻结配置数（cover 说 seven）===")
    for mm in list(re.finditer(r"seven (strict|backbone|configuration)", allt, re.I))[:4]:
        s = " ".join(allt[max(0, mm.start() - 150):mm.start() + 200].split())
        print("   • " + s[:320])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
