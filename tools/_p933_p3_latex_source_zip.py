# -*- coding: utf-8 -*-
r"""Rebuild P3's LaTeX source archive from the current sources.

The 13 October upload carried `P3_PRLETTERS-D-26-02378_LaTeX_Source.zip` with 17 entries:

    README_compile.txt, main.tex, main.bbl, references.bib
    sections/{introduction,related_work,theory,experiments,discussion,conclusion}.tex
    figures/{fig1_phase_transition,fig2_counterfactual}.png
    supplementary/{supplementary.tex, supplementary.bbl, references.bib}
    supplementary/figures/{fig3_ers,fig4_E_trajectory}.png

Since then the manuscript and the supplement have both changed (section pointers, corollary numbering,
theorem spacing, table layout, added sample-size table), so the archive has to be rebuilt rather than
reused. This rebuilds the same layout from the live files, verifies every member is byte-identical to its
source, then extracts the archive into a temporary directory and compiles **both** documents there to
prove the package is self-contained.

    python tools/_p933_p3_latex_source_zip.py [--apply]
"""
from __future__ import annotations

import argparse
import hashlib
import io
import re
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
P3 = REPO / "paper3" / "paper_ieee"
REV = REPO / "SUBMISSION" / "P3_PRL_revision"
OUT = REV / "UPLOAD_2026-10-15" / "P3_PRLETTERS-D-26-02378_LaTeX_Source.zip"

# (path in the archive, path on disk)
MEMBERS = [
    ("main.tex", P3 / "main.tex"),
    ("main.bbl", P3 / "main.bbl"),
    ("references.bib", P3 / "references.bib"),
    ("sections/introduction.tex", P3 / "sections" / "introduction.tex"),
    ("sections/related_work.tex", P3 / "sections" / "related_work.tex"),
    ("sections/theory.tex", P3 / "sections" / "theory.tex"),
    ("sections/experiments.tex", P3 / "sections" / "experiments.tex"),
    ("sections/discussion.tex", P3 / "sections" / "discussion.tex"),
    ("sections/conclusion.tex", P3 / "sections" / "conclusion.tex"),
    ("figures/fig1_phase_transition.png", P3 / "figures" / "fig1_phase_transition.png"),
    ("figures/fig2_counterfactual.png", P3 / "figures" / "fig2_counterfactual.png"),
    ("supplementary/supplementary.tex", P3 / "supplementary" / "supplementary.tex"),
    ("supplementary/supplementary.bbl", P3 / "supplementary" / "supplementary.bbl"),
    ("supplementary/references.bib", P3 / "supplementary" / "references.bib"),
    ("supplementary/figures/fig3_ers.png", P3 / "supplementary" / "figures" / "fig3_ers.png"),
    ("supplementary/figures/fig4_E_trajectory.png", P3 / "supplementary" / "figures" / "fig4_E_trajectory.png"),
]

README = """Compilation instructions for the P3 LaTeX source
================================================

Manuscript: PRLETTERS-D-26-02378R1
Title:      Zero-Shot Cross-Architecture Rank Allocation from Gradient Geometry
Journal:    Pattern Recognition Letters

The manuscript:

    pdflatex main
    bibtex   main
    pdflatex main
    pdflatex main

The Supplementary Material is a separate document and is compiled from its own folder:

    cd supplementary
    pdflatex supplementary
    bibtex   supplementary
    pdflatex supplementary
    pdflatex supplementary

Both use the standard IEEEtran class plus amsmath, amssymb, amsfonts, amsthm, graphicx, booktabs,
multirow and hyperref, all of which ship with a full TeX Live installation. The bibliography is also
supplied as the compiled .bbl file, so bibtex is optional if the .bib is unavailable.

Layout:

    main.tex, main.bbl, references.bib
    sections/           introduction, related_work, theory, experiments, discussion, conclusion
    figures/            fig1_phase_transition.png, fig2_counterfactual.png
    supplementary/      supplementary.tex, supplementary.bbl, references.bib
    supplementary/figures/  fig3_ers.png, fig4_E_trajectory.png
"""


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def compile_in(tmp: Path, folder: Path, stem: str) -> tuple[int, int, str]:
    """Compile one document inside an extracted copy; return (errors, undefined, pages).

    The final pdflatex run is the one whose log is examined, so the check reflects the state a reader
    would get. If the log reports errors, the offending lines are printed, because an earlier version of
    this script asserted only "not clean" and gave no way to see why.
    """
    work = tmp / folder if folder != Path(".") else tmp
    for cmd in (["pdflatex", "-interaction=nonstopmode", f"{stem}.tex"],
                ["bibtex", stem],
                ["pdflatex", "-interaction=nonstopmode", f"{stem}.tex"],
                ["pdflatex", "-interaction=nonstopmode", f"{stem}.tex"]):
        subprocess.run(cmd, cwd=work, capture_output=True)
    log = (work / f"{stem}.log").read_text(encoding="utf-8", errors="replace")
    errors = sum(1 for line in log.splitlines() if line.startswith("!"))
    # Count real problems only. A bare occurrence of the word "undefined" also matches
    # "Font shape `OT1/ptm/m/scit' undefined", which is a font substitution warning, not a
    # broken reference, and it made this check fail while the document was in fact fine.
    undef_refs = len(re.findall(r"Reference `[^']*' on page \d+ undefined", log))
    undef_cites = len(re.findall(r"Citation `[^']*' undefined", log))
    undefined = undef_refs + undef_cites
    pdf = work / f"{stem}.pdf"
    pages = "?"
    if pdf.exists():
        import pypdf
        pages = str(len(pypdf.PdfReader(str(pdf)).pages))
    if errors or undefined:
        print(f"    [{stem}] errors={errors}, 'undefined'={undefined}; first problems:")
        for line in log.splitlines():
            if line.startswith("!"):
                print(f"      {line[:118]}")
        for m in list(re.finditer(r"^!.*?\n(?:.*\n){0,4}?l\.(\d+)(.*)$", log, re.M))[:4]:
            print(f"      at {stem}.tex:{m.group(1)} -> {m.group(2)[:80]}")
    return errors, undefined, pages


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    missing = [str(src) for _n, src in MEMBERS if not src.exists()]
    assert not missing, f"missing sources: {missing}"
    print(f"  members: {len(MEMBERS) + 1} (including README_compile.txt)")
    for name, src in MEMBERS:
        print(f"    {name:<44} {src.stat().st_size:>9,} bytes")

    if not a.apply:
        print("  (dry run)")
        return 0

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("README_compile.txt", README)
        for name, src in MEMBERS:
            z.write(src, arcname=name)

    with zipfile.ZipFile(OUT) as z:
        names = z.namelist()
        assert z.testzip() is None, "the archive is corrupt"
        for name, src in MEMBERS:
            assert sha(z.read(name)) == sha(src.read_bytes()), f"{name} differs from its source"
    print(f"  wrote {OUT.name}: {OUT.stat().st_size:,} bytes, {len(names)} entries, CRC ok, "
          f"every member byte-identical to its source")

    tmp = Path(tempfile.mkdtemp(prefix="p3_src_"))
    try:
        with zipfile.ZipFile(OUT) as z:
            z.extractall(tmp)
        e1, u1, p1 = compile_in(tmp, Path("."), "main")
        e2, u2, p2 = compile_in(tmp, Path("supplementary"), "supplementary")
        print(f"  extracted and compiled: main.pdf {p1} pages (errors {e1}, 'undefined' {u1}), "
              f"supplementary.pdf {p2} pages (errors {e2}, 'undefined' {u2})")
        assert e1 == 0 and u1 == 0, "the extracted manuscript does not compile cleanly"
        assert e2 == 0 and u2 == 0, "the extracted supplement does not compile cleanly"
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print("  the archive compiles standalone for both documents")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
