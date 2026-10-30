# -*- coding: utf-8 -*-
r"""Build A1's Pattern Analysis and Applications submission package, with a standalone compile check.

Steps
  1. fix the stale `\journal{Neural Networks}` line (A1 now targets PAA);
  2. write and compile the PAA cover letter (prior-submission history and related work disclosed);
  3. assemble `paper_a1/PAA_submission/`: Manuscript.pdf, Title Page.pdf, Cover Letter.pdf, latex_source/ + zip, README;
  4. copy the source to a temp dir, compile it there, and require the same page count and zero errors.

    python tools/_p1236_build_paa_package.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import os
import shutil
import subprocess
import tempfile
import zipfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
import sys as _sys
_sys.path.insert(0, os.path.join(REPO, "tools"))
from paper_audit.texutil import count_words as _count_words

A1 = os.path.join(REPO, "paper_a1")
OUT = os.path.join(REPO, "SUBMISSION", "A1_PatternAnalysisApplications")
MAIN = os.path.join(A1, "main.tex")

COVER = r"""\documentclass[11pt]{article}
\usepackage[a4paper,margin=2.4cm]{geometry}
\usepackage[T1]{fontenc}
\usepackage{url}
\usepackage{parskip}
\pagestyle{empty}

\begin{document}

\noindent Hongrui Wan\\
University of Southampton, University Road, Southampton SO17 1BJ, United Kingdom\\
\texttt{hw4c24@soton.ac.uk}

\vspace{1.2em}
\noindent The Editor-in-Chief\\
\emph{Pattern Analysis and Applications}\\
Springer

\vspace{1.2em}
\noindent Dear Editor-in-Chief,

\vspace{0.4em}
I am submitting the enclosed manuscript, ``Order Preservation Tracks Zero-Shot Accuracy under Classification
Fine-Tuning: Why the Modality Gap Is Not a Universal Health Metric'', for consideration as an original research article
in \emph{Pattern Analysis and Applications}.

\textbf{What the paper shows.} The modality gap is widely used as a diagnostic of cross-modal alignment in
vision--language models. The manuscript asks whether it is a valid health metric for zero-shot classification, and answers
structurally rather than only empirically: accuracy depends on the ordering of each image--text similarity row, whereas
the gap is a first-moment quantity that is not a function of those orderings. We state this as a proposition and
construct matched-gap configurations that differ by $33$ accuracy points at a gap difference of $0.03$ ($52$ points at
$0.05$). A $200$-direction control shows the effect requires coherent shifts---which is the regime a fine-tuning
trajectory traverses---and the same direction replicates on three architectures (CLIP ViT-B/32, OpenCLIP laion2B, SigLIP).
The order statistic $\tau$ is proposed and validated as the cheap replacement: it needs only the top-$k$ class sets that a
validation pass already produces.

\textbf{Fit to the journal.} The contribution concerns what a representation-level statistic can and cannot reveal about a
decision rule, and the paper is deliberately analytical-empirical: matched controls, three model families, four
zero-shot benchmarks, and a quantified boundary for the mechanistic model (a first-order class-dependent bias field
reproduces the shape of the measured curve, $r=0.93$--$0.99$, but not its level across benchmarks, and we report it as a
mechanism with a boundary rather than as a predictive law). All per-run records, analysis scripts and training
configurations are openly available in a public repository and in a versioned Zenodo snapshot.

\textbf{Prior submission history, disclosed.} This manuscript has been submitted three times previously without being
accepted: \emph{Pattern Recognition Letters} (\texttt{PRLETTERS-D-26-01941}; rejected after peer review),
\emph{Neurocomputing} (\texttt{NEUCOM-D-26-20952}; desk rejection), and \emph{Neural Networks}
(\texttt{NEUNET-D-26-09426}; desk rejection without external review, the action editor judging the technical novelty
marginal). The present version responds to that record with material that did not exist in earlier versions: the
non-sufficiency proposition, the matched-gap control, the three-architecture replication, the random-direction control,
and the quantified boundary of the first-order law.

\textbf{Related work by the same author.} A critical review with a reporting checklist as its output is under review at
\emph{Pattern Recognition Letters} (\texttt{PRLETTERS-D-26-02402}). A companion manuscript on adaptation-site dynamics is under consideration at
\emph{Neurocomputing} (submitted October 2026). Neither reports the results of this manuscript; the shared ground is the general observation
that gap-based quantities and retrieval or classification accuracy are not interchangeable.

The manuscript is not under consideration elsewhere and no part of it has been published. Data, code and the use of
AI-assisted tools are declared on the title page.

\vspace{1em}
\noindent Yours sincerely,\\[0.4em]
Hongrui Wan

\end{document}
"""


def run(cmd, cwd):
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=900)
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def pages(pdf):
    from pypdf import PdfReader
    return len(PdfReader(pdf).pages)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    # 1. journal line
    t = io.open(MAIN, encoding="utf-8").read()
    n = t.count(r"\journal{Neural Networks}")
    print(f"  stale journal line: {n}")
    assert n <= 1
    if n == 1:
        t = t.replace(r"\journal{Neural Networks}", r"\journal{Pattern Analysis and Applications}", 1)
    else:
        assert r"\journal{Pattern Analysis and Applications}" in t, "journal line neither old nor new"
        print("  journal line already corrected")
    if not a.apply:
        print("  (dry run)")
        return 0
    io.open(MAIN, "w", encoding="utf-8", newline="").write(t)

    # rebuild the manuscript
    for _ in range(3):
        rc, out = run(["pdflatex", "-interaction=nonstopmode", "main.tex"], A1)
    print(f"  main.pdf rebuilt: {pages(os.path.join(A1, 'main.pdf'))} pages")

    # 2. cover letter
    cl = os.path.join(A1, "cover_letter_paa.tex")
    io.open(cl, "w", encoding="utf-8", newline="").write(COVER)
    for _ in range(2):
        rc, out = run(["pdflatex", "-interaction=nonstopmode", "cover_letter_paa.tex"], A1)
        if rc != 0:
            print("  !! cover letter compile failed")
            print(out[-1500:])
            return 1
    print(f"  cover_letter_paa.pdf: {pages(os.path.join(A1, 'cover_letter_paa.pdf'))} pages")

    # 3. package
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)
    shutil.copy2(os.path.join(A1, "main.pdf"), os.path.join(OUT, "Manuscript.pdf"))
    shutil.copy2(os.path.join(A1, "title_page.pdf"), os.path.join(OUT, "Title Page.pdf"))
    shutil.copy2(os.path.join(A1, "cover_letter_paa.pdf"), os.path.join(OUT, "Cover Letter.pdf"))
    ga = os.path.join(A1, "figures", "graphical_abstract.pdf")
    if os.path.exists(ga):
        shutil.copy2(ga, os.path.join(OUT, "Graphical Abstract.pdf"))
    src = os.path.join(OUT, "latex_source")
    os.makedirs(src)
    for f in ("main.tex", "related_work.tex", "title_page.tex"):
        shutil.copy2(os.path.join(A1, f), os.path.join(src, f))
    shutil.copytree(os.path.join(A1, "figures"), os.path.join(src, "figures"))
    nsrc = sum(len(fs) for _, _, fs in os.walk(src))
    print(f"  latex_source: {nsrc} files")

    z = os.path.join(OUT, "latex_source.zip")
    with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, _dirs, files in os.walk(src):
            for f in files:
                p = os.path.join(root, f)
                zf.write(p, os.path.relpath(p, src))
    print(f"  zip entries: {len(zipfile.ZipFile(z).namelist())}")

    # 4. standalone compile of the packaged source
    tmp = tempfile.mkdtemp(prefix="a1_paa_")
    try:
        stage = os.path.join(tmp, "src")
        shutil.copytree(src, stage)
        for _ in range(3):
            rc, out = run(["pdflatex", "-interaction=nonstopmode", "main.tex"], stage)
        log = io.open(os.path.join(stage, "main.log"), encoding="utf-8", errors="ignore").read()
        import re
        errs = len(re.findall(r"^!", log, re.M))
        undef = len(re.findall(r"undefined", log, re.I))
        got = pages(os.path.join(stage, "main.pdf"))
        want = pages(os.path.join(A1, "main.pdf"))
        print(f"  staged build: errors={errs} undefined={undef} pages={got} (expected {want})")
        ok = errs == 0 and undef == 0 and got == want
        print("  staged build", "OK" if ok else "FAILED")
        if not ok:
            return 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    readme = """# A1 — Pattern Analysis and Applications submission package

| portal item | file | note |
|---|---|---|
| Manuscript | `Manuscript.pdf` | %d pages, elsarticle review format |
| Title page | `Title Page.pdf` | 1 page; title, affiliation, corresponding author, full Declarations |
| Cover Letter | `Cover Letter.pdf` | %d page; discloses prior submission history and related work |
| Graphical abstract (optional) | `Graphical Abstract.pdf` | 1 page; four-panel summary |
| LaTeX source | `latex_source.zip` | main.tex, related_work.tex, title_page.tex, figures/ |

Compliance (Pattern Analysis and Applications guide, read 2026-10-18): abstract %d words (limit 150-250), keywords 5
(limit 4-6), no page or word limit on the body, LaTeX accepted, Declarations consolidated on a separate title page,
AI-tool use documented in the methods section and in the Declarations.

Build: `pdflatex -interaction=nonstopmode main.tex` three times; the packaged source was recompiled in a temporary
directory and reproduced the same page count with zero errors.
""" % (pages(os.path.join(A1, "main.pdf")), pages(os.path.join(A1, "cover_letter_paa.pdf")), _count_words(open(os.path.join(A1, "main.tex"), encoding="utf-8").read().split("\\begin{abstract}")[1].split("\\end{abstract}")[0]))
    io.open(os.path.join(OUT, "README.md"), "w", encoding="utf-8", newline="").write(readme)
    print("  README.md written")
    for f in sorted(os.listdir(OUT)):
        p = os.path.join(OUT, f)
        print(f"    {f:32s} {os.path.getsize(p):>10,} B" if os.path.isfile(p) else f"    {f:32s} [dir]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
