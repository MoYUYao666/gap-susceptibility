# -*- coding: utf-8 -*-
r"""Read the two scripts that look like the producers, and extract their data sources.

_claim_ledger.py already asserts the OpenCLIP BitFit R2 of 0.943, so the source is in that file.
_docs_synth_pr.py records the "222 fits, 203 negative" attribution. This prints the relevant
sections of both, plus whatever file paths they read, so the Paper A ledger can cite them.

    python tools/_p711_read_producers.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def show(path: Path, patterns, before=3, after=22, label=""):
    print("=" * 112)
    print(f"{label or path.name}")
    print("=" * 112)
    if not path.exists():
        print("  missing")
        return
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    shown = set()
    for pat in patterns:
        for i, l in enumerate(lines):
            if re.search(pat, l, re.I):
                lo, hi = max(0, i - before), min(len(lines), i + after)
                if (lo, hi) in shown:
                    continue
                shown.add((lo, hi))
                print(f"  --- matched /{pat}/ at line {i+1} ---")
                for k in range(lo, hi):
                    print(f"  {k+1:>4} {lines[k][:150]}")
                print()
    # every path-like string in the file
    print("  paths referenced in this file:")
    for l in lines:
        for m in re.finditer(r"[\w./\-]+\.(?:json|txt|md|csv)", l):
            print(f"     {m.group(0)}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    show(REPO / "tools" / "_claim_ledger.py", [r"OpenCLIP BitFit", r"\boc\s*=", r"0\.943"],
         label="_claim_ledger.py  (the OpenCLIP BitFit assertion)")
    show(REPO / "tools" / "_docs_synth_pr.py", [r"222", r"203"], before=6, after=34,
         label="_docs_synth_pr.py  (the 222 / 203 attribution)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
