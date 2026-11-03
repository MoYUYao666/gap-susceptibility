"""Scan the gate chain for references to the three retired directories, bare names included.

The first re-check before the move used a naive substring match and produced a false positive
(`SUBMISSION/_archive/...`). The second one used root-anchored matching **with a trailing slash**, which
missed a real reference: `tools/_final_check_prl.py` builds `REPO / "paper_review" / "refs_all.json"` from
a **bare string literal**, so the moved directory broke that gate with a FileNotFoundError. This script
closes that gap: it matches path *components* (with or without a trailing slash) and prints the context.

Usage:
    python tools/_p1665_scan_dir_refs.py [--bare-only]
"""

from __future__ import annotations

import argparse
import io
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
NAMES = ("_archive", "paper", "paper_review")

# Any of the three names as a whole path component: quoted, or followed by a slash.
PATTERNS = {n: re.compile(r"""["'](?:\.\./)?%s["'/]""" % re.escape(n)) for n in NAMES}


def gate_files() -> list[Path]:
    out = set()
    for pat in ("paper3/paper_ieee/*.py", "tools/paper_audit/**/*.py", "tools/*ledger*.py",
                "tools/_claim*.py", "tools/_p11*.py", "tools/_p14*.py", "tools/_p16*.py",
                "tools/_final*.py", "tools/_p1428_provenance_gate.py",
                "tools/_p1181_verify_paperA_consistency.py", "paper_a2/verify_a23_fix.py"):
        out.update(REPO.glob(pat))
    return sorted(p for p in out if p.is_file())


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bare-only", action="store_true",
                    help="only report references without a trailing slash (the ones a slash-based scan missed)")
    args = ap.parse_args()
    total = 0
    for p in gate_files():
        try:
            text = io.open(p, encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        for name, rx in PATTERNS.items():
            for m in rx.finditer(text):
                lit = m.group(0)
                bare = not lit.endswith("/")
                if args.bare_only and not bare:
                    continue
                total += 1
                line = text.count("\n", 0, m.start()) + 1
                ctx = text[max(0, m.start() - 60):m.start() + 45].replace("\n", " ")
                print("%-46s :%-5d %-18r %s" % (p.relative_to(REPO), line, lit, ctx))
    print("\ntotal references:", total)
    return 0


if __name__ == "__main__":
    sys.exit(main())
