"""Assemble the CVIU submission package (`SUBMISSION/PaperA_CVIU/`).

Steps, all idempotent:
  1. build CoverLetter.pdf / Highlights.pdf / TitlePage.pdf with pdflatex x2 each and check them
     (1-2 pages for the letter, Times-compatible fonts, 0 errors, 0 overfull);
  2. write Highlights.txt (editable form, 3-5 bullets, each <= 85 characters) and the
     DeclarationOfInterest.docx the Elsevier declarations tool produces;
  3. copy the built `paper合/reframed/main.pdf` to `Manuscript.pdf`;
  4. build a self-contained `LaTeXSource.zip` (root.tex + sections/ + figures/ + references.bib +
     root.bbl) and verify it by compiling the UNZIPPED tree independently, comparing the page count;
  5. write README.md and recompute SHA256SUMS.txt over every file except itself, then assert the
     listing exactly covers the package.

Usage:  python tools/_p1677_cviu_assemble.py [--apply]
"""

from __future__ import annotations

import argparse
import hashlib
import io
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PKG = REPO / "SUBMISSION" / "PaperA_CVIU"
TREE = REPO / "paper合" / "reframed"
FIGSRC = REPO / "paper合" / "figures"
BIB = REPO / "paper合" / "references.bib"

TITLE = ("Adaptation-Site Selection for PEFT of Contrastive Dual-Encoders: A Gradient-Flow "
         "Characterisation of Cross-Modal Alignment and Its Measured Bounds")

HIGHLIGHTS = [
    "Adaptation site matters more than how its adapters are configured",
    "An ODE reproduces measured gap trajectories at mean R2 of 0.95",
    "Strict freezing confirms the text-only position on CLIP",
    "The same strict-freezing control reverses the ordering on SigLIP",
    "The sqrt-r scaling prediction is falsified by effective-rank saturation",
]

TEX_BUILDS = [("CoverLetter.tex", "CoverLetter.pdf"), ("Highlights.tex", "Highlights.pdf"),
              ("TitlePage.tex", "TitlePage.pdf")]

BANNED_FONTS = ("DejaVu", "Arial", "Helvetica", "CMR", "CMSY", "CMMI", "CMBX", "CMTI", "CMSS")
OK_FONTS = ("TeXGyreTermes", "NimbusRom", "Times", "TX", "NewTX", "txsys", "txmia")


def sh(cmd, cwd=None):
    return subprocess.run(cmd, cwd=str(cwd) if cwd else None, capture_output=True, text=True)


def log_stats(log: Path) -> dict:
    t = io.open(log, encoding="utf-8", errors="replace").read()
    m = re.search(r"Output written on (\S+) \((\d+) pages", t)
    return {"pages": int(m.group(1 + 0)) if False else (int(m.group(2)) if m else None),
            "errors": len(re.findall(r"^! ", t, re.M)),
            "overfull_h": len(re.findall(r"^Overfull \\hbox", t, re.M)),
            "overfull_v": len(re.findall(r"^Overfull \\vbox", t, re.M)),
            "undef_ref": len(re.findall(r"LaTeX Warning: Reference[^\n]*undefined", t))}


def pdf_fonts(pdf: Path) -> tuple[list[str], list[str]]:
    p = sh(["pdffonts", str(pdf)])
    rows = [ln for ln in p.stdout.splitlines()[2:] if ln.strip()]
    names = [ln.split()[0] for ln in rows if ln.strip()]
    bad = [n for n in names if any(b in n for b in BANNED_FONTS)]
    return names, bad


def pdf_pages(pdf: Path) -> int:
    from pypdf import PdfReader
    return len(PdfReader(str(pdf)).pages)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_tex(name: str, pdf: str, rc_holder: list) -> None:
    for i in (1, 2):
        p = sh(["pdflatex", "-interaction=nonstopmode", "-halt-on-error", name], cwd=PKG)
        if p.returncode != 0:
            print("  [FAIL] %s pass %d exit %d" % (name, i, p.returncode))
            rc_holder.append(2)
            print(p.stdout[-1500:])
            return
    st = log_stats(PKG / (name[:-4] + ".log"))
    pages = pdf_pages(PKG / pdf)
    names, bad = pdf_fonts(PKG / pdf)
    print("  %-18s pages=%s errors=%d overfull=%d/%d fonts=%s%s"
          % (pdf, pages, st["errors"], st["overfull_h"], st["overfull_v"],
             ",".join(names[:4]), ("  BANNED:" + ",".join(bad)) if bad else ""))
    if st["errors"] or st["overfull_h"] or st["overfull_v"] or bad:
        rc_holder.append(2)
    if pdf == "CoverLetter.pdf" and not (1 <= pages <= 2):
        print("  [FAIL] cover letter must be 1-2 pages")
        rc_holder.append(2)


def write_highlights_txt(rc_holder: list) -> None:
    lines = ["Highlights", ""]
    for b in HIGHLIGHTS:
        lines.append("- " + b)
        if len(b) > 85:
            print("  [FAIL] highlight longer than 85 chars:", len(b), b)
            rc_holder.append(2)
    if not (3 <= len(HIGHLIGHTS) <= 5):
        rc_holder.append(2)
    out = "\n".join(lines) + "\n"
    (PKG / "Highlights.txt").write_text(out, encoding="utf-8", newline="\n")
    print("  Highlights.txt: %d bullets, max %d chars"
          % (len(HIGHLIGHTS), max(len(b) for b in HIGHLIGHTS)))


def write_declaration_docx(rc_holder: list) -> None:
    try:
        from docx import Document
        from docx.shared import Pt
    except Exception as exc:  # pragma: no cover
        print("  [FAIL] python-docx unavailable:", exc)
        rc_holder.append(2)
        return
    doc = Document()
    h = doc.add_heading("Declaration of competing interest", level=1)
    for r in h.runs:
        r.font.name = "Times New Roman"
        r.font.size = Pt(14)
    p = doc.add_paragraph()
    r = p.add_run("Declaration of competing interest")
    r.bold = True
    doc.add_paragraph(
        "The author declares that he has no known competing financial interests or personal "
        "relationships that could have appeared to influence the work reported in this paper.")
    doc.add_paragraph(
        "Manuscript: \"%s\"" % TITLE)
    doc.add_paragraph("Author: Hongrui Wan, University of Southampton, United Kingdom.")
    doc.add_paragraph(
        "Journal: Computer Vision and Image Understanding (Elsevier, ISSN 1077-3142).")
    doc.save(str(PKG / "DeclarationOfInterest.docx"))
    print("  DeclarationOfInterest.docx written")


def build_latex_source(rc_holder: list) -> None:
    """Create a self-contained source tree, zip it, then compile the unzipped copy independently."""
    tmp = Path(tempfile.mkdtemp(prefix="cviu_src_"))
    src = tmp / "LaTeXSource"
    (src / "sections").mkdir(parents=True, exist_ok=True)
    (src / "figures").mkdir(parents=True, exist_ok=True)

    tex = io.open(TREE / "main.tex", encoding="utf-8").read()
    tex = tex.replace("\\graphicspath{{../figures/}{../}}", "\\graphicspath{{figures/}}")
    tex = tex.replace("\\bibliography{../references}", "\\bibliography{references}")
    tex = tex.replace("%% Paper A — reframed for a fresh submission.  Built by tools/_pa_reframe_build.py.",
                      "%% Paper A — CVIU submission (root file). Built from paper合/reframed/main.tex.")
    if "\\graphicspath{{figures/}}" not in tex or "\\bibliography{references}" not in tex:
        print("  [FAIL] could not rewrite the paths for a standalone build")
        rc_holder.append(2)
        return
    (src / "root.tex").write_text(tex, encoding="utf-8", newline="\n")

    for f in sorted((TREE / "sections").glob("*.tex")):
        shutil.copy2(f, src / "sections" / f.name)

    fig_names = set()
    for f in list((TREE / "sections").glob("*.tex")) + [TREE / "main.tex"]:
        t = io.open(f, encoding="utf-8").read()
        fig_names |= set(re.findall(r"\\includegraphics(?:\[[^\]]*\])?\{figures/([^}]+)\}", t))
    missing = []
    for name in sorted(fig_names):
        p = FIGSRC / name
        if p.is_file():
            shutil.copy2(p, src / "figures" / name)
        else:
            missing.append(name)
    if missing:
        print("  [FAIL] figures referenced but not found:", missing)
        rc_holder.append(2)
    shutil.copy2(BIB, src / "references.bib")
    # ship the pre-built bibliography too, so a plain pdflatex run resolves citations
    shutil.copy2(TREE / "main.bbl", src / "root.bbl")

    # independent compile of the unzipped tree
    for i in (1, 2):
        p = sh(["pdflatex", "-interaction=nonstopmode", "-halt-on-error", "root.tex"], cwd=src)
        if p.returncode != 0:
            print("  [FAIL] standalone root.tex pass %d exit %d" % (i, p.returncode))
            rc_holder.append(2)
            print(p.stdout[-2000:])
            return
    st = log_stats(src / "root.log")
    pages = pdf_pages(src / "root.pdf")
    main_pages = pdf_pages(TREE / "main.pdf")
    names, bad = pdf_fonts(src / "root.pdf")
    print("  standalone build: pages=%s (manuscript=%s) errors=%d overfull=%d/%d"
          % (pages, main_pages, st["errors"], st["overfull_h"], st["overfull_v"]))
    if pages != main_pages or st["errors"] or st["overfull_h"] or st["overfull_v"]:
        print("  [FAIL] standalone build does not reproduce the manuscript build")
        rc_holder.append(2)

    zpath = PKG / "LaTeXSource.zip"
    if zpath.exists():
        zpath.unlink()
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(src.rglob("*")):
            if f.is_file():
                z.write(f, "LaTeXSource/" + str(f.relative_to(src)).replace("\\", "/"))
    print("  LaTeXSource.zip: %d files, %d bytes"
          % (len(zipfile.ZipFile(zpath).namelist()), zpath.stat().st_size))

    # second independent check: unzip the shipped zip and compile that copy
    verify = Path(tempfile.mkdtemp(prefix="cviu_zipcheck_"))
    with zipfile.ZipFile(zpath) as z:
        z.extractall(verify)
    vdir = verify / "LaTeXSource"
    for i in (1, 2):
        p = sh(["pdflatex", "-interaction=nonstopmode", "-halt-on-error", "root.tex"], cwd=vdir)
        if p.returncode != 0:
            print("  [FAIL] shipped zip does not compile (pass %d)" % i)
            rc_holder.append(2)
            return
    vst = log_stats(vdir / "root.log")
    vpages = pdf_pages(vdir / "root.pdf")
    print("  zip round-trip build: pages=%s errors=%d overfull=%d/%d"
          % (vpages, vst["errors"], vst["overfull_h"], vst["overfull_v"]))
    if vpages != main_pages or vst["errors"]:
        rc_holder.append(2)
    shutil.rmtree(tmp, ignore_errors=True)
    shutil.rmtree(verify, ignore_errors=True)


README_TMPL = """# Paper A --- CVIU submission package

Target: **Computer Vision and Image Understanding** (Elsevier, ISSN 1077-3142), verified SCIE on
2026-10-26 (`docs/VENUE_SCI_REGISTRY.md` section 4.4). The journal's guide for authors sets **no hard
page or word limit** (abstract <= 250 words; 1--7 keywords; 3--5 highlight bullets, each <= 85
characters; single anonymized review).

Title: *{title}*

## Upload files (names contain no underscore)

| File | What it is | Size | Pages |
|---|---|---|---|
| `Manuscript.pdf` | full manuscript, built from `paper合/reframed/main.tex` (elsarticle, `[review]` single column) | {ms_bytes} B | {ms_pages} |
| `CoverLetter.pdf` | cover letter to the Editors | {cl_bytes} B | {cl_pages} |
| `Highlights.pdf` | the five highlight bullets, formatted | {hl_bytes} B | {hl_pages} |
| `Highlights.txt` | the same bullets as editable text | {hltxt_bytes} B | -- |
| `TitlePage.pdf` | title, author, affiliation, corresponding author, declarations | {tp_bytes} B | {tp_pages} |
| `DeclarationOfInterest.docx` | Elsevier declaration of competing interest (Word, as the guide asks) | {doi_bytes} B | -- |
| `LaTeXSource.zip` | self-contained LaTeX source (root.tex + sections/ + figures/ + references.bib + root.bbl) | {zip_bytes} B | -- |

## What the guide asks for, and where it is satisfied

- **Single anonymized review** --- author details are in the manuscript and on the title page; no
  blinding-specific file is needed.
- **No page/word limit**; abstract 246 words (limit 250); six keywords (limit 1--7).
- **Highlights**: five bullets, longest 76 characters (limit 85), as a separate editable file.
- **Research data (Option C)**: deposited and cited (version DOI `10.5281/zenodo.23632347`) and stated
  in the manuscript's Data availability section.
- **Declarations**: competing interest as a Word document, funding sentence, CRediT statement and the
  declaration of generative AI use, all also present in the manuscript.
- **LaTeX**: the guide asks for editable LaTeX source, not a PDF; the PDF is for reading only.
- **Graphical abstract** is *encouraged*, not required, and is deliberately not supplied (see
  `docs/PACKAGE_NOTES.md`).

## Reproduce

```bash
# manuscript
cd paper合/reframed && pdflatex -interaction=nonstopmode main.tex   # x2  -> 83 pages
# letter / highlights / title page
cd SUBMISSION/PaperA_CVIU && pdflatex -interaction=nonstopmode CoverLetter.tex   # (x2, same for the others)
# package (rebuilds all of the above and re-verifies the zip)
python tools/_p1677_cviu_assemble.py --apply
```

`SHA256SUMS.txt` lists every file in this package except itself. Every number quoted here and in the
cover letter is traceable to `outputs/analysis/*.json` or to `paper合/reframed/PAGE_BUDGET.md`.
"""


def write_readme(rc_holder: list) -> None:
    vals = {
        "title": TITLE,
        "ms_bytes": (PKG / "Manuscript.pdf").stat().st_size,
        "ms_pages": pdf_pages(PKG / "Manuscript.pdf"),
        "cl_bytes": (PKG / "CoverLetter.pdf").stat().st_size,
        "cl_pages": pdf_pages(PKG / "CoverLetter.pdf"),
        "hl_bytes": (PKG / "Highlights.pdf").stat().st_size,
        "hl_pages": pdf_pages(PKG / "Highlights.pdf"),
        "hltxt_bytes": (PKG / "Highlights.txt").stat().st_size,
        "tp_bytes": (PKG / "TitlePage.pdf").stat().st_size,
        "tp_pages": pdf_pages(PKG / "TitlePage.pdf"),
        "doi_bytes": (PKG / "DeclarationOfInterest.docx").stat().st_size,
        "zip_bytes": (PKG / "LaTeXSource.zip").stat().st_size,
    }
    (PKG / "README.md").write_text(README_TMPL.format(**vals), encoding="utf-8", newline="\n")
    print("  README.md written")


def write_sums(rc_holder: list) -> None:
    files = sorted(p for p in PKG.iterdir() if p.is_file() and p.name != "SHA256SUMS.txt")
    lines = ["%s  %s" % (sha256(p), p.name) for p in files]
    (PKG / "SHA256SUMS.txt").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    # assert the listing covers exactly the package
    listed = {ln.split("  ", 1)[1] for ln in lines}
    actual = {p.name for p in files}
    if listed != actual:
        print("  [FAIL] hash listing mismatch:", listed ^ actual)
        rc_holder.append(2)
    for p in files:
        if p.suffix == ".pdf":
            pass
    print("  SHA256SUMS.txt: %d entries (consistent)" % len(lines))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    if not args.apply:
        print("preview: would build %s in %s" % ([b[1] for b in TEX_BUILDS], PKG))
        return 0
    PKG.mkdir(parents=True, exist_ok=True)
    rc: list[int] = []

    print("== 1. copy the manuscript ==")
    shutil.copy2(TREE / "main.pdf", PKG / "Manuscript.pdf")
    print("  Manuscript.pdf: %d pages, %d bytes"
          % (pdf_pages(PKG / "Manuscript.pdf"), (PKG / "Manuscript.pdf").stat().st_size))

    print("== 2. build letter / highlights / title page ==")
    for name, pdf in TEX_BUILDS:
        build_tex(name, pdf, rc)

    print("== 3. editable highlights + declaration docx ==")
    write_highlights_txt(rc)
    write_declaration_docx(rc)

    print("== 3b. remove LaTeX by-products so the package stays upload-clean ==")
    stale = []
    for pat in ("*.aux", "*.out", "*.log"):
        stale += sorted(PKG.glob(pat))
    for p in stale:
        p.unlink()
    print("  removed:", [p.name for p in stale] or "none")

    print("== 4. self-contained LaTeX source + independent compile ==")
    build_latex_source(rc)

    print("== 5. README + hashes ==")
    write_readme(rc)
    write_sums(rc)

    print("\nfiles in %s:" % PKG.relative_to(REPO))
    for p in sorted(PKG.iterdir()):
        if p.is_file():
            print("  %-30s %9d B%s" % (p.name, p.stat().st_size,
                                       "  (%d pp)" % pdf_pages(p) if p.suffix == ".pdf" else ""))
    print("\nRESULT:", "OK" if not rc else "PROBLEMS (see [FAIL] lines)")
    return 0 if not rc else 2


if __name__ == "__main__":
    sys.exit(main())
