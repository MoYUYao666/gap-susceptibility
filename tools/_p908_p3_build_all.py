# -*- coding: utf-8 -*-
r"""Show what each P3 main-text variant includes, then build the two that matter.

`main.tex` is the submitted 10-page manuscript; `main_full.tex` is the 13-page archive that also carries
the appendix; `main_10pp.tex` is the older layout. All three share the same `sections/`, so a change
there has to leave every variant compiling.

    python tools/_p908_p3_build_all.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import re
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
P3 = REPO / "paper3" / "paper_ieee"
LOGS = REPO / "outputs" / "analysis"
VARIANTS = ["main", "main_full", "main_10pp"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    for v in VARIANTS:
        t = (P3 / f"{v}.tex").read_text(encoding="utf-8")
        inc = re.findall(re.escape(chr(92)) + r"input\{([^}]*)\}", t)
        print(f"  {v}.tex includes: {inc}")

    if not a.apply:
        print("  (dry run)")
        return 0

    for v in VARIANTS:
        for i, cmd in enumerate((
            ["pdflatex", "-interaction=nonstopmode", f"{v}.tex"],
            ["bibtex", v],
            ["pdflatex", "-interaction=nonstopmode", f"{v}.tex"],
            ["pdflatex", "-interaction=nonstopmode", f"{v}.tex"],
        )):
            r = subprocess.run(cmd, cwd=P3, capture_output=True)
            if i == 3:                      # keep the last pass for the audit
                (LOGS / f"_p3_{v}_final.log").write_bytes((r.stdout or b"") + (r.stderr or b""))

    print()
    for v in VARIANTS:
        log = (LOGS / f"_p3_{v}_final.log").read_text(encoding="utf-8", errors="replace")
        errs = re.findall(r"^!.*$", log, re.M)
        refs = sorted(set(re.findall(r"Reference `([^']+)' on page", log)))
        cites = sorted(set(re.findall(r"Citation `([^']+)'", log)))
        pdf = P3 / f"{v}.pdf"
        pages = "?"
        if pdf.exists():
            import pypdf
            pages = len(pypdf.PdfReader(str(pdf)).pages)
        print(f"  {v}.pdf: {pages} pages | errors {len(errs)} | undefined refs {len(refs)} {refs[:4]} "
              f"| undefined cites {len(cites)}")
        if errs:
            for e in errs[:3]:
                print(f"      {e[:110]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
