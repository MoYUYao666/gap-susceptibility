# -*- coding: utf-8 -*-
r"""Recompile Paper A and verify the strict-freezing count is now consistent everywhere.

After changing 95 -> 104 in two files, this confirms the compiled PDF carries 104 and no stale 95,
and syncs the updated sources and PDF into the submission package.

    python tools/_p724_rebuild_and_sync.py [--apply]
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


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    ok = True

    print("=" * 104)
    print("1. source check")
    print("=" * 104)
    for rel in ("sections/supplement.tex", "sections/conclusion.tex",
                "sections/empirical.tex", "main_nc.tex"):
        t = io.open(PA / rel, encoding="utf-8", errors="replace").read()
        for m in re.finditer(r"(\d+)\s+strict-freezing controls|and (\d+) under strict freezing",
                             t):
            v = m.group(1) or m.group(2)
            ln = t[:m.start()].count("\n") + 1
            print(f"  {rel}:{ln}  ->  {v}")

    if not a.apply:
        print("  (dry run)")
        return 0

    print()
    print("=" * 104)
    print("2. recompile")
    print("=" * 104)
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
    print(f"  pages={pg.group(1) if pg else '?'}  errors={len(errs)}  "
          f"undef-refs={len(u)}  undef-cites={len(c)}")
    for e in errs[:5]:
        print(f"     ! {e[:110]}")

    print()
    print("=" * 104)
    print("3. PDF check")
    print("=" * 104)
    r = subprocess.run(["pdftotext", "-q", "-layout", str(PA / "main_nc.pdf"), "-"],
                       capture_output=True)
    t = " ".join(r.stdout.decode("utf-8", errors="replace").split())
    checks = {
        "'104 strict-freezing' present": "104 strict-freezing" in t,
        "no '95 strict-freezing'": "95 strict-freezing" not in t,
        "catalogue 221 runs present": "221 runs" in t,
        "383 experiments present": "383 experiments" in t,
        "no '??'": "??" not in t,
    }
    for k, v in checks.items():
        ok = ok and v
        print(f"  {'OK ' if v else 'BAD'} {k}")

    print()
    print("=" * 104)
    print("4. sync into the package")
    print("=" * 104)
    for rel in ("sections/supplement.tex", "sections/conclusion.tex"):
        src, dst = PA / rel, LS / rel
        if src.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            print(f"  copied {rel}")
    members = [p for p in LS.rglob("*") if p.is_file()]
    with zipfile.ZipFile(NC / "latex_source.zip", "w", zipfile.ZIP_DEFLATED) as z:
        for p in sorted(members):
            z.write(p, p.relative_to(LS).as_posix())
    print(f"  rebuilt latex_source.zip: {len(members)} members, "
          f"{(NC / 'latex_source.zip').stat().st_size:,} bytes")
    shutil.copy2(PA / "main_nc.pdf", NC / "Manuscript.pdf")
    print(f"  copied main_nc.pdf -> Manuscript.pdf "
          f"({(NC / 'Manuscript.pdf').stat().st_size:,} bytes)")

    print()
    print(f"  OVERALL: {'CONSISTENT AND PACKAGE UPDATED' if ok else 'SOMETHING NEEDS ATTENTION'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
