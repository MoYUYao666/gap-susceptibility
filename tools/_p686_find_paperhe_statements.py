# -*- coding: utf-8 -*-
r"""Locate both Data availability statements in the Paper A sources.

The compiled manuscript carries two different statements: a one-liner on page 43
("Data will be made available on request") and a longer passage on page 59 that says the
repository "is currently private and will be made public upon publication" and that "no new
data were generated that requires deposit in an external repository". Neither matches reality:
the repository is public and has a Zenodo DOI.

The one-liner is in sections/conclusion.tex. This finds the source of the longer passage.

    python tools/_p686_find_paperhe_statements.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PA = REPO / "paper合"
OUT = REPO / "outputs" / "analysis" / "paperhe_statements.json"

PROBES = [
    "currently private",
    "will be made public upon publication",
    "No new data were generated",
    "available to the reviewers on request",
    "Data will be made available on request",
    "data availability",
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    hits: dict[str, dict[str, int]] = {}
    for p in sorted(PA.rglob("*.tex")):
        try:
            t = io.open(p, encoding="utf-8", errors="replace").read()
        except Exception:
            continue
        for probe in PROBES:
            n = len(re.findall(re.escape(probe), t, re.I))
            if n:
                hits.setdefault(p.relative_to(PA).as_posix(), {})[probe] = n

    print("=" * 104)
    print("which source files contain which statement")
    print("=" * 104)
    for f, d in sorted(hits.items()):
        print(f"  {f}")
        for k, v in d.items():
            print(f"      {v}x  {k}")

    print()
    print("=" * 104)
    print("main_nc.tex: which files it inputs, and where the statements would be")
    print("=" * 104)
    main = io.open(PA / "main_nc.tex", encoding="utf-8", errors="replace").read()
    for m in re.finditer(r"\\input\{([^}]+)\}", main):
        f = m.group(1)
        exists = (PA / (f + ".tex")).exists()
        print(f"  \\input{{{f}}}  ->  {f}.tex exists={exists}")
    print()
    print("  tail of main_nc.tex (where declarations usually live):")
    tail = " ".join(main.split())[-900:]
    print("    " + tail)

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps(hits, ensure_ascii=False, indent=1))
        print()
        print(f"  wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
