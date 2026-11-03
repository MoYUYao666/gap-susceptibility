# -*- coding: utf-8 -*-
r"""Report the LaTeX errors and unresolved references in the P3 build logs.

    python tools/_p892_p3_build_check.py
"""
from __future__ import annotations

import io
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
LOGS = REPO / "outputs" / "analysis"
FILES = ["_p3_main3.log", "_p3_supp2.log", "_p3_supp1.log"]

for name in FILES:
    p = LOGS / name
    if not p.exists():
        print(f"=== {name}: MISSING")
        continue
    t = p.read_text(encoding="utf-8", errors="replace")
    errs = re.findall(r"^!.*$", t, re.M)
    undef_ref = sorted(set(re.findall(r"Reference `([^']+)' on page", t)))
    undef_cite = sorted(set(re.findall(r"Citation `([^']+)'", t)))
    print(f"=== {name}")
    print(f"  errors:            {len(errs)}")
    for e in errs[:8]:
        print(f"    {e[:118]}")
    print(f"  undefined refs:    {len(undef_ref)} {undef_ref[:8]}")
    print(f"  undefined cites:   {len(undef_cite)} {undef_cite[:8]}")
    print(f"  rerun requested:   {'Rerun' in t}")
    print(f"  overfull hbox:     {t.count('Overfull ' + chr(92) + 'hbox')}")
    # the first error with its input line, which is what identifies the offending source line
    m = re.search(r"^!.*?\n(?:.*\n){0,6}?l\.(\d+)([^\n]*)", t, re.M)
    if m:
        print(f"  first error at input line {m.group(1)}: {m.group(2)[:110]}")
