# -*- coding: utf-8 -*-
r"""P2-13: assemble a submission-ready package skeleton for a target venue, from the current local manuscripts.

The frozen packages under SUBMISSION/ are never touched; this script writes a new directory. It copies what exists, counts
pages, and writes a README that states the measured facts. A missing item is reported, not invented.

    python tools/_p1336_build_venue_package.py --manuscript paper_a1/main.pdf --title-page paper_a1/title_page.pdf \
        --cover-letter paper_a1/cover_letter_paa.pdf --figures paper_a1/figures --source paper_a1 \
        --venue PAA --out SUBMISSION/A1_next --apply

    # Paper A (Neurocomputing build):
    python tools/_p1336_build_venue_package.py --manuscript paper合/main_nc.pdf --abstract paper合/abstract_nc.pdf \
        --cover-letter paper合/cover_letter.pdf --highlights paper合/highlights_nc.pdf --source paper合 \
        --venue Neurocomputing --out SUBMISSION/PaperA_next
"""
from __future__ import annotations

import argparse
import glob
import io
import os
import shutil
import zipfile

from pypdf import PdfReader

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

README = """# {venue} submission package (built locally, {when})

| item | file | note |
|---|---|---|
| Manuscript | `{manuscript_name}` | {pages} pages |
| Title page | `{title_name}` | {title_note} |
| Cover letter | `{cover_name}` | {cover_note} |
| Abstract (separate) | `{abstract_name}` | {abstract_note} |
| Highlights | `{highlights_name}` | {highlights_note} |
| LaTeX source | `latex_source.zip` | {n_source} files |

Built by `tools/_p1336_build_venue_package.py`; page counts measured with pypdf. The submission packages under
`SUBMISSION/` and the frozen copies under `SUBMISSION/_frozen_submitted/` are untouched.
"""


def pages(p):
    return len(PdfReader(p).pages)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manuscript", required=True)
    ap.add_argument("--title-page", default=None)
    ap.add_argument("--cover-letter", default=None)
    ap.add_argument("--abstract", default=None)
    ap.add_argument("--highlights", default=None)
    ap.add_argument("--figures", default=None)
    ap.add_argument("--source", default=None, help="directory whose .tex files and figures are zipped")
    ap.add_argument("--venue", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    def abs_(rel):
        return os.path.join(REPO, rel) if rel else None

    items = [("manuscript", abs_(a.manuscript), "Manuscript.pdf")]
    for name, rel in (("title_page", a.title_page), ("cover_letter", a.cover_letter),
                      ("abstract", a.abstract), ("highlights", a.highlights)):
        if rel:
            items.append((name, abs_(rel), os.path.basename(rel)))
    out = abs_(a.out)
    print(f"  venue={a.venue} out={a.out} apply={a.apply}")
    for name, src, _ in items:
        print(f"   {name:14s} {'OK ' if src and os.path.exists(src) else 'MISS'} {src}")
        if src and not os.path.exists(src):
            print("     -> missing; not copied")
    if not a.apply:
        print("  (dry run)")
        return 0
    os.makedirs(out, exist_ok=True)
    facts = {}
    for name, src, target in items:
        if not src or not os.path.exists(src):
            facts[name] = None
            continue
        shutil.copyfile(src, os.path.join(out, target))
        facts[name] = {"file": target, "pages": pages(src), "bytes": os.path.getsize(src)}
    # source zip
    n_source = 0
    if a.source:
        src_dir = abs_(a.source)
        tex_files = sorted(glob.glob(os.path.join(src_dir, "*.tex")))
        bib = sorted(glob.glob(os.path.join(src_dir, "*.bib")))
        extra = []
        for sub in ("sections", "sections_full", "supplementary"):
            d = os.path.join(src_dir, sub)
            if os.path.isdir(d):
                for f in sorted(glob.glob(os.path.join(d, "**", "*.tex"), recursive=True)):
                    extra.append((f, os.path.relpath(f, src_dir).replace(os.sep, "/")))
        for pat in ("*.cls", "*.sty", "*.bst"):
            for f in sorted(glob.glob(os.path.join(src_dir, pat))):
                extra.append((f, os.path.basename(f)))
        figs = []
        if a.figures:
            fdir = abs_(a.figures)
            for ext in ("*.pdf", "*.png", "*.jpg", "*.jpeg", "*.eps"):
                for f in sorted(glob.glob(os.path.join(fdir, "**", ext), recursive=True)):
                    figs.append((f, "figures/" + os.path.relpath(f, fdir).replace(os.sep, "/")))
        zpath = os.path.join(out, "latex_source.zip")
        with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
            for f in tex_files + bib:
                z.write(f, os.path.basename(f))
                n_source += 1
            for f, arc in extra:
                z.write(f, arc)
                n_source += 1
            for f, arc in figs:
                z.write(f, arc)
                n_source += 1
        print(f"  latex_source.zip: {n_source} entries")
    import datetime
    readme = README.format(
        venue=a.venue, when=datetime.date.today().isoformat(),
        manuscript_name=facts["manuscript"]["file"] if facts.get("manuscript") else "missing",
        pages=facts["manuscript"]["pages"] if facts.get("manuscript") else "n/a",
        title_name=facts["title_page"]["file"] if facts.get("title_page") else "-",
        title_note=(f"{facts['title_page']['pages']} pages" if facts.get("title_page") else "not supplied"),
        cover_name=facts["cover_letter"]["file"] if facts.get("cover_letter") else "-",
        cover_note=(f"{facts['cover_letter']['pages']} pages" if facts.get("cover_letter") else "not supplied"),
        abstract_name=facts["abstract"]["file"] if facts.get("abstract") else "-",
        abstract_note=(f"{facts['abstract']['pages']} pages" if facts.get("abstract") else "not supplied"),
        highlights_name=facts["highlights"]["file"] if facts.get("highlights") else "-",
        highlights_note=(f"{facts['highlights']['pages']} pages" if facts.get("highlights") else "not supplied"),
        n_source=n_source,
    )
    io.open(os.path.join(out, "README.md"), "w", encoding="utf-8", newline="").write(readme)
    print("  wrote", os.path.relpath(os.path.join(out, "README.md"), REPO))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
