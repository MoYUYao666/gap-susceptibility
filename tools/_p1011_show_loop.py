# -*- coding: utf-8 -*-
r"""Show the structure of the sweep's run loop, so the guard can be placed exactly.

    python tools/_p1011_show_loop.py
"""
from __future__ import annotations

import io
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
lines = (REPO / "tools" / "_p820_llava_sites.py").read_text(encoding="utf-8").splitlines()
start = next(i for i, l in enumerate(lines) if "Release the previous arm" in l)
print(f"  release step at line {start + 1}")
for i in range(max(0, start - 6), min(len(lines), start + 200)):
    l = lines[i]
    s = l.strip()
    if s.startswith(("for seed", "for arm", "print(f\"  wrote", "# ----", "results[", "if a.apply")) \
            or "for ep in range" in s or s.startswith("mm = build"):
        print(f"{i + 1:>5} |{l[:100]}")
