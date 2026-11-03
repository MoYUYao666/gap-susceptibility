# -*- coding: utf-8 -*-
r"""Build the ISPRS J submission package for the RS-VLM survey.

Compiles the manuscript and the cover letter, builds the LaTeX source archive and the highlights file, copies
everything into SUBMISSION/RS_REVIEW_ISPRSJ_2026-10-31/ and writes the package README and hashes.

Usage
  python paper_rsvlm_survey/scripts/build_package_ISPRSJ.py
"""
import hashlib
import io
import os
import re
import shutil
import subprocess
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(ROOT, "paper_rsvlm_survey", "isprsj")
SUB = os.path.join(ROOT, "SUBMISSION", "RS_REVIEW_ISPRSJ_2026-10-31")
ZIP_FILES = ["main.tex", "01_introduction.tex", "02_foundations.tex", "03_datasets.tex", "04_pretraining.tex",
             "05_adaptation.tex", "06_evaluation.tex", "07_open_conclusion.tex", "References.bib",
             "fig_corpus.pdf", "fig_scale.pdf", "fig_provenance.pdf", "fig_audit.pdf", "cover_letter.tex"]

HIGHLIGHTS = r"""\documentclass[11pt]{article}
\usepackage[letterpaper,margin=1in]{geometry}
\usepackage{times}
\pagestyle{empty}
\begin{document}
\noindent\textbf{Highlights}\\[0.6em]
\begin{itemize}
\item Reviews remote-sensing vision--language models by their text provenance.
\item Audits eight representative papers: none report repeated runs or dispersion.
\item Proposes an eight-field reporting protocol for comparable results.
\item The verified corpus of 833 records is released with the survey.
\item Analyses geometry, sensor heterogeneity and spatial autocorrelation.
\end{itemize}
\end{document}
"""


def compile_tex(workdir, name="main.tex", runs=3):
    for i in range(runs):
        subprocess.run(["pdflatex", "-interaction=nonstopmode", name], cwd=workdir,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if i == 0:
            subprocess.run(["bibtex", name[:-4]], cwd=workdir, stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL)
    log = io.open(os.path.join(workdir, name[:-4] + ".log"), encoding="utf-8", errors="replace").read()
    errors = len(re.findall(r"(?m)^! ", log))
    undef_c = len(re.findall(r"Citation .* undefined", log))
    undef_r = len(re.findall(r"Reference .* undefined", log))
    pdf = os.path.join(workdir, name[:-4] + ".pdf")
    pages = 0
    if os.path.exists(pdf):
        out = subprocess.run(["pdfinfo", pdf], capture_output=True, text=True).stdout
        m = re.search(r"Pages:\s+(\d+)", out)
        pages = int(m.group(1)) if m else 0
    return pages, errors, undef_c, undef_r


def build_zip():
    zp = os.path.join(SRC, "LaTeXSource.zip")
    with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
        for name in ZIP_FILES:
            p = os.path.join(SRC, name)
            if os.path.exists(p):
                z.write(p, name)
            else:
                print("warning: missing", name)
    return zp


def sha256(path):
    return hashlib.sha256(io.open(path, "rb").read()).hexdigest()


def main():
    os.makedirs(SUB, exist_ok=True)
    pages, errors, undef_c, undef_r = compile_tex(SRC)
    print("Manuscript.pdf: %d pages, %d errors, %d undefined citations, %d undefined references" % (
        pages, errors, undef_c, undef_r))
    shutil.copy(os.path.join(SRC, "main.pdf"), os.path.join(SUB, "Manuscript.pdf"))

    # cover letter
    cl = os.path.join(SRC, "cover_letter.tex")
    io.open(os.path.join(SRC, "cover_letter_highlights.tex"), "w", encoding="utf-8", newline="").write(HIGHLIGHTS)
    for name in ("cover_letter.tex", "cover_letter_highlights.tex"):
        compile_tex(SRC, name, runs=2)
    shutil.copy(os.path.join(SRC, "cover_letter.pdf"), os.path.join(SUB, "CoverLetter.pdf"))
    shutil.copy(os.path.join(SRC, "cover_letter_highlights.pdf"), os.path.join(SUB, "Highlights.pdf"))

    # LaTeX source
    shutil.copy(build_zip(), os.path.join(SUB, "LaTeXSource.zip"))

    # declaration: reuse the journal's filled template from the A3 package
    dec = os.path.join(ROOT, "SUBMISSION", "A3_ISPRSJ", "DeclarationOfCompetingInterest.docx")
    if os.path.exists(dec):
        shutil.copy(dec, os.path.join(SUB, "DeclarationOfCompetingInterest.docx"))

    # README + hashes
    names = [n for n in ("Manuscript.pdf", "LaTeXSource.zip", "CoverLetter.pdf", "Highlights.pdf",
                         "DeclarationOfCompetingInterest.docx") if os.path.exists(os.path.join(SUB, n))]
    lines = ["%s  %s" % (sha256(os.path.join(SUB, n)), n) for n in names]
    io.open(os.path.join(SUB, "SHA256SUMS.txt"), "w", encoding="utf-8", newline="").write("\n".join(lines) + "\n")

    readme = """# RS-VLM survey - frozen package for ISPRS J (Review Paper)

Status: **prepared, not yet submitted** (2026-10-31).

| item | value |
|---|---|
| manuscript | *Vision--Language Models for Remote Sensing: A Survey of Pretraining, Adaptation and Evaluation* |
| target journal | ISPRS Journal of Photogrammetry and Remote Sensing (Elsevier, ISSN 0924-2716; subscription, no APC) |
| article type | **Review Paper** |
| author | Hongrui Wan, University of Southampton, hw4c24@soton.ac.uk, ORCID 0009-0003-8649-7504 |
| code / data snapshot cited | GitHub release v2.6, DOI 10.5281/zenodo.23800255 |

## Files

| file | role |
|---|---|
| `Manuscript.pdf` | refereeing PDF (single column preprint) |
| `LaTeXSource.zip` | main.tex, seven sections, References.bib, five figures, cover letter source |
| `CoverLetter.pdf` | two pages, written for a Review Paper submission |
| `Highlights.pdf` | five bullets, each at most 85 characters |
| `DeclarationOfCompetingInterest.docx` | journal .docx template, filled (no competing interests) |
| `SHA256SUMS.txt` | hashes above |

## Why ISPRS J (evidence recorded 2026-10-31)

- the journal accepts Review Papers (author guide) and published 27 review-titled articles since 2022, including
  systematic reviews on GeoAI and geospatial foundation models (2026);
- it ran a special issue on vision--language models (editorial, 2026) and publishes the field's reference papers;
- a Crossref sweep found **no review of remote-sensing vision--language models** in the journal.

## Build and checks

Produced by `paper_rsvlm_survey/scripts/build_package_ISPRSJ.py`; the two added synthesis figures are generated by
`paper_rsvlm_survey/scripts/make_figs_isprsj.py` from the disclosure-audit records. The package is frozen: any later
revision goes to `RS_REVIEW_ISPRSJ_2026-10-31_revision/`.
"""
    io.open(os.path.join(SUB, "README.md"), "w", encoding="utf-8", newline="").write(readme)
    print("package written to", SUB)
    print("files:", ", ".join(sorted(os.listdir(SUB))))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
