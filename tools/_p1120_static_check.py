# -*- coding: utf-8 -*-
r"""Static checks of the sweep after the canonical-metric switch, before any expensive run.

None of `before[...]` / `after[...]` may still index a tuple, `measure()` must return the dict, the record must
carry both definitions, and the checkpoint filter must be the name-based one. A five-second AST/inspection pass
is much cheaper than discovering a KeyError forty minutes into a twelve-run retrain.

    python tools/_p1120_static_check.py
"""
from __future__ import annotations

import io
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SWEEP = REPO / "tools" / "_p820_llava_sites.py"


def main() -> int:
    t = io.open(SWEEP, encoding="utf-8").read()
    ok = True

    leftovers = re.findall(r"(?:before|after)\[\d\]", t)
    print(f"  tuple indexing on before/after: {leftovers if leftovers else 'none'}")
    ok &= not leftovers

    checks = {
        "measure returns the canonical dict": '"dg_star": mean(dg_stars)' in t,
        "record has dg_star_before": '"dg_star_before"' in t,
        "record has dg_star_after": '"dg_star_after"' in t,
        "record has dg_empirical": '"dg_empirical_after"' in t,
        "legacy keys preserved": '"dg_before": before["legacy_dg"]' in t,
        "canonical gap formula": "((A - B) ** 2).sum(dim=-1).mean()" in t,
        "last hidden state used": "out.hidden_states[-1]" in t,
        "text side excludes image tokens": "inp[\"attention_mask\"].bool() & ~vm" in t,
        "checkpoint filter by name": "_trainable_names" in t,
        "no identity filter left": "any(t is v for t in" not in t,
        "full forward (no manual vision tower)": "vision(pv.to(torch.bfloat16)" not in t,
    }
    for label, val in checks.items():
        print(f"  {'PASS' if val else 'FAIL'}  {label}")
        ok &= val

    # the eval slicing: `before` must also be a dict now
    m = re.search(r"before = measure\([^\n]*", t)
    print(f"  before-measure call: {m.group(0) if m else 'NOT FOUND'}")

    print("\n  RESULT:", "READY (static)" if ok else "NOT READY")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
