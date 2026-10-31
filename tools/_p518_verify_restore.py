# -*- coding: utf-8 -*-
r"""核验 `experiments.tex` 恢复是否干净 + 补充材料是否含残留误加段（2026-10-13）。

    python tools\_p518_verify_restore.py
"""
from __future__ import annotations

import io
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PI = REPO / "paper3" / "paper_ieee"
EX = PI / "sections" / "experiments.tex"
SUP = PI / "supplementary" / "supplementary.tex"


def main() -> int:
    ex = io.open(EX, encoding="utf-8", errors="replace").read()
    sup = io.open(SUP, encoding="utf-8", errors="replace").read()
    print("=" * 96)
    print("① experiments.tex 环境配平")
    print("=" * 96)
    ok = True
    for name in ("table", "table*", "figure", "figure*", "tabular", "itemize"):
        nb = len(re.findall(r"\\begin\{" + re.escape(name) + r"\}", ex))
        ne = len(re.findall(r"\\end\{" + re.escape(name) + r"\}", ex))
        good = nb == ne
        ok = ok and good
        print(f"  {'✅' if good else '🔴'} {name:<9} begin {nb} ｜ end {ne}")

    print()
    print("=" * 96)
    print("② 4 个 label 是否都在（应为「在」——已放弃移表）")
    print("=" * 96)
    for lab in ("tab:sample", "tab:phase", "fig:phase_transition", "fig:counterfactual"):
        has_lab = f"\\label{{{lab}}}" in ex
        has_ref = f"\\ref{{{lab}}}" in ex
        print(f"  {'✅' if has_lab and has_ref else '⚠️'} {lab:<26} label {has_lab} ｜ ref {has_ref}")

    print()
    print("=" * 96)
    print("③ 补充材料是否含残留的误加段")
    print("=" * 96)
    for pat in ("\\section{Tables and Figures}", "\\section{Deferred Experimental Detail}"):
        n = sup.count(pat)
        print(f"  {pat:<42} 出现 {n} 次")
    print(f"  supplementary = {len(sup):,} 字符")
    print(f"  experiments   = {len(ex):,} 字符")

    print()
    print("=" * 96)
    print("④ 断头命令 / 字面 \\n")
    print("=" * 96)
    for f, t in (("experiments", ex), ("supplementary", sup)):
        sev = [t[:m.start()].count("\n") + 1
               for m in re.finditer(r"(?m)^(abla|oindent|eq|ot|onumber|eg)\b", t)]
        lit = len(re.findall(r"\\n(?![A-Za-z])", t))
        print(f"  {f:<15} 断头 {len(sev)} 处 {sev[:5]} ｜ 字面 \\n {lit}")
        ok = ok and not sev and lit == 0
    print()
    print(f"  **判定：{'✅ 全部干净' if ok else '🔴 有问题'}**")
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
