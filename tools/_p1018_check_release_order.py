# -*- coding: utf-8 -*-
r"""Show the order of the release step and the model build in the sweep.

The cloud log prints "after release: allocated 14.13 GB" and then "device free before this arm: 19.4 GB",
which means a 14 GB model is still resident when the release runs -- so the release is executing after the
build, not before it. This prints the actual order, and whether more than one release block survived the
several patches applied during the session.

    python tools/_p1018_check_release_order.py
"""
from __future__ import annotations

import io
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
lines = (REPO / "tools" / "_p820_llava_sites.py").read_text(encoding="utf-8").splitlines()

marks = []
for i, l in enumerate(lines, 1):
    s = l.strip()
    if ("Release the previous arm" in s or "device free before this arm" in s
            or "after release:" in s or "mm = build(arm)" in s or "del mm" == s
            or s.startswith("del mm")):
        marks.append((i, l))
print(f"  {len(marks)} relevant lines:")
for i, l in marks:
    print(f"  {i:>5} |{l[:104]}")

order_build = next((i for i, l in marks if "mm = build(arm)" in l), None)
order_rel = next((i for i, l in marks if "Release the previous arm" in l), None)
print()
print(f"  release at line {order_rel}, build at line {order_build}")
print("  ORDER IS " + ("CORRECT (release before build)" if order_rel and order_build and order_rel < order_build
                      else "WRONG (build happens first, so the old model is still resident)"))
