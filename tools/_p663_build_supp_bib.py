# -*- coding: utf-8 -*-
r"""Build the supplementary material's bibliography properly and rebuild it.

My earlier attempt failed for a diagnosable reason: supplementary.tex does
\bibliography{references}, and bibtex runs with supplementary/ as the working directory, but
references.bib lives one level up in paper_ieee/. So bibtex reported "I couldn't open database
file references.bib", wrote an empty .bbl, and the following pdflatex run died with
"Something's wrong--perhaps a missing \item" because the empty thebibliography environment has
no \bibitem.

The supplementary does cite six keys, so it does need a real .bbl.

Fix: place a copy of references.bib next to supplementary.tex. This also makes the source
package self-consistent - in the archive, supplementary/ carries the database it names.

    python tools/_p663_build_supp_bib.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PAPER = REPO / "paper3" / "paper_ieee"
SUPP = PAPER / "supplementary"


def run(cmd, cwd):
    r = subprocess.run(cmd, cwd=str(cwd), capture_output=True)
    return r.returncode, r.stdout.decode("utf-8", errors="replace")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    tex = io.open(SUPP / "supplementary.tex", encoding="utf-8").read()
    keys = sorted(set(re.findall(r"\\cite[a-z]*\{([^}]*)\}", tex)))
    print(f"  supplementary cites {len(keys)} distinct key(s) in the source")
    for k in keys:
        print(f"     {k}")
    if not a.apply:
        print("  (dry run)")
        return 0

    # 1. give bibtex the database it asks for
    src_bib = PAPER / "references.bib"
    dst_bib = SUPP / "references.bib"
    shutil.copy2(src_bib, dst_bib)
    print(f"  copied references.bib ({dst_bib.stat().st_size:,} bytes) next to supplementary.tex")

    # 2. clean the failed artefacts so nothing stale is reused
    for n in ("supplementary.bbl", "supplementary.blg", "supplementary.aux"):
        p = SUPP / n
        if p.exists():
            p.unlink()

    # 3. full build: pdflatex, bibtex, pdflatex, pdflatex
    rc, out = run(["pdflatex", "-interaction=nonstopmode", "supplementary.tex"], SUPP)
    print(f"  pdflatex 1: rc={rc}")
    rc, out = run(["bibtex", "supplementary"], SUPP)
    print(f"  bibtex    : rc={rc}")
    for l in out.splitlines():
        if l.strip() and ("Warning" in l or "error" in l.lower() or "couldn't" in l.lower()):
            print(f"     {l.strip()[:110]}")
    for k in (2, 3):
        rc, out = run(["pdflatex", "-interaction=nonstopmode", "-halt-on-error",
                       "supplementary.tex"], SUPP)
        errs = re.findall(r"^! (.*)$", out, re.M)
        pages = re.findall(r"Output written on supplementary\.pdf \((\d+) pages", out)
        print(f"  pdflatex {k}: rc={rc}  pages={pages[0] if pages else '?'}  errors={len(errs)}")
        for e in errs[:4]:
            print(f"     ! {e[:110]}")
        if rc != 0:
            return 1

    bbl = SUPP / "supplementary.bbl"
    nb = io.open(bbl, encoding="utf-8", errors="replace").read().count("\\bibitem") if bbl.exists() else 0
    print(f"  supplementary.bbl: {bbl.stat().st_size:,} bytes, {nb} entries")
    lg = io.open(SUPP / "supplementary.log", encoding="utf-8", errors="replace").read()
    undef = [m.group(1) for m in re.finditer(r"Citation `([^']+)' .* undefined", lg)]
    print(f"  undefined citations: {len(undef)} {undef if undef else ''}")
    return 0 if nb > 0 and not undef else 1


if __name__ == "__main__":
    raise SystemExit(main())
