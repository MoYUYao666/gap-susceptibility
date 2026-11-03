# -*- coding: utf-8 -*-
r"""Generate supplementary.bbl so the source package does not depend on bibtex.

main.bbl already exists for the main text, but the supplementary material had no .bbl. If the
publisher compiles it without running bibtex (which is common), the reference list would come
out empty or as [?]. Running bibtex once here removes that dependency.

    python tools/_p662_make_supplementary_bbl.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SUPP = REPO / "paper3" / "paper_ieee" / "supplementary"


def run(cmd, cwd):
    r = subprocess.run(cmd, cwd=str(cwd), capture_output=True)
    return r.returncode, r.stdout.decode("utf-8", errors="replace")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    bbl = SUPP / "supplementary.bbl"
    print(f"  before: supplementary.bbl exists = {bbl.exists()}")
    print(f"  citations in supplementary.tex   = "
          f"{len(set(re.findall(r'\\\\cite[a-z]*\\{([^}]*)\\}', io.open(SUPP / 'supplementary.tex', encoding='utf-8').read())))} distinct \\cite keys")
    if not a.apply:
        print("  (dry run)")
        return 0
    # pdflatex -> bibtex -> pdflatex x2
    rc, _ = run(["pdflatex", "-interaction=nonstopmode", "-halt-on-error",
                 "supplementary.tex"], SUPP)
    print(f"  pdflatex pass 1: rc={rc}")
    rc, out = run(["bibtex", "supplementary"], SUPP)
    print(f"  bibtex: rc={rc}")
    for l in out.splitlines()[:8]:
        if l.strip():
            print(f"     {l.strip()[:110]}")
    for k in range(2):
        rc, out = run(["pdflatex", "-interaction=nonstopmode", "-halt-on-error",
                       "supplementary.tex"], SUPP)
        errs = re.findall(r"^! (.*)$", out, re.M)
        pages = re.findall(r"Output written on supplementary\.pdf \((\d+) pages", out)
        print(f"  pdflatex pass {k+2}: rc={rc}  pages={pages[0] if pages else '?'}  "
              f"errors={len(errs)}")
    print()
    if bbl.exists():
        print(f"  supplementary.bbl created: {bbl.stat().st_size:,} bytes")
        t = io.open(bbl, encoding="utf-8", errors="replace").read()
        print(f"  entries: {t.count(chr(92) + 'bibitem')}")
    else:
        print("  BAD: supplementary.bbl still missing")
        return 1
    # unresolved citations?
    log = SUPP / "supplementary.log"
    if log.exists():
        lt = io.open(log, encoding="utf-8", errors="replace").read()
        print(f"  'undefined' mentions in log: {len(re.findall('undefined', lt, re.I))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
