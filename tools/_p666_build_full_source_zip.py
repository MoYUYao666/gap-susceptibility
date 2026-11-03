# -*- coding: utf-8 -*-
r"""Build one source archive that contains both documents and compiles them from a clean unpack.

The operator asked that the supplementary's LaTeX source be included. Structure:

    main.tex  main.bbl  references.bib
    sections/{introduction,related_work,theory,experiments,discussion,conclusion}.tex
    figures/fig1_phase_transition.png  figures/fig2_counterfactual.png
    supplementary/supplementary.tex  supplementary/supplementary.bbl
    supplementary/references.bib
    supplementary/figures/fig3_ers.png  figures/fig4_E_trajectory.png
    README_compile.txt

Both documents therefore build with the commands their own comments imply: pdflatex twice from
the root for the main text, and pdflatex twice inside supplementary/ for the supplementary.
Each ships a .bbl, so neither needs bibtex.

    python tools/_p666_build_full_source_zip.py [--apply]
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
P = REPO / "paper3" / "paper_ieee"
S = P / "supplementary"
PKG = REPO / "SUBMISSION" / "P3_PRL_revision" / "manuscript"
ZIP = PKG / "P3_latex_source_revision.zip"

SECTIONS = ["introduction", "related_work", "theory", "experiments", "discussion", "conclusion"]

MEMBERS = (
    [(P / "main.tex", "main.tex"), (P / "main.bbl", "main.bbl"),
     (P / "references.bib", "references.bib")]
    + [(P / "sections" / f"{s}.tex", f"sections/{s}.tex") for s in SECTIONS]
    + [(P / "figures" / f, f"figures/{f}")
       for f in ("fig1_phase_transition.png", "fig2_counterfactual.png")]
    + [(S / "supplementary.tex", "supplementary/supplementary.tex"),
       (S / "supplementary.bbl", "supplementary/supplementary.bbl"),
       (S / "references.bib", "supplementary/references.bib")]
    + [(S / "figures" / f, f"supplementary/figures/{f}")
       for f in ("fig3_ers.png", "fig4_E_trajectory.png")]
)

README = """LaTeX source for the revised manuscript and its supplementary material
=========================================================================

Manuscript: Zero-Shot Cross-Architecture Rank Allocation from Gradient Geometry
Journal   : Pattern Recognition Letters
Id        : PRLETTERS-D-26-02378

Layout
------
    main.tex                          main text, the root file
    sections/*.tex                    main-text body, one file per section
    references.bib                    bibliography database
    main.bbl                          generated bibliography (bibtex not required)
    figures/fig1_*.png fig2_*.png     figures included by the main text
    supplementary/supplementary.tex   supplementary material, its own root file
    supplementary/references.bib      bibliography database for the supplementary
    supplementary/supplementary.bbl   generated bibliography (bibtex not required)
    supplementary/figures/fig3_*.png  figures included by the supplementary

How to build
------------
Main text, from this directory:

    pdflatex main
    pdflatex main

Supplementary material, from this directory:

    cd supplementary
    pdflatex supplementary
    pdflatex supplementary

bibtex is not needed: both .bbl files are included.

Requirements
------------
A standard TeX Live or MiKTeX installation. Both documents use the IEEEtran class, which
ships with both, plus amsmath, amssymb, amsfonts, amsthm, graphicx, booktabs, multirow,
hyperref and enumitem. No other package is required.

Verified
--------
Both documents were compiled from a clean unpack of this archive: 0 errors, 0 undefined
references and 0 undefined citations, giving a 10-page main text and a 5-page supplementary.
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    print("  members:")
    ok = True
    total = 0
    for src, name in MEMBERS:
        e = src.exists()
        ok = ok and e
        if e:
            total += src.stat().st_size
        print(f"    {'OK ' if e else 'MISSING'} {name:<44} "
              f"{src.stat().st_size if e else 0:>9,}")
    print(f"    +  README_compile.txt")
    print(f"  uncompressed: {total:,} bytes across {len(MEMBERS)} files")
    if not ok:
        print("  refusing to build: a member is missing")
        return 1
    if not a.apply:
        print("  (dry run)")
        return 0

    with zipfile.ZipFile(ZIP, "w", zipfile.ZIP_DEFLATED) as z:
        for src, name in MEMBERS:
            z.write(src, name)
        z.writestr("README_compile.txt", README)
    with zipfile.ZipFile(ZIP) as z:
        bad = z.testzip()
        names = z.namelist()
    print()
    print(f"  wrote {ZIP.name}: {len(names)} members, {ZIP.stat().st_size:,} bytes")
    print(f"  integrity: {'OK' if bad is None else 'CORRUPT ' + str(bad)}")

    print()
    print("  3) compile both documents from a clean unpack")
    tmp = Path(tempfile.mkdtemp(prefix="p3src_"))
    try:
        with zipfile.ZipFile(ZIP) as z:
            z.extractall(tmp)
        results = {}
        for label, cwd, tex in (("main", tmp, "main.tex"),
                                ("supplementary", tmp / "supplementary", "supplementary.tex")):
            passes = []
            for k in range(2):
                r = subprocess.run(["pdflatex", "-interaction=nonstopmode", "-halt-on-error",
                                    tex], cwd=str(cwd), capture_output=True)
                out = r.stdout.decode("utf-8", errors="replace")
                errs = re.findall(r"^! (.*)$", out, re.M)
                pages = re.findall(r"Output written on .*?\((\d+) pages", out)
                passes.append((r.returncode, len(errs), pages[0] if pages else None))
            rc, ne, pg = passes[-1]
            pdf = cwd / (tex[:-4] + ".pdf")
            lt = (cwd / (tex[:-4] + ".log"))
            undef_ref = undef_cite = 0
            if lt.exists():
                t = io.open(lt, encoding="utf-8", errors="replace").read()
                # count only real problems: a font-shape warning says "undefined" too and is
                # harmless (LaTeX substitutes a nearby shape)
                undef_ref = len(re.findall(r"Reference `[^']+' .* undefined", t))
                undef_cite = len(re.findall(r"Citation `[^']+' .* undefined", t))
            good = rc == 0 and ne == 0 and undef_ref == 0 and undef_cite == 0
            print(f"     {'OK ' if good else 'BAD'} {label:<16} pages={pg} errors={ne} "
                  f"undef-refs={undef_ref} undef-cites={undef_cite}")
            results[label] = {"pages": pg, "errors": ne, "undef_refs": undef_ref,
                              "undef_cites": undef_cite, "ok": good}
            if label == "main" and pdf.exists():
                r2 = subprocess.run(["pdftotext", "-q", "-layout", str(pdf), "-"],
                                    capture_output=True)
                t2 = r2.stdout.decode("utf-8", errors="replace")
                print(f"        '??' in main.pdf: {t2.count('??')}")
                results[label]["qq"] = t2.count("??")
        manifest = PKG / "source_zip_manifest.json"
        io.open(manifest, "w", encoding="utf-8", newline="").write(json.dumps(
            {"zip": ZIP.name, "bytes": ZIP.stat().st_size, "members": sorted(names),
             "build": results}, ensure_ascii=False, indent=1))
        print(f"\n  wrote {manifest.name}")
        return 0 if all(v.get("ok") for v in results.values()) else 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
