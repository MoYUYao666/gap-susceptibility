# -*- coding: utf-8 -*-
r"""Trace the cross-document references between the main text and the supplementary.

The main text appears to reference tab:gamma_detail and tab:gamma_rank, which are defined in
supplementary.tex. That matters twice over: it decides whether the two documents can be
compiled independently, and a "[?]" in the submitted PDF would be visible to the reviewer.

    python tools/_p664_trace_xrefs.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
P = REPO / "paper3" / "paper_ieee"
LABELS = ["tab:gamma_detail", "tab:gamma_rank"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    files = [P / "main.tex"] + sorted((P / "sections").glob("*.tex"))
    supp = P / "supplementary" / "supplementary.tex"

    print("=" * 96)
    print("1. where the main text refers to them")
    print("=" * 96)
    for p in files:
        t = io.open(p, encoding="utf-8", errors="replace").read()
        for lab in LABELS:
            for m in re.finditer(re.escape(lab), t):
                ln = t[:m.start()].count("\n") + 1
                seg = " ".join(t[max(0, m.start() - 180):m.start() + 120].split())
                print(f"  {p.name}:{ln}  [{lab}]")
                print(f"     ...{seg[:300]}...")

    print()
    print("=" * 96)
    print("2. where the labels are defined")
    print("=" * 96)
    for p in files + [supp]:
        t = io.open(p, encoding="utf-8", errors="replace").read()
        for lab in LABELS:
            if ("\\label{%s}" % lab) in t:
                print(f"  {p.name} defines {lab}")

    print()
    print("=" * 96)
    print("3. does the compiled main.pdf show a broken reference?")
    print("=" * 96)
    log = P / "main.log"
    if log.exists():
        t = io.open(log, encoding="utf-8", errors="replace").read()
        undef = re.findall(r"Reference `([^']+)' on page (\d+) undefined", t)
        print(f"  undefined references in main.log: {len(undef)}")
        for name, page in undef[:12]:
            print(f"     {name}  (page {page})")
        print(f"  'There were undefined references' present: "
              f"{'There were undefined references' in t}")
    else:
        print("  main.log not found")

    print()
    print("=" * 96)
    print("4. what the reader sees in the PDF")
    print("=" * 96)
    import subprocess
    r = subprocess.run(["pdftotext", "-q", "-layout", str(P / "main.pdf"), "-"],
                       capture_output=True)
    t = r.stdout.decode("utf-8", errors="replace")
    qs = [(m.start(), t[max(0, m.start() - 60):m.start() + 30]) for m in re.finditer(r"\?\?", t)]
    print(f"  '??' occurrences in main.pdf text: {len(qs)}")
    for pos, seg in qs[:8]:
        print(f"     ...{' '.join(seg.split())[:110]}...")
    r = subprocess.run(["pdftotext", "-q", "-layout",
                        str(P / "supplementary" / "supplementary.pdf"), "-"],
                       capture_output=True)
    s = r.stdout.decode("utf-8", errors="replace")
    print(f"  '??' occurrences in supplementary.pdf text: {len(re.findall(r'\\?\\?', s))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
