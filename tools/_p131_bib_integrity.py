# -*- coding: utf-8 -*-
r"""核查 A1 书目完整性（57 碎片 vs 56 条）（2026-10-10）。

    python tools\_p131_bib_integrity.py
"""
from __future__ import annotations

import io
import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MAIN = REPO / "paper_a1" / "main.tex"
FIXED = REPO / "outputs" / "analysis" / "a1_apa_fixed.json"


def main() -> int:
    t = io.open(MAIN, encoding="utf-8", errors="replace").read()
    i = t.find("\\begin{thebibliography}")
    j = t.find("\\end{thebibliography}")
    print(f"书目块位置: {i} → {j}")
    block = t[i:j] if (i > 0 and j > i) else ""
    print(f"块字符数: {len(block)}")

    m0 = re.search(r"\\begin\{thebibliography\}\{[^}]*\}", block)
    body = block[m0.end():] if m0 else ""
    parts = [p for p in re.split(r"(?=\\bibitem)", body) if p.strip()]
    print(f"碎片数: {len(parts)}")

    print("\n=== 逐个碎片的首行 ===")
    for n, p in enumerate(parts):
        lab = re.search(r"\\bibitem\[([^\]]*)\]\{([^}]*)\}", p)
        if lab:
            print(f"  {n:>2} [{lab.group(1):<22}] {lab.group(2)}")
        else:
            print(f"  {n:>2} ⚠ **无 label** → {repr(p[:220])}")

    n_lab = len(re.findall(r"\\bibitem\[[^\]]*\]\{[^}]*\}", block))
    n_nolab = len(re.findall(r"\\bibitem\{", block))
    print(f"\n有 label: {n_lab} ｜ 无 label: {n_nolab}")

    # 与 JSON 对照
    want = {r["key"] for r in json.loads(io.open(FIXED, encoding="utf-8").read())}
    got = set(re.findall(r"\\bibitem\[[^\]]*\]\{([^}]*)\}", block))
    print(f"应有 key: {len(want)} ｜ 实有 key: {len(got)}")
    print(f"  缺: {sorted(want - got)}")
    print(f"  多: {sorted(got - want)}")

    # 正文引用的 key 是否都在
    cited = set()
    for f in (REPO / "paper_a1" / "main.tex", REPO / "paper_a1" / "related_work.tex"):
        if f.exists():
            s = io.open(f, encoding="utf-8", errors="replace").read()
            for m in re.finditer(r"\\cite[tp]?\{([^}]*)\}", s):
                cited |= {k.strip() for k in m.group(1).split(",") if k.strip()}
    print(f"\n正文引用 key: {len(cited)}")
    print(f"  未定义: {sorted(cited - got)}")
    print(f"  定义未引用: {sorted(got - cited)[:10]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
