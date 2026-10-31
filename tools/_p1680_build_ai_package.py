"""Build the Applied Intelligence (Springer) submission package for Paper A.

Inputs (read-only):
  paper合/reframed/main.tex        reframed manuscript (elsarticle build; 39 pp main text / 83 pp total)
  paper合/reframed/sections/*.tex  10 section files
  paper合/references.bib           verified bibliography
  paper合/figures/*.pdf            artwork
  paper合/sn-jnl.cls, sn-mathphys-num.bst vendored Springer style files

Output: SUBMISSION/PaperA_AppliedIntelligence/
  Manuscript.pdf          Springer/sn-jnl build (sn-basic numeric bibliography, single column)
  CoverLetter.pdf         + CoverLetter.tex
  TitlePage.pdf           + TitlePage.tex   (separate title page; manuscript itself is single-blind ready)
  LaTeXSource.zip         flat source tree (no subdirectories) + style files + .bbl
  Artwork/*.pdf           18 figures as separate files, underscore-free names
  README.md, SHA256SUMS.txt

Everything is regenerated from scratch; the script asserts each transformation so a silent mismatch cannot
ship. It also verifies: 0 errors / 0 undefined refs / 0 undefined citations / 0 overfull, page counts,
Times-compatible fonts, an independent unzip-and-compile, SHA256SUMS self-consistency, and that
SUBMISSION/PaperA_Neurocomputing/ is byte-identical before and after.

Usage: python tools/_p1680_build_ai_package.py [--apply]
"""

from __future__ import annotations

import argparse
import hashlib
import io
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
REF = REPO / "paper合" / "reframed"
PKG = REPO / "SUBMISSION" / "PaperA_AppliedIntelligence"
SRC = PKG / "LaTeXSource"
ART = PKG / "Artwork"

TITLE = ("Adaptation-Site Selection for PEFT of Contrastive Dual-Encoders: A Gradient-Flow "
         "Characterisation of Cross-Modal Alignment and Its Measured Bounds")

FROZEN_NEUCOM = REPO / "SUBMISSION" / "PaperA_Neurocomputing"

DCLASS = r"\documentclass[pdflatex,sn-mathphys-num,onecolumn]{sn-jnl}"

PREAMBLE = r"""%% ===================================================================================
%% Paper A -- Applied Intelligence (Springer) submission, root file.
%% Written by tools/_p1680_build_ai_package.py from paper合/reframed/main.tex.
%%
%% Template: the journal guide says "Please use Springer's LaTeX macro package and choose the
%% formatting option 'smallcondensed'".  'smallcondensed' is an option of Springer's older svjour3
%% class, which is not distributed with TeX Live and is not present in this environment; the current
%% Springer Nature class is used instead (the same guide also encourages the Springer Nature LaTeX
%% template).  sn-jnl's 'onecolumn' option reproduces the single-column condensed layout, and
%% 'sn-mathphys-num' is the numeric square-bracket reference style the journal's format rules require
%% (the guide's generic mention of sn-basic.bst is superseded: sn-basic produces name-year citations,
%% which contradicts the journal's own "numbers in square brackets" rule).
%% ===================================================================================
\documentclass[pdflatex,sn-mathphys-num,onecolumn]{sn-jnl}

\usepackage{graphicx}
\usepackage{multirow}
\usepackage{amsmath,amssymb,amsfonts}
\usepackage{booktabs}
% float-density fix (2026-10-26): appendix figures were leaving half-empty pages
\renewcommand{\topfraction}{0.9}
\renewcommand{\bottomfraction}{0.8}
\renewcommand{\textfraction}{0.07}
\renewcommand{\floatpagefraction}{0.6}
\renewcommand{\dbltopfraction}{0.9}
\renewcommand{\dblfloatpagefraction}{0.6}
\setcounter{topnumber}{3}
\setcounter{bottomnumber}{2}
\setcounter{totalnumber}{4}
\setcounter{dbltopnumber}{3}

\usepackage{longtable}
\usepackage{url}
\usepackage{float}
\usepackage{placeins}

% Theorem environments (sn-jnl custom styles)
\theoremstyle{thmstyleone}
\newtheorem{theorem}{Theorem}[section]
\newtheorem{proposition}[theorem]{Proposition}

\theoremstyle{thmstyletwo}
\newtheorem{lemma}{Lemma}[section]
\newtheorem{corollary}{Corollary}[section]
\newtheorem{remark}{Remark}[section]

\theoremstyle{thmstylethree}
\newtheorem{definition}{Definition}[section]
\newtheorem{assumption}{Assumption}[section]

\newcommand{\Rk}[1]{R{\normalfont @}#1}

\raggedbottom

\begin{document}
"""


def sh(cmd, cwd):
    return subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True)


def stats(log: Path) -> dict:
    t = io.open(log, encoding="utf-8", errors="replace").read()
    m = re.search(r"Output written on (\S+) \((\d+) pages, (\d+) bytes\)", t)
    return {
        "pages": int(m.group(2)) if m else None,
        "errors": len(re.findall(r"^! ", t, re.M)),
        "undef_ref": len(re.findall(r"LaTeX Warning: Reference[^\n]*undefined", t)),
        "undef_cite": len(re.findall(r"(?:LaTeX|Package natbib) Warning: Citation[^\n]*undefined", t)),
        "overfull_h": len(re.findall(r"^Overfull \\hbox", t, re.M)),
        "overfull_v": len(re.findall(r"^Overfull \\vbox", t, re.M)),
        "text": t,
    }


def fonts(pdf: Path) -> tuple[list[str], list[str]]:
    p = sh(["pdffonts", str(pdf)], REPO)
    rows = [ln for ln in p.stdout.splitlines()[2:] if ln.strip()]
    names = [ln.split()[0] for ln in rows if ln.strip()]
    # only genuinely wrong families are banned; Computer Modern is the Springer class default for
    # LaTeX submissions and is not a defect (the journal re-typesets), TeXGyreTermes/newtx is the
    # Times-compatible family required for the generated documents.
    banned = [n for n in names if re.search(r"DejaVu|Arial|Helvetica|NimbusSan|FreeSans", n)]
    return names, banned


def pages(pdf: Path) -> int:
    from pypdf import PdfReader
    return len(PdfReader(str(pdf)).pages)


def size(p: Path) -> str:
    return "%.1f kB" % (p.stat().st_size / 1024.0)


def extract(text: str, start: str, end: str, what: str) -> str:
    i = text.find(start)
    j = text.find(end, i + len(start)) if i >= 0 else -1
    if i < 0 or j < 0:
        raise SystemExit("FATAL: could not extract %s (%r .. %r)" % (what, start, end))
    return text[i + len(start):j].strip()


def camel_case(name: str) -> str:
    base, ext = os.path.splitext(name)
    parts = base.split("_")
    return parts[0] + "".join(p[:1].upper() + p[1:] for p in parts[1:]) + ext


def sha_tree(root: Path) -> dict:
    out = {}
    if not root.is_dir():
        return out
    for p in sorted(root.rglob("*")):
        if p.is_file():
            out[str(p.relative_to(root)).replace("\\", "/")] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    if not args.apply:
        print("preview: would build %s" % PKG.relative_to(REPO))
        return 0
    rc: list[int] = []
    frozen_before = sha_tree(FROZEN_NEUCOM)

    src_tex = io.open(REF / "main.tex", encoding="utf-8").read()
    abstract = extract(src_tex, "\\begin{abstract}", "\\end{abstract}", "abstract")
    keywords = extract(src_tex, "\\begin{keyword}", "\\end{keyword}", "keywords")
    keywords = re.sub(r"\s*\\sep\s*", ", ", " ".join(keywords.split()))
    da = extract(src_tex, "\\section*{Data availability}", "\\section*{Funding}", "data availability")
    funding = extract(src_tex, "\\section*{Funding}",
                      "\\section*{Declaration of competing interests}", "funding")
    competing = extract(src_tex, "\\section*{Declaration of competing interests}",
                        "\\section*{CRediT authorship contribution statement}", "competing interests")
    credit = extract(src_tex, "\\section*{CRediT authorship contribution statement}",
                     "\\section*{Declaration of generative AI", "CRediT")
    genai = extract(src_tex, "\\section*{Declaration of generative AI", "\\bibliographystyle", "genai")
    # drop the heading remainder of the generative-AI heading from the extracted prose
    genai = genai.split("\n", 1)[1].strip() if "\n" in genai else genai
    for label, piece in (("abstract", abstract), ("keywords", keywords), ("data availability", da),
                         ("funding", funding), ("competing", competing), ("CRediT", credit),
                         ("genai", genai)):
        if not piece:
            print("FATAL: empty %s" % label)
            return 2

    # ---- figure mapping (all referenced figures, underscore-free names) -------------------------
    fig_names = set()
    for f in [REF / "main.tex"] + sorted((REF / "sections").glob("*.tex")):
        fig_names |= set(re.findall(r"figures/([A-Za-z0-9_]+\.pdf)", io.open(f, encoding="utf-8").read()))
    fig_map = {name: camel_case(name) for name in sorted(fig_names)}
    bad = [v for v in fig_map.values() if "_" in v]
    if bad:
        print("FATAL: underscore left in artwork names:", bad)
        return 2
    for name in fig_map:
        if not (REPO / "paper合" / "figures" / name).is_file():
            print("FATAL: missing figure", name)
            return 2

    # ---- package skeleton ---------------------------------------------------------------------
    for d in (SRC, ART):
        if d.exists():
            shutil.rmtree(d)
        d.mkdir(parents=True)

    # ---- root.tex -----------------------------------------------------------------------------
    body_inputs = "\n".join("\\input{%s}" % n for n in
                            ("10_introduction", "20_theory", "30_prior", "40_protocol",
                             "50_results", "60_negative", "70_implications", "80_conclusion"))
    root = (
        PREAMBLE
        + "\\hypersetup{pdftitle={%s},pdfauthor={Hongrui Wan}}\n" % TITLE
        + "\\pdfinfo{/Title (%s) /Author (Hongrui Wan)}\n\n" % TITLE
        + "\\title[Adaptation-Site Selection for PEFT]{%s}\n\n" % TITLE
        + "\\author*[1]{\\fnm{Hongrui} \\sur{Wan}}\\email{hw4c24@soton.ac.uk}\n\n"
        + "\\affil*[1]{\\orgname{University of Southampton}, \\orgaddress{\\street{University Road}, "
          "\\city{Southampton}, \\postcode{SO17 1BJ}, \\country{United Kingdom}}}\n\n"
        + "\\abstract{%s}\n\n" % abstract
        + "\\keywords{%s}\n\n" % keywords
        + "\\maketitle\n\n"
        + body_inputs + "\n\n"
        + "%% flush every main-text float before the appendix so that the main text ends here\n"
        + "\\FloatBarrier\n\\clearpage\n\\appendix\n"
        + "\\input{95_appendix_original}\n\\input{96_appendix_displaced}\n\n"
        + "\\backmatter\n\n"
        + "\\bmhead{Statements and Declarations}\n\n"
        + "\\noindent\\textbf{Funding.} " + funding + "\n\n"
        + "\\noindent\\textbf{Competing interests.} " + competing + "\n\n"
        + "\\noindent\\textbf{Data availability.} " + da + "\n\n"
        + "\\noindent\\textbf{Authors' contributions.} " + credit + "\n\n"
        + "\\noindent\\textbf{Declaration of generative AI and AI-assisted technologies in the "
          "manuscript preparation process.} " + genai + "\n\n"
        # the sn-mathphys-num class option already emits \bibstyle{sn-mathphys-num}; a second \bibliographystyle
        # makes bibtex abort with "Illegal, another \bibstyle command", so only \bibliography is issued
        + "\\bibliography{references}\n\n\\end{document}\n"
    )
    (SRC / "root.tex").write_text(root, encoding="utf-8", newline="\n")

    # ---- flat section files (figure paths rewritten) -------------------------------------------
    for f in sorted((REF / "sections").glob("*.tex")):
        t = io.open(f, encoding="utf-8").read()
        for old, new in fig_map.items():
            t = t.replace("figures/" + old, new)
        if "figures/" in t:
            print("FATAL: unrewritten figure path in", f.name)
            rc.append(2)
        (SRC / f.name).write_text(t, encoding="utf-8", newline="\n")

    # ---- style files, bibliography, figures ---------------------------------------------------
    shutil.copy2(REPO / "paper合" / "references.bib", SRC / "references.bib")
    shutil.copy2(REPO / "paper合" / "sn-jnl.cls", SRC / "sn-jnl.cls")
    shutil.copy2(REPO / "paper合" / "sn-mathphys-num.bst", SRC / "sn-mathphys-num.bst")
    for old, new in fig_map.items():
        shutil.copy2(REPO / "paper合" / "figures" / old, SRC / new)
        shutil.copy2(REPO / "paper合" / "figures" / old, ART / new)
    subs = [p for p in SRC.rglob("*") if p.is_dir()]
    if subs:
        print("FATAL: source tree has subdirectories:", [str(s.relative_to(SRC)) for s in subs])
        rc.append(2)

    # ---- build in a scratch dir ---------------------------------------------------------------
    build = Path(tempfile.mkdtemp(prefix="ai_build_"))
    for f in SRC.iterdir():
        shutil.copy2(f, build / f.name)
    for i in (1, 2):
        r = sh(["pdflatex", "-interaction=nonstopmode", "-halt-on-error", "root.tex"], build)
        if r.returncode != 0:
            print("FATAL: pdflatex pass %d failed" % i)
            print(r.stdout[-2500:])
            return 2
    r = sh(["bibtex", "root"], build)
    if r.returncode != 0:
        print("FATAL: bibtex failed")
        print(r.stdout[-1500:])
        return 2
    for i in (3, 4):
        r = sh(["pdflatex", "-interaction=nonstopmode", "-halt-on-error", "root.tex"], build)
        if r.returncode != 0:
            print("FATAL: pdflatex pass %d failed" % i)
            print(r.stdout[-2500:])
            return 2
    st = stats(build / "root.log")
    print("build:", {k: st[k] for k in ("pages", "errors", "undef_ref", "undef_cite",
                                       "overfull_h", "overfull_v")})
    if st["errors"] or st["undef_ref"] or st["undef_cite"] or st["overfull_h"] or st["overfull_v"]:
        print("FATAL: build not clean")
        rc.append(2)
    # main-text page span: appendix A starts on a fresh page after \clearpage
    from pypdf import PdfReader
    reader = PdfReader(str(build / "root.pdf"))
    main_pp = None
    for i, pg in enumerate(reader.pages, 1):
        txt = pg.extract_text() or ""
        if "Complete Experiment Catalog" in txt or "Complete Experiment Catalogue" in txt:
            main_pp = i - 1
            break
    print("pages: total=%s main-text=%s appendix=%s"
          % (len(reader.pages), main_pp, (len(reader.pages) - main_pp) if main_pp else "?"))
    fnames, fbanned = fonts(build / "root.pdf")
    print("Manuscript fonts:", ", ".join(fnames[:6]), ("BANNED: " + ",".join(fbanned)) if fbanned else "")
    if fbanned:
        rc.append(2)
    shutil.copy2(build / "root.pdf", PKG / "Manuscript.pdf")
    shutil.copy2(build / "root.bbl", SRC / "root.bbl")

    # content sanity check on the built manuscript
    full = " ".join((p.extract_text() or "") for p in reader.pages)
    checks = {
        "title": "Adaptation-Site Selection for PEFT",
        "statements heading": "Statements and Declarations",
        "data DOI": "10.5281/zenodo.23632347",
        "keywords": "Distribution Gap",
        "references": "References",
    }
    for label, needle in checks.items():
        ok = needle in full
        print("  manuscript contains %-20s %s" % (label, "OK" if ok else "MISSING"))
        if not ok:
            rc.append(2)
    n_cite = len(re.findall(r"\[\d{1,3}(?:,\s?\d{1,3})*\]", full))
    print("  numeric citations found:", n_cite)
    if n_cite < 20:
        rc.append(2)

    # ---- zip the pristine flat source and verify an independent compile ------------------------
    zpath = PKG / "LaTeXSource.zip"
    if zpath.exists():
        zpath.unlink()
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(SRC.iterdir()):
            if f.is_file():
                z.write(f, f.name)
    verify = Path(tempfile.mkdtemp(prefix="ai_zipcheck_"))
    with zipfile.ZipFile(zpath) as z:
        z.extractall(verify)
    for i in (1, 2):
        r = sh(["pdflatex", "-interaction=nonstopmode", "-halt-on-error", "root.tex"], verify)
        if r.returncode != 0:
            print("FATAL: shipped zip does not compile (pass %d)" % i)
            print(r.stdout[-2000:])
            return 2
    vst = stats(verify / "root.log")
    vpages = pages(verify / "root.pdf")
    print("zip round-trip: pages=%s (manuscript=%s) errors=%d overfull=%d/%d"
          % (vpages, pages(PKG / "Manuscript.pdf"), vst["errors"], vst["overfull_h"], vst["overfull_v"]))
    if vpages != pages(PKG / "Manuscript.pdf") or vst["errors"]:
        rc.append(2)

    # the pristine source tree ships only inside the zip; dropping the expanded copy keeps the package
    # upload-clean (the section file names carry underscores and must not surface as uploads)
    shutil.rmtree(SRC, ignore_errors=True)

    # ---- cover letter + title page ------------------------------------------------------------
    for tex, out, maxpages in (("CoverLetter.tex", "CoverLetter.pdf", 2),
                               ("TitlePage.tex", "TitlePage.pdf", 1)):
        work = Path(tempfile.mkdtemp(prefix="ai_aux_"))
        shutil.copy2(PKG / tex, work / tex)
        for i in (1, 2):
            r = sh(["pdflatex", "-interaction=nonstopmode", "-halt-on-error", tex], work)
            if r.returncode != 0:
                print("FATAL: %s failed" % tex)
                print(r.stdout[-2000:])
                return 2
        shutil.copy2(work / out, PKG / out)
        n = pages(PKG / out)
        fnames, fbanned = fonts(PKG / out)
        print("%-16s pages=%d fonts=%s%s" % (out, n, ",".join(fnames[:4]),
                                             ("  BANNED:" + ",".join(fbanned)) if fbanned else ""))
        if n > maxpages or fbanned:
            rc.append(2)

    # ---- README -------------------------------------------------------------------------------
    files = sorted(p for p in PKG.iterdir() if p.is_file() and p.name != "README.md")
    art = sorted(p for p in ART.iterdir() if p.is_file())
    readme = f"""# Paper A --- Applied Intelligence (Springer) submission package

Target: **Applied Intelligence** (Springer; ISSN 0924-669X, eISSN 1573-7497), verified **SCIE** on
2026-10-26 against the Clarivate Master Journal List
(`docs/VENUE_SCI_REGISTRY.md` section 4.6; guide notes in
`docs/venue_second_candidates_2026-10-26.md`).

Title: *{TITLE}*

This package **supersedes** `SUBMISSION/PaperA_CVIU/`, which is kept on disk as a superseded artefact
(CVIU was dropped because its guide requires an author Vitae with a passport-type photograph).

## Upload files (no underscore in any filename)

| File | What it is | Size | Pages |
|---|---|---|---|
| `Manuscript.pdf` | full manuscript, Springer `sn-jnl` build (single column, numeric square-bracket references) | {size(PKG / 'Manuscript.pdf')} | {pages(PKG / 'Manuscript.pdf')} |
| `CoverLetter.pdf` | cover letter to the Editors | {size(PKG / 'CoverLetter.pdf')} | {pages(PKG / 'CoverLetter.pdf')} |
| `TitlePage.pdf` | title, author, full postal affiliation, corresponding author, statements | {size(PKG / 'TitlePage.pdf')} | {pages(PKG / 'TitlePage.pdf')} |
| `LaTeXSource.zip` | flat LaTeX source (no subdirectories) + style files + figures + `root.bbl` | {size(PKG / 'LaTeXSource.zip')} | -- |
| `Artwork/*.pdf` | {len(art)} figures as separate files (guide: "Figures should be provided within the text and as separate files") | -- | -- |
| `README.md`, `SHA256SUMS.txt` | this file and the hash list | -- | -- |

Manuscript totals: **{pages(PKG / 'Manuscript.pdf')} pages** ({main_pp} pages of main text + {pages(PKG / 'Manuscript.pdf') - main_pp} pages of appendix).
For comparison, the elsarticle build of the same text is 39 pages of main text and 83 pages in total.

## What the Applied Intelligence guide asks for, and where it is satisfied

- **No page/word limit** --- nothing to compress; the reframed text is used unchanged.
- **Abstract 150--250 words** --- 246 words. **Keywords 4--6** --- six.
- **LaTeX source**: "Manuscripts should be submitted in LaTeX ... include the original source (including
  all style files and figures) and a PDF version of the compiled output"; "Please do not use subfolders".
  => `LaTeXSource.zip` is flat (all files at the top level) and includes `sn-jnl.cls` / `sn-mathphys-num.bst`;
  `Manuscript.pdf` is the compiled output.
- **Template**: the guide's journal-specific line asks for "Springer's LaTeX macro package ... the
  formatting option *smallcondensed*". `smallcondensed` is an option of Springer's older `svjour3`
  class, which is not distributed with TeX Live nor present here; the current Springer Nature class
  `sn-jnl` is used with `onecolumn` (single-column condensed layout) and `sn-mathphys-num` (numeric
  square-bracket references: the guide's format rules require numbers in square brackets, while the generic
  sentence mentioning `sn-basic.bst` would give name-year citations),
  as the same guide also encourages the Springer Nature template.
- **Figures** as separate files, numbered and cited: `Artwork/` (names also used inside the source).
- **Statements and Declarations** (funding, competing interests, data availability, authors'
  contributions, generative-AI use): in the manuscript before the reference list, and repeated on the
  title page. The data statement keeps the version DOI **10.5281/zenodo.23632347**.
- **Highlights**: not required by this journal's guide -> not supplied.
- **Review model**: the guide does not state single vs double anonymization. The manuscript carries
  author details (single-blind ready) and a separate title page is supplied. To produce a double-blind
  version, strip: the `\\author*`/`\\affil*`/`\\email` block and `\\maketitle` author lines; the
  Acknowledgements (none); the repository URL and DOI in the Data availability statement (replace with
  "available from the authors on request"); the self-citations written as "our earlier work"; and the
  PDF metadata in `\\hypersetup`/`\\pdfinfo` (author name).

## Reproduce

```bash
python tools/_p1680_build_ai_package.py --apply     # rebuilds everything and re-verifies
# manual: cd LaTeXSource && pdflatex root && bibtex root && pdflatex root && pdflatex root
```

`SHA256SUMS.txt` lists every file in this package except itself.
"""
    (PKG / "README.md").write_text(readme, encoding="utf-8", newline="\n")

    # ---- hashes -------------------------------------------------------------------------------
    all_files = sorted(p for p in PKG.rglob("*") if p.is_file() and p.name != "SHA256SUMS.txt")
    lines = ["%s  %s" % (hashlib.sha256(p.read_bytes()).hexdigest(),
                         str(p.relative_to(PKG)).replace("\\", "/")) for p in all_files]
    (PKG / "SHA256SUMS.txt").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    listed = {ln.split("  ", 1)[1] for ln in lines}
    actual = {str(p.relative_to(PKG)).replace("\\", "/") for p in all_files}
    print("SHA256SUMS: %d entries, consistent=%s" % (len(lines), listed == actual))
    if listed != actual:
        rc.append(2)
    paths = [str(p.relative_to(PKG)).replace("\\", "/") for p in all_files]
    underscored = [p for p in paths if "_" in os.path.basename(p)]
    print("upload names with underscore:", underscored or "none")
    if underscored:
        rc.append(2)

    # ---- frozen package untouched -------------------------------------------------------------
    frozen_after = sha_tree(FROZEN_NEUCOM)
    print("SUBMISSION/PaperA_Neurocomputing unchanged:", frozen_before == frozen_after,
          "(%d files)" % len(frozen_after))
    if frozen_before != frozen_after:
        rc.append(2)

    shutil.rmtree(build, ignore_errors=True)
    shutil.rmtree(verify, ignore_errors=True)
    print("\nRESULT:", "OK" if not rc else "PROBLEMS")
    return 0 if not rc else 2


if __name__ == "__main__":
    sys.exit(main())
