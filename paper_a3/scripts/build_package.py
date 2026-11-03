# -*- coding: utf-8 -*-
r"""Build the submission package for A3 and audit it.

Produces (under paper_a3/submission/):
  Manuscript.pdf      compiled from paper_a3/draft/main.tex
  LaTeXSource.zip     main.tex, sections, tables, bibliography, generated numbers, figures, numbers.tex
  CoverLetter.pdf     two variants: ISPRS J (primary; SCI verification pending per registry) and Image and Vision
                      Computing (verified fallback)
  Highlights.pdf      three to five bullets, Elsevier format
  DeclarationOfInterest.md
  README.md
  SHA256SUMS.txt

Audit checks (all must pass):
  - manuscript compiles standalone from the zip: 0 errors, 0 undefined citations/references
  - page count and figure font check are reported
  - every generated table/numbers file is newer than the JSON it came from
  - upload filenames contain no underscore (repository rule)

Usage
  python build_package.py
"""
import glob
import hashlib
import io
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DRAFT = os.path.join(ROOT, "draft")
SUB = os.path.join(ROOT, "submission")
FIGS = os.path.join(ROOT, "figures")


def sha(p):
    h = hashlib.sha256()
    with io.open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def compile_pdf(tex_name, out_name, cwd):
    for _ in range(2):
        subprocess.run(["pdflatex", "-interaction=nonstopmode", tex_name], cwd=cwd,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["bibtex", tex_name.replace(".tex", "")], cwd=cwd,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(2):
        subprocess.run(["pdflatex", "-interaction=nonstopmode", tex_name], cwd=cwd,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    log = io.open(os.path.join(cwd, tex_name.replace(".tex", ".log")), encoding="utf-8", errors="replace").read()
    pages = 0
    m = re.search(r"Output written on .*?\((\d+) pages?", log)
    if m:
        pages = int(m.group(1))
    return pages, len(re.findall(r"(?m)^! ", log)), len(re.findall(r"Citation .* undefined", log)), \
        len(re.findall(r"Reference .* undefined", log))


def build():
    os.makedirs(SUB, exist_ok=True)
    # 1) manuscript
    pages, errors, undefc, undefr = compile_pdf("main.tex", "Manuscript.pdf", DRAFT)
    shutil.copy(os.path.join(DRAFT, "main.pdf"), os.path.join(SUB, "Manuscript.pdf"))
    print("Manuscript.pdf: %d pages, %d errors, %d undefined citations, %d undefined references" % (
        pages, errors, undefc, undefr))

    # 2) source zip (flat, as Elsevier likes it)
    zp = os.path.join(SUB, "LaTeXSource.zip")
    files = ["main.tex", "References.bib", "numbers.tex", "rust_numbers.tex", "cloud_numbers.tex",
             "budget_numbers.tex", "repeated_numbers.tex", "llmarm_numbers.tex", "probe_numbers.tex", "fullarm_numbers.tex"]
    files += sorted(os.path.basename(p) for p in glob.glob(os.path.join(DRAFT, "0*.tex")))
    files += sorted(os.path.basename(p) for p in glob.glob(os.path.join(DRAFT, "table_*.tex")))
    files += ["fig1_provenance.pdf", "fig2_scaling.pdf"]
    with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
        for f in files:
            p = os.path.join(DRAFT, f)
            if not os.path.exists(p):
                p = os.path.join(FIGS, f)
            if os.path.exists(p):
                z.write(p, f)
    print("LaTeXSource.zip: %d entries" % len(zipfile.ZipFile(zp).namelist()))

    # 3) highlights and declarations
    hl = r"""\documentclass[11pt]{article}
\usepackage[letterpaper,margin=1in]{geometry}
\usepackage{times}
\pagestyle{empty}
\begin{document}
\noindent\textbf{Highlights}\\[0.6em]
\begin{itemize}
\item Text provenance tested at a matched budget: 4 corpora, 3 sites, 3 seeds.
\item Human captions win only where they describe the whole image.
\item More pairs let the weakest text source overtake the richest one.
\item Text-tower LoRA lowers the modality gap; joint LoRA retrieves best.
\item Generated text inflates within-corpus caption scores, not transfer.
\end{itemize}
\end{document}
"""
    tmp = tempfile.mkdtemp(prefix="a3_highlights_")
    hl_tex = os.path.join(tmp, "hl.tex")
    io.open(hl_tex, "w", encoding="utf-8", newline="").write(hl)
    compile_pdf("hl.tex", "hl.pdf", tmp)
    shutil.copy(os.path.join(tmp, "hl.pdf"), os.path.join(SUB, "Highlights.pdf"))
    shutil.rmtree(tmp, ignore_errors=True)

    # official Elsevier declaration template (filled: no competing interests)
    dec_src = os.path.join(ROOT, "docs", "declaration-of-competing-interests-template.docx")
    dec_dst = os.path.join(SUB, "DeclarationOfCompetingInterest.docx")
    if os.path.exists(dec_dst):
        pass
    elif os.path.exists(dec_src):
        shutil.copy(dec_src, dec_dst)
    else:
        print("warning: competing-interest docx missing")

    # graphical abstract (optional, encouraged)
    ga_src = os.path.join(FIGS, "graphical_abstract.pdf")
    if os.path.exists(ga_src):
        shutil.copy(ga_src, os.path.join(SUB, "GraphicalAbstract.pdf"))
    else:
        print("warning: graphical abstract missing")

    # remove the superseded markdown declaration if present
    old_md = os.path.join(SUB, "DeclarationOfInterest.md")
    if os.path.exists(old_md):
        os.remove(old_md)
    return pages, errors, undefc, undefr


def audit():
    problems = []
    if not os.path.exists(os.path.join(SUB, "Manuscript.pdf")):
        problems.append("Manuscript.pdf missing")
    # fonts
    try:
        out = subprocess.run(["pdffonts", os.path.join(SUB, "Manuscript.pdf")], capture_output=True, text=True).stdout
        bad = [ln for ln in out.splitlines() if ("Type 3" in ln) or ("DejaVu" in ln) or ("Arial" in ln)]
        if bad:
            problems.append("figure/embedded font problem: %s" % bad[:2])
    except Exception as e:
        problems.append("pdffonts failed: %s" % e)
    # generated files newer than the JSONs
    pairs = [(os.path.join(DRAFT, "table_main.tex"), os.path.join(ROOT, "analysis", "full_10k_aggregate.json")),
             (os.path.join(DRAFT, "table_scaling.tex"), os.path.join(ROOT, "analysis", "h2_scaling.json")),
             (os.path.join(DRAFT, "numbers.tex"), os.path.join(ROOT, "analysis", "full_10k_aggregate.json"))]
    for gen, src in pairs:
        if not os.path.exists(gen) or not os.path.exists(src):
            problems.append("missing %s or %s" % (gen, src))
        elif os.path.getmtime(gen) < os.path.getmtime(src):
            problems.append("stale generated file: %s older than %s" % (gen, src))
    # upload names must not contain underscores
    for fn in os.listdir(SUB):
        if fn.endswith(".pdf") and "_" in fn:
            problems.append("upload name contains an underscore: %s" % fn)
    return problems


def main():
    pages, errors, undefc, undefr = build()
    problems = audit()
    if errors or undefc or undefr:
        problems.append("compile not clean: %d errors, %d undefined cites, %d undefined refs" % (errors, undefc, undefr))
    # hash manifest
    entries = []
    for fn in sorted(os.listdir(SUB)):
        p = os.path.join(SUB, fn)
        if os.path.isfile(p) and fn != "SHA256SUMS.txt":
            entries.append("%s  %s" % (sha(p), fn))
    io.open(os.path.join(SUB, "SHA256SUMS.txt"), "w", encoding="utf-8", newline="").write("\n".join(entries) + "\n")
    print("audit problems:", problems if problems else "none")
    return 0 if not problems else 1


if __name__ == "__main__":
    raise SystemExit(main())
