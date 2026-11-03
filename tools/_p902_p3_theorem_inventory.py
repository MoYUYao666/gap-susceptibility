# -*- coding: utf-8 -*-
r"""List P3's theorem-like environments in document order, and how the supplement refers to them.

Needed before changing any numbering: the supplement cites "Theorem 1", "Lemma 1" and "Corollary 5"
by hand, so renumbering the main text has to be reflected there or the two documents drift apart again.

    python tools/_p902_p3_theorem_inventory.py
"""
from __future__ import annotations

import io
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
P3 = REPO / "paper3" / "paper_ieee"
ENVS = ("theorem", "lemma", "corollary", "definition", "remark", "proposition")
BEGIN = re.compile(r"\\begin\{(" + "|".join(ENVS) + r")\}(\[[^\]]*\])?")

print("=== theorem-like environments in the main text, in order ===")
order = []
main_files = [P3 / "main.tex"] + sorted(p for p in (P3 / "sections").glob("*.tex") if ".bak" not in p.name)
for p in main_files:
    t = p.read_text(encoding="utf-8", errors="replace")
    for m in BEGIN.finditer(t):
        ln = t[: m.start()].count("\n") + 1
        opt = m.group(2) or ""
        lab = re.search(r"\\label\{([^}]*)\}", t[m.end(): m.end() + 400])
        order.append((p.name, ln, m.group(1), opt, lab.group(1) if lab else ""))
print(f"  {len(order)} environments")
counts: dict[str, int] = {}
for name, ln, env, opt, lab in order:
    counts[env] = counts.get(env, 0) + 1
    print(f"  {name}:{ln:<4} {env:<11} {opt:<34} n={counts[env]}  label={lab}")
print(f"  counts: {counts}")

print()
print("=== how the supplementary material refers to them ===")
sup = (P3 / "supplementary" / "supplementary.tex").read_text(encoding="utf-8", errors="replace")
for pat in (r"Theorem~?\s*[0-9IVX]+[0-9.]*", r"Lemma~?\s*[0-9IVX]+[0-9.]*",
            r"Corollary~?\s*[0-9IVX]+[0-9.]*", r"Definition~?\s*[0-9IVX]+[0-9.]*"):
    for m in re.finditer(pat, sup):
        ln = sup[: m.start()].count("\n") + 1
        print(f"  supplement.tex:{ln}: {m.group(0)}")

print()
print("=== the same in the three main-text variants ===")
for f in ("main.tex", "main_full.tex", "main_10pp.tex"):
    t = (P3 / f).read_text(encoding="utf-8", errors="replace")
    print(f"  {f}: "
          f"newtheorem x{len(re.findall(re.escape(chr(92)) + 'newtheorem', t))}, "
          f"hidelinks={'hidelinks' in t}, hypersetup={'hypersetup' in t}, "
          f"parindent={'parindent' in t}")
