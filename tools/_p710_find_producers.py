# -*- coding: utf-8 -*-
r"""Find the scripts that produced the seven unsourced Paper A numbers.

Method: the numbers were emitted by some analysis script, and that script names its output file.
So search the tool scripts for the value AND for the output path they write, then read the script
to see whether it recomputes the number from tracked archives.

    python tools/_p710_find_producers.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

TARGETS = {
    "0.943": "OpenCLIP BitFit mean R2",
    "0.29": "CR1 standard error of the slope",
    "222": "fits archived",
    "203": "fits with negative alpha",
    "117": "mechanism experiments",
    "95": "strict-freezing controls",
    "221": "runs in the experiment catalogue",
    "383": "experiments in the validation part",
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    scripts = [p for p in (REPO / "tools").rglob("*.py")
               if "_removed_from_publish" not in str(p)]
    print(f"  searching {len(scripts)} tool scripts")
    print()
    for val, desc in TARGETS.items():
        print("=" * 110)
        print(f"{val}   ({desc})")
        print("=" * 110)
        hits = []
        for p in scripts:
            try:
                t = p.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            if val not in t:
                continue
            # is it an assertion, a print, or a write?
            lines = [l.strip() for l in t.splitlines() if val in l]
            hits.append((p.name, lines[:3]))
        if not hits:
            print("  no script mentions this value literally")
        for name, lines in hits[:6]:
            print(f"  {name}")
            for l in lines:
                print(f"      {l[:130]}")
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
