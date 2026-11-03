# -*- coding: utf-8 -*-
r"""Sync the updated Paper A sources and PDF into the submission package, then verify.

What changed: main_nc.tex (data availability statement, English header comment) and
sections/conclusion.tex (contradictory one-liner replaced). The package holds copies under
NC_submission/latex_source/ plus a zip, so all three have to be refreshed before the operator
submits.

    python tools/_p690_paperhe_sync_package.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PA = REPO / "paper合"
NC = PA / "NC_submission"
LS = NC / "latex_source"
ZIP = NC / "latex_source.zip"
DOI = "10.5281/zenodo.23341223"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    print("=" * 104)
    print("1. what the package currently holds vs the live sources")
    print("=" * 104)
    pairs = [(PA / "main_nc.tex", LS / "main_nc.tex"),
             (PA / "sections" / "conclusion.tex", LS / "sections" / "conclusion.tex")]
    stale = []
    for live, pkg in pairs:
        if not pkg.exists():
            print(f"  MISSING in package: {pkg.relative_to(NC)}")
            stale.append(live)
            continue
        same = live.read_bytes() == pkg.read_bytes()
        print(f"  {'same ' if same else 'STALE'} {pkg.relative_to(NC)}")
        if not same:
            stale.append(live)

    print()
    print("=" * 104)
    print("2. copy the updated sources in")
    print("=" * 104)
    for live, pkg in pairs:
        if a.apply:
            pkg.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(live, pkg)
            print(f"  copied -> {pkg.relative_to(NC)}")
        else:
            print(f"  would copy {live.name} -> {pkg.relative_to(NC)}")

    print()
    print("=" * 104)
    print("3. rebuild the LaTeX source zip")
    print("=" * 104)
    if a.apply:
        members = [p for p in LS.rglob("*") if p.is_file()]
        with zipfile.ZipFile(ZIP, "w", zipfile.ZIP_DEFLATED) as z:
            for p in sorted(members):
                z.write(p, p.relative_to(LS).as_posix())
        with zipfile.ZipFile(ZIP) as z:
            bad = z.testzip()
            names = z.namelist()
        print(f"  {ZIP.name}: {len(names)} members, {ZIP.stat().st_size:,} bytes, "
              f"integrity {'OK' if bad is None else 'CORRUPT'}")
        # does the zip carry the new statement?
        with zipfile.ZipFile(ZIP) as z:
            t = z.read("main_nc.tex").decode("utf-8", "replace")
        print(f"  zip's main_nc.tex carries the DOI: {DOI in t}")
    else:
        print("  (dry run)")

    print()
    print("=" * 104)
    print("4. recompile and copy the manuscript PDF into the package")
    print("=" * 104)
    if a.apply:
        for cmd in (["pdflatex", "-interaction=nonstopmode", "main_nc.tex"],
                    ["bibtex", "main_nc"],
                    ["pdflatex", "-interaction=nonstopmode", "main_nc.tex"],
                    ["pdflatex", "-interaction=nonstopmode", "main_nc.tex"]):
            r = subprocess.run(cmd, cwd=str(PA), capture_output=True)
        log = io.open(PA / "main_nc.log", encoding="utf-8", errors="replace").read()
        errs = re.findall(r"^! (.*)$", log, re.M)
        u = re.findall(r"Reference `[^']+' .* undefined", log)
        c = re.findall(r"Citation `[^']+' .* undefined", log)
        r = subprocess.run(["pdfinfo", str(PA / "main_nc.pdf")], capture_output=True)
        pg = re.search(r"Pages:\s+(\d+)", r.stdout.decode("utf-8", "replace"))
        print(f"  compiled: pages={pg.group(1) if pg else '?'}  errors={len(errs)}  "
              f"undef-refs={len(u)}  undef-cites={len(c)}")
        for e in errs[:5]:
            print(f"     ! {e[:110]}")
        shutil.copy2(PA / "main_nc.pdf", NC / "Manuscript.pdf")
        print(f"  copied main_nc.pdf -> NC_submission/Manuscript.pdf "
              f"({(NC / 'Manuscript.pdf').stat().st_size:,} bytes)")
    else:
        print("  (dry run)")

    print()
    print("=" * 104)
    print("5. verify the package manuscript")
    print("=" * 104)
    pdf = NC / "Manuscript.pdf"
    r = subprocess.run(["pdftotext", "-q", "-layout", str(pdf), "-"], capture_output=True)
    t = r.stdout.decode("utf-8", errors="replace")
    flat = re.sub(r"[\s\u00ad]+", "", t)
    checks = {
        f"DOI {DOI} present": DOI.replace(" ", "") in flat,
        "no 'currently private'": "currentlyprivate" not in flat,
        "no 'on request' data statement": "Datawillbemadeavailableonrequest" not in flat,
        "no '??'": "??" not in t,
        "no Chinese characters": not re.search(r"[\u4e00-\u9fff]", t),
    }
    ok = True
    for k, v in checks.items():
        ok = ok and v
        print(f"  {'OK ' if v else 'BAD'} {k}")
    print()
    print(f"  OVERALL: {'PACKAGE READY' if ok else 'SOMETHING NEEDS ATTENTION'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
