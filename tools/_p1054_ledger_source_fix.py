# -*- coding: utf-8 -*-
r"""Give the three LLaVA parameter claims their `source` argument.

The ledger's `claim(name, manuscript, computed, source, tol)` requires the source, and three of the new
entries omitted it, so the ledger aborted with `TypeError: claim() missing 1 required positional argument`.
The source names the archived field, as it does for every other entry.

    python tools/_p1054_ledger_source_fix.py [--apply]
"""
from __future__ import annotations

import argparse
import ast
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
LEDGER = REPO / "tools" / "_claim_ledger.py"

PAIRS = [
    ('        claim("LLaVA text_only 可训练参数", 19988480.0,\n'
     '              float(_iso.get("text_only", {}).get("n_trainable", -1)), tol=0.5)\n',
     '        claim("LLaVA text_only 可训练参数", 19988480.0,\n'
     '              float(_iso.get("text_only", {}).get("n_trainable", -1)),\n'
     '              "llava_sites.json:isolation_verified.text_only.n_trainable", tol=0.5)\n'),
    ('        claim("LLaVA vision_only 可训练参数", 3645440.0,\n'
     '              float(_iso.get("vision_only", {}).get("n_trainable", -1)), tol=0.5)\n',
     '        claim("LLaVA vision_only 可训练参数", 3645440.0,\n'
     '              float(_iso.get("vision_only", {}).get("n_trainable", -1)),\n'
     '              "llava_sites.json:isolation_verified.vision_only.n_trainable", tol=0.5)\n'),
    ('        claim("LLaVA both 可训练参数", 23633920.0,\n'
     '              float(_iso.get("both", {}).get("n_trainable", -1)), tol=0.5)\n',
     '        claim("LLaVA both 可训练参数", 23633920.0,\n'
     '              float(_iso.get("both", {}).get("n_trainable", -1)),\n'
     '              "llava_sites.json:isolation_verified.both.n_trainable", tol=0.5)\n'),
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = LEDGER.read_text(encoding="utf-8")
    if "isolation_verified.text_only.n_trainable" in t:
        print("  already fixed")
        return 0
    for old, new in PAIRS:
        assert t.count(old) == 1, f"expected one occurrence:\n{old}"
        t = t.replace(old, new, 1)
    ast.parse(t)
    print("  source argument added to all three parameter claims")
    if not a.apply:
        print("  (dry run)")
        return 0
    LEDGER.write_text(t, encoding="utf-8", newline="")
    print("  written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
