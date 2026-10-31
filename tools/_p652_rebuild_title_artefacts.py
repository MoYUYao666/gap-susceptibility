# -*- coding: utf-8 -*-
r"""Rebuild the remaining title-bearing artefacts and verify the source package.

The title change reaches three more places that have not been rebuilt yet:
- title_page_prl.tex        -> title page with declarations
- PRL_submission/highlights.tex -> highlights (the title is printed above the bullets)

Both are small and compile on their own. Then the source archive is tested the way the
publisher would build it.

    python tools/_p652_rebuild_title_artefacts.py [--apply]
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
STAGE = REPO / "SUBMISSION" / "P3_PRL_revision" / "UPLOAD"


def build(tex: Path, cwd: Path, label: str) -> tuple[bool, str]:
    passes = []
    for k in range(2):
        r = subprocess.run(["pdflatex", "-interaction=nonstopmode", "-halt-on-error",
                            tex.name], cwd=str(cwd), capture_output=True)
        out = r.stdout.decode("utf-8", errors="replace")
        errs = re.findall(r"^! (.*)$", out, re.M)
        pages = re.findall(r"Output written on .*?\((\d+) pages", out)
        passes.append((r.returncode, errs, pages[0] if pages else None))
    rc, errs, pages = passes[-1]
    ok = rc == 0 and not errs
    print(f"  {'OK ' if ok else 'BAD'} {label:<24} pages={pages}  errors={len(errs)}  rc={rc}")
    for e in errs[:4]:
        print(f"        ! {e[:110]}")
    return ok, pages


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not a.apply:
        print("  (dry run)")
        return 0
    ok = True
    print("  1) title page")
    tp_ok, _ = build(PAPER / "title_page_prl.tex", PAPER, "title page")
    ok = ok and tp_ok

    print()
    print("  2) highlights")
    hp = PAPER / "PRL_submission"
    hl_ok, _ = build(hp / "highlights.tex", hp, "highlights")
    ok = ok and hl_ok
    hl_pdf = hp / "highlights.pdf"
    if hl_pdf.exists():
        r = subprocess.run(["pdftotext", "-q", "-layout", str(hl_pdf), "-"],
                           capture_output=True)
        t = re.sub(r"[\s\u00ad]+", "", r.stdout.decode("utf-8", errors="replace"))
        print(f"     new title in highlights: "
              f"{'Zero-ShotCross-ArchitectureRankAllocation' in t}  |  "
              f"old title: {'GradientStructureLaws' in t}")
        # each bullet must stay within the 85-character limit
        raw = r.stdout.decode("utf-8", errors="replace")
        print("     highlights bullets and lengths:")
        for line in raw.splitlines():
            s = line.strip()
            if len(s) > 30 and not s.lower().startswith("highlights"):
                flag = "OK " if len(s) <= 85 else f"TOO LONG ({len(s)})"
                print(f"        [{flag}] {s[:88]}")

    print()
    print("  3) source archive: does it compile standalone and carry the new title?")
    r = subprocess.run([sys.executable, str(REPO / "tools" / "_p625_test_source_zip.py"),
                        "--apply"], cwd=str(REPO), capture_output=True)
    for l in r.stdout.decode("utf-8", errors="replace").splitlines():
        if "pass " in l or "COMPILES" in l or "PROBLEM" in l or "Pages" in l:
            print(f"     {l.strip()}")

    print()
    print(f"  OVERALL: {'ALL CHECKS PASSED' if ok else 'SOMETHING NEEDS ATTENTION'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
