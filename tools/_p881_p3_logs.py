# -*- coding: utf-8 -*-
r"""Read the P3 build logs, and locate the labels the main text refers to.

Two questions:

1. Do the two compiled documents resolve every `\ref` and `\cite`? They are separate PDFs, so a
   reference into the other document cannot resolve and would print as `??`.
2. Where are `tab:gamma_detail` and `tab:gamma_rank` defined? The cross-check shows the main text refers
   to them and the supplement does not define them, so either they are tables in the main text (fine)
   or the main text prints `??`.

    python tools/_p881_p3_logs.py
"""
from __future__ import annotations

import io
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
P3 = REPO / "paper3" / "paper_ieee"
LOGS = [P3 / "main.log", P3 / "supplementary" / "supplementary.log",
        P3 / "main_full.log", P3 / "cover_letter_prl.log"]
SRC = [P3 / "main.tex", P3 / "main_full.tex", P3 / "main_10pp.tex",
       P3 / "supplementary" / "supplementary.tex"] + \
      [p for p in (P3 / "sections").glob("*.tex") if ".bak" not in p.name]

for log in LOGS:
    if not log.exists():
        print(f"=== {log.name}: MISSING")
        continue
    t = log.read_text(encoding="utf-8", errors="replace")
    undef = re.findall(r"Reference `([^']+)' on page", t) + \
            re.findall(r"reference `([^']+)' on page", t)
    cites = re.findall(r"Citation `([^']+)' (?:on page [\d]+ )?undefined", t)
    errs = re.findall(r"^!.*$", t, re.M)
    print(f"=== {log.name}")
    print(f"  undefined references: {len(undef)} {sorted(set(undef))}")
    print(f"  undefined citations:  {len(cites)} {sorted(set(cites))[:6]}")
    print(f"  errors:               {len(errs)}")
    for e in errs[:3]:
        print(f"    {e[:110]}")
    for w in ("Rerun to get", "Label(s) may have changed", "Float too large", "Overfull \\hbox"):
        print(f"  {w:<28} {len(re.findall(re.escape(w), t))}")

print()
print("=== where are the gamma labels defined? ===")
for p in SRC:
    t = p.read_text(encoding="utf-8", errors="replace")
    for lab in ("tab:gamma_detail", "tab:gamma_rank"):
        for m in re.finditer(re.escape(lab), t):
            ln = t[: m.start()].count("\n") + 1
            print(f"  {lab:<18} {p.relative_to(REPO).as_posix()}:{ln}")

print()
print("=== every label and table in the main text ===")
mt = (P3 / "main.tex").read_text(encoding="utf-8", errors="replace")
for p in (P3 / "sections").glob("*.tex"):
    if ".bak" not in p.name:
        mt += "\n" + p.read_text(encoding="utf-8", errors="replace")
print("  labels:", sorted(m.group(1) for m in re.finditer(r"\\label\{([^}]*)\}", mt)))
print("  tables:", [m.group(0)[:60] for m in re.finditer(r"\\begin\{table\*?\}", mt)])
print("  figures:", [m.group(0)[:60] for m in re.finditer(r"\\begin\{figure\*?\}", mt)])
