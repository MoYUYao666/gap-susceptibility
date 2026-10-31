# -*- coding: utf-8 -*-
r"""量化 `experiments.tex` 每段的字符数与可压缩空间（2026-10-13）。

    python tools\_p507_measure_experiments.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
EX = REPO / "paper3" / "paper_ieee" / "sections" / "experiments.tex"
OUT = REPO / "outputs" / "analysis" / "p3_experiments_measure.json"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(EX, encoding="utf-8", errors="replace").read()
    lines = t.split("\n")

    # 定位所有 subsection
    subs = []
    for m in re.finditer(r"\\subsection\{", t):
        ln = t[:m.start()].count("\n")
        d, i = 0, m.end() - 1
        while i < len(t):
            if t[i] == "{":
                d += 1
            elif t[i] == "}":
                d -= 1
                if d == 0:
                    break
            i += 1
        subs.append((ln, t[m.end():i]))
    print("=" * 100)
    print("按 subsection 分段")
    print("=" * 100)
    rep = {}
    tot = 0
    print(f"  {'段':<40} {'字符':>7} {'粗估页':>7} {'%':>6}")
    for k, (ln, title) in enumerate(subs):
        nxt = subs[k + 1][0] if k + 1 < len(subs) else len(lines)
        seg = "\n".join(lines[ln:nxt])
        c = len(seg)
        tot += c
        rep[title] = c
        print(f"  {title[:38]:<40} {c:>7,} {c/8500:>7.2f} {100*c/len(t):>5.1f}%")
    print(f"  {'（section 头之前）':<40} {len(lines[0]) if subs else 0:>7,}")
    print(f"  {'合计':<40} {tot:>7,}")

    # 段内再按 paragraph（\textbf{ 或空行）拆
    print()
    print("=" * 100)
    print("Counterfactual Validation 段内的子块（按 \\textbf 开头）")
    print("=" * 100)
    i = t.find("\\subsection{Counterfactual Validation}")
    j = t.find("\\subsection{Rank Scaling")
    seg = t[i:j]
    blocks = re.split(r"(?=\\textbf\{)", seg)
    for b in blocks:
        head = " ".join(b.split())[:70]
        print(f"  {len(b):>7,} 字符 ｜ {head}")
    rep["_counterfactual_blocks"] = [len(b) for b in blocks]
    rep["_total"] = tot
    rep["_file"] = len(t)

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps(rep, ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
