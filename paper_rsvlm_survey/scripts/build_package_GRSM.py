# -*- coding: utf-8 -*-
r"""Build the IEEE GRSM submission package for the rewritten survey.

Compiles the two-column manuscript, the supplementary material and the cover letter, builds the LaTeX source archive,
copies everything into SUBMISSION/SURVEY_GRSM_2026-11-02/ and writes the README and hashes.

Usage
  python paper_rsvlm_survey/scripts/build_package_GRSM.py
"""
import hashlib
import io
import os
import re
import shutil
import subprocess
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(ROOT, "paper_rsvlm_survey", "grrsm")
SUB = os.path.join(ROOT, "SUBMISSION", "SURVEY_GRSM_2026-11-02")

ZIP_ITEMS = [
    "main_ieee.tex", "trends_numbers.tex", "References.bib",
    "supplementary.tex", "supplementary_body.tex", "cover_letter.tex",
    "fig_scale.pdf", "fig_provenance.pdf", "fig_audit.pdf", "fig_corpus.pdf",
    "fig_trends_volume.pdf", "fig_trends_datasets.pdf", "fig_corpus_column.pdf",
]


def run(cmd, cwd):
    subprocess.run(cmd, cwd=cwd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def compile_main(name, workdir, runs=3):
    stem = name[:-4]
    for i in range(runs):
        run(["pdflatex", "-interaction=nonstopmode", name], workdir)
        if i == 0:
            run(["bibtex", stem], workdir)
    log = io.open(os.path.join(workdir, stem + ".log"), encoding="utf-8", errors="replace").read()
    pdf = os.path.join(workdir, stem + ".pdf")
    pages = 0
    if os.path.exists(pdf):
        out = subprocess.run(["pdfinfo", pdf], capture_output=True, text=True).stdout
        m = re.search(r"Pages:\s+(\d+)", out)
        pages = int(m.group(1)) if m else 0
    return pages, len(re.findall(r"(?m)^! ", log)), len(re.findall(r"Citation .* undefined", log)), \
        len(re.findall(r"Reference .* undefined", log))


def sha(path):
    return hashlib.sha256(io.open(path, "rb").read()).hexdigest()


def build_zip():
    zp = os.path.join(SRC, "LaTeXSource_GRSM.zip")
    with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
        for name in ZIP_ITEMS:
            p = os.path.join(SRC, name)
            if os.path.exists(p):
                z.write(p, name)
            else:
                print("warning: missing", name)
        for name in sorted(os.listdir(os.path.join(SRC, "ieee_sections"))):
            z.write(os.path.join(SRC, "ieee_sections", name), "ieee_sections/" + name)
        moved = os.path.join(SRC, "supplement", "moved_prose_2026-11-02.tex")
        if os.path.exists(moved):
            z.write(moved, "supplement/moved_prose_2026-11-02.tex")
    return zp


def main():
    os.makedirs(SUB, exist_ok=True)
    pages, errs, uc, ur = compile_main("main_ieee.tex", SRC)
    print("Manuscript (IEEE two-column): %d pages, %d errors, %d undefined citations, %d undefined references" % (pages, errs, uc, ur))
    shutil.copy(os.path.join(SRC, "main_ieee.pdf"), os.path.join(SUB, "Manuscript.pdf"))

    pages, errs, uc, ur = compile_main("supplementary.tex", SRC, runs=2)
    print("Supplementary: %d pages, %d errors, %d undefined citations, %d undefined references" % (pages, errs, uc, ur))
    shutil.copy(os.path.join(SRC, "supplementary.pdf"), os.path.join(SUB, "Supplementary.pdf"))

    run(["pdflatex", "-interaction=nonstopmode", "cover_letter.tex"], SRC)
    run(["pdflatex", "-interaction=nonstopmode", "cover_letter.tex"], SRC)
    shutil.copy(os.path.join(SRC, "cover_letter.pdf"), os.path.join(SUB, "CoverLetter.pdf"))

    shutil.copy(build_zip(), os.path.join(SUB, "LaTeXSource.zip"))

    names = [n for n in ("Manuscript.pdf", "Supplementary.pdf", "CoverLetter.pdf", "LaTeXSource.zip")
             if os.path.exists(os.path.join(SUB, n))]
    lines = ["%s  %s" % (sha(os.path.join(SUB, n)), n) for n in names]
    io.open(os.path.join(SUB, "SHA256SUMS.txt"), "w", encoding="utf-8", newline="").write("\n".join(lines) + "\n")

    readme = """# Survey rewrite - frozen package for IEEE Geoscience and Remote Sensing Magazine

Status: **prepared, not yet submitted** (2026-11-02).

| item | value |
|---|---|
| manuscript | *Vision--Language Models for Remote Sensing: A Survey of Pretraining, Adaptation and Evaluation* |
| target journal | IEEE Geoscience and Remote Sensing Magazine (IEEE, ISSN 2473-2397 / 2168-6831; SCIE verified 2026-11-02 on the Clarivate Master Journal List; subscription-supported, no publication charge) |
| article type | survey / review (the journal states that original review articles and surveys are acceptable) |
| template | official IEEE Transactions LaTeX2e template (`IEEEtran.cls` v1.8b, identical to TeX Live 2025), `[lettersize,journal]`, drop cap and Roman-numeral section headings |
| author | Hongrui Wan, University of Southampton, hw4c24@soton.ac.uk, ORCID 0009-0003-8649-7504 |
| code and data snapshot cited | GitHub release v2.7, DOI 10.5281/zenodo.23835149 |

## Files

| file | role |
|---|---|
| `Manuscript.pdf` | two-column IEEE-format manuscript (main text, figures, tables, references) |
| `Supplementary.pdf` | corpus statistics, per-paper disclosure audit, catalogue of studies moved from the main text |
| `CoverLetter.pdf` | two pages, addressed to the GRSM Editor-in-Chief; states the ISPRS J decision and how this version answers it |
| `LaTeXSource.zip` | main wrapper, nine section files, bibliography, six figures, supplementary sources, cover letter source |
| `SHA256SUMS.txt` | hashes of the files above |

## What changed relative to the ISPRS J submission

The ISPRS Journal of Photogrammetry and Remote Sensing returned the earlier version without external review, with the
comment that it read as a listing of papers rather than an analysis of trends, pitfalls and a guide for future research.
This version answers that comment with three new measurements: a corpus time series (Section IV of the manuscript), a
seven-pitfall analysis with the hand-verified audit (Section V), and a research agenda with testable questions. The
catalogue-style passages were compressed into the supplementary material. The manuscript is 51 pages in the preprint
layout and 18 pages in IEEE two-column format.

## Build and checks

Produced by `paper_rsvlm_survey/scripts/build_package_GRSM.py`; figures and macros by
`analyse_corpus_trends.py`; supplementary body by `build_supp_GRSM.py`. Both documents compile with 0 errors and 0
undefined citations.
"""
    io.open(os.path.join(SUB, "README.md"), "w", encoding="utf-8", newline="").write(readme)
    print("package written to", SUB)
    print("files:", ", ".join(sorted(os.listdir(SUB))))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
