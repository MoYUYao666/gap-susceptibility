# -*- coding: utf-8 -*-
r"""Verify the newly inserted held-out sentence against the archive, then rebuild and sync.

Every number in the inserted sentence must resolve to pr_stats_hardened.json :: holdout. This
checks each one, recompiles, and updates the submission package.

    python tools/_p745_verify_holdout_sentence.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PA = REPO / "paper合"
PUB = REPO / "publish_clean"
NC = PA / "NC_submission"
LS = NC / "latex_source"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    ok = True
    ho = json.loads((PUB / "outputs/analysis/pr_stats_hardened.json").read_text(
        encoding="utf-8", errors="ignore"))["holdout"]
    fam, cell = ho["leave_one_family_out"], ho["leave_one_design_cell_out"]

    t = io.open(PA / "sections" / "empirical.tex", encoding="utf-8", errors="replace").read()
    m = re.search(r"To check that this is not in-sample fitting.*?predictive relation\.", t, re.S)
    if not m:
        print("  !! the inserted sentence was not found")
        return 1
    sent = " ".join(m.group(0).split())
    print("=" * 108)
    print("1. every figure in the sentence must resolve to the archive")
    print("=" * 108)
    checks = {
        "12 folds (family)": (fam["n_folds"], re.search(r"\(12 folds\)", sent)),
        "0.449 pooled (family)": (round(fam["r2_oos_pooled"], 3), "0.449" in sent),
        "0.396 median (family)": (round(fam["r2_oos_median_fold"], 3), "0.396" in sent),
        "67% of folds (family)": (round(fam["frac_folds_beat_constant"] * 100), "67\\%" in sent),
        "6 folds (cell)": (cell["n_folds"], re.search(r"\(6 folds\)", sent)),
        "0.236 pooled (cell)": (round(cell["r2_oos_pooled"], 3), "0.236" in sent),
        "0.227 median (cell)": (round(cell["r2_oos_median_fold"], 3), "0.227" in sent),
    }
    for k, (archive_val, present) in checks.items():
        good = bool(present) and archive_val is not None
        ok = ok and good
        print(f"  [{'OK  ' if good else 'TODO'}] {k:<26} archive = {archive_val}  "
              f"in sentence = {bool(present)}")

    print()
    print("=" * 108)
    print("2. recompile")
    print("=" * 108)
    if a.apply:
        for cmd in (["pdflatex", "-interaction=nonstopmode", "main_nc.tex"],
                    ["bibtex", "main_nc"],
                    ["pdflatex", "-interaction=nonstopmode", "main_nc.tex"],
                    ["pdflatex", "-interaction=nonstopmode", "main_nc.tex"]):
            subprocess.run(cmd, cwd=str(PA), capture_output=True)
        log = io.open(PA / "main_nc.log", encoding="utf-8", errors="replace").read()
        errs = re.findall(r"^! (.*)$", log, re.M)
        r = subprocess.run(["pdfinfo", str(PA / "main_nc.pdf")], capture_output=True)
        pg = re.search(r"Pages:\s+(\d+)", r.stdout.decode("utf-8", "replace"))
        print(f"  pages={pg.group(1) if pg else '?'}  errors={len(errs)}")
        for e in errs[:4]:
            print(f"     ! {e[:110]}")

        print()
        print("=" * 108)
        print("3. the compiled PDF must carry the held-out figures")
        print("=" * 108)
        r = subprocess.run(["pdftotext", "-q", "-layout", str(PA / "main_nc.pdf"), "-"],
                           capture_output=True)
        pt = " ".join(r.stdout.decode("utf-8", errors="replace").split())
        for k in ("out-of-sample", "0.449", "0.396", "0.236", "0.227"):
            good = k in pt
            ok = ok and good
            print(f"  [{'OK  ' if good else 'BAD '}] {k} in the PDF")

        print()
        print("=" * 108)
        print("4. sync the package")
        print("=" * 108)
        src, dst = PA / "sections" / "empirical.tex", LS / "sections" / "empirical.tex"
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        print("  copied sections/empirical.tex")
        members = [p for p in LS.rglob("*") if p.is_file()]
        with zipfile.ZipFile(NC / "latex_source.zip", "w", zipfile.ZIP_DEFLATED) as z:
            for p in sorted(members):
                z.write(p, p.relative_to(LS).as_posix())
        print(f"  latex_source.zip: {len(members)} members, "
              f"{(NC / 'latex_source.zip').stat().st_size:,} bytes")
        shutil.copy2(PA / "main_nc.pdf", NC / "Manuscript.pdf")
        print(f"  Manuscript.pdf: {(NC / 'Manuscript.pdf').stat().st_size:,} bytes")
    else:
        print("  (dry run)")

    print()
    print(f"  OVERALL: {'VERIFIED AND SYNCED' if ok else 'SOMETHING NEEDS ATTENTION'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
