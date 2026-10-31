# -*- coding: utf-8 -*-
r"""Extract the source archive to a clean directory and compile it standalone.

A source package is only valid if it compiles by itself. This extracts the zip into a fresh
temporary directory with nothing else in it, runs pdflatex as the publisher would, and
reports the page count and any error.

    python tools/_p625_test_source_zip.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ZIP = REPO / "SUBMISSION" / "P3_PRL_revision" / "manuscript" / "P3_latex_source_revision.zip"
OUT = REPO / "outputs" / "analysis" / "source_zip_build_test.json"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    tmp = Path(tempfile.mkdtemp(prefix="p3zip_"))
    print(f"  Extracting to {tmp}")
    with zipfile.ZipFile(ZIP) as z:
        z.extractall(tmp)
    files = sorted(p.relative_to(tmp).as_posix() for p in tmp.rglob("*") if p.is_file())
    print(f"  {len(files)} files extracted")
    print()
    if not a.apply:
        print("  (dry run)")
        shutil.rmtree(tmp, ignore_errors=True)
        return 0

    passes = []
    for k in range(3):
        r = subprocess.run(["pdflatex", "-interaction=nonstopmode", "main.tex"],
                           cwd=str(tmp), capture_output=True)
        out = r.stdout.decode("utf-8", errors="replace")
        errs = re.findall(r"^! (.*)$", out, re.M)
        pages = re.findall(r"Output written on main\.pdf \((\d+) pages", out)
        passes.append({"pass": k + 1, "rc": r.returncode,
                       "errors": errs[:5], "pages": pages[0] if pages else None})
        print(f"  pass {k+1}: rc={r.returncode}  pages={pages[0] if pages else '?'}  "
              f"errors={len(errs)}")
        if errs:
            for e in errs[:5]:
                print(f"      ! {e[:100]}")
        if r.returncode != 0 and k == 0:
            break
    pdf = tmp / "main.pdf"
    ok = pdf.exists() and all(not p["errors"] for p in passes)
    print()
    print(f"  Produced main.pdf: {pdf.exists()}  ({pdf.stat().st_size if pdf.exists() else 0:,} bytes)")
    print(f"  Pages: {passes[-1]['pages'] if passes else '?'}")
    print(f"  => {'SOURCE PACKAGE COMPILES STANDALONE' if ok else 'PROBLEM - see errors above'}")
    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(
            {"zip": str(ZIP.relative_to(REPO)), "files": files, "passes": passes,
             "compiles": ok}, ensure_ascii=False, indent=1))
        print(f"\n  Wrote {OUT.relative_to(REPO)}")
    shutil.rmtree(tmp, ignore_errors=True)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
