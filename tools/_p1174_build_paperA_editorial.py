# -*- coding: utf-8 -*-
"""Rebuild every Paper A PDF after the 2026-10-17 editorial fixes, and audit the logs.

Builds, in paper合/:
  * main_nc.tex      - three pdflatex passes around one bibtex pass, plus convergence passes;
  * main_springer.tex- same;
  * cover_letter_nc.tex / cover_letter.tex / highlights_nc.tex - after the measured NC page
    count is written into the cover letters.

Per-document audit on the final log: LaTeX errors, undefined references, undefined citations,
Overfull hbox, "Float too large", rerun requests. Exit code 0 only if every count is zero and
the cover-letter page counts match the built PDF.

    python tools/_p1174_build_paperA_editorial.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PA = REPO / "paper合"
LOGS = REPO / "outputs" / "analysis"

FAILS: list[str] = []


def fail(msg: str) -> None:
    print("FAIL  " + msg)
    FAILS.append(msg)


def run(cmd: list[str], log: Path, cwd: Path) -> int:
    r = subprocess.run(cmd, cwd=str(cwd), capture_output=True)
    log.parent.mkdir(parents=True, exist_ok=True)
    log.write_bytes((r.stdout or b"") + (r.stderr or b""))
    return r.returncode


def pages(pdf: Path) -> int:
    import pypdf
    return len(pypdf.PdfReader(str(pdf)).pages)


def build_paper(tex: str) -> Path:
    stem = tex[:-4]
    n = 0
    for extra in range(1, 4):
        n = extra
        run(["pdflatex", "-interaction=nonstopmode", tex], LOGS / ("_pa_" + stem + "_pass%d.log" % extra), PA)
    run(["bibtex", stem], LOGS / ("_pa_" + stem + "_bibtex.log"), PA)
    for extra in range(4, 9):
        n = extra
        run(["pdflatex", "-interaction=nonstopmode", tex], LOGS / ("_pa_" + stem + "_pass%d.log" % extra), PA)
        txt = (LOGS / ("_pa_" + stem + "_pass%d.log" % extra)).read_text(encoding="utf-8", errors="replace")
        if "Rerun to get cross-references right" not in txt and "Label(s) may have changed" not in txt:
            break
    return LOGS / ("_pa_" + stem + "_pass%d.log" % n)


def build_simple(tex: str) -> Path:
    stem = tex[:-4]
    for extra in (1, 2):
        run(["pdflatex", "-interaction=nonstopmode", tex], LOGS / ("_pa_" + stem + "_pass%d.log" % extra), PA)
    return LOGS / ("_pa_" + stem + "_pass2.log")


def audit(name: str, log: Path, pdf: Path) -> None:
    txt = log.read_text(encoding="utf-8", errors="replace")
    errs = re.findall(r"^! .*$", txt, re.M)
    cites = re.findall(r"Warning: Citation `([^']+)' .*undefined", txt)
    refs = re.findall(r"Warning: Reference `([^']+)' .*undefined", txt)
    over = re.findall(r"Overfull \\hbox", txt)
    floats = re.findall(r"Float too large for page", txt)
    rerun = "Rerun to get" in txt
    p = pages(pdf) if pdf.exists() else -1
    print(f"  {name:<20} pages={p:<4} errors={len(errs)} undef-cites={len(cites)} "
          f"undef-refs={len(refs)} overfull={len(over)} floats={len(floats)} rerun={rerun}")
    if errs:
        for e in errs[:4]:
            print("     " + e[:150])
    if cites:
        print("     undefined citations: " + ", ".join(sorted(set(cites))[:6]))
    if refs:
        print("     undefined references: " + ", ".join(sorted(set(refs))[:6]))
    if errs or cites or refs or over or floats or rerun:
        fail(f"{name}: audit not clean (log {log.relative_to(REPO)})")


def patch_cover_pages(path: Path, n_pages: int) -> None:
    text = io.open(path, encoding="utf-8").read()
    pat = re.compile(r"The manuscript is (\d+) pages")
    hits = pat.findall(text)
    if len(hits) != 1:
        fail(f"{path.name}: expected exactly one 'The manuscript is N pages' statement, found {len(hits)}")
        return
    old = int(hits[0])
    new_text = pat.sub("The manuscript is %d pages" % n_pages, text)
    if old != n_pages:
        io.open(path, "w", encoding="utf-8", newline="").write(new_text)
        print(f"  {path.name}: manuscript page count {old} -> {n_pages}")
    else:
        print(f"  {path.name}: manuscript page count already {n_pages}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not a.apply:
        print("  (dry run; pass --apply to build)")
        return 0

    print("=" * 80)
    print("1. build main_nc.tex")
    nc_log = build_paper("main_nc.tex")
    nc_pdf = PA / "main_nc.pdf"
    audit("main_nc", nc_log, nc_pdf)
    nc_pages = pages(nc_pdf)

    print("=" * 80)
    print("2. build main_springer.tex")
    sp_log = build_paper("main_springer.tex")
    audit("main_springer", sp_log, PA / "main_springer.pdf")

    print("=" * 80)
    print("3. page count in the cover letters")
    patch_cover_pages(PA / "cover_letter_nc.tex", nc_pages)
    patch_cover_pages(PA / "cover_letter.tex", nc_pages)

    print("=" * 80)
    print("4. build cover letters and highlights")
    for tex, out in (("cover_letter_nc.tex", "cover_letter_nc.pdf"),
                     ("cover_letter.tex", "cover_letter.pdf"),
                     ("highlights_nc.tex", "highlights_nc.pdf")):
        log = build_simple(tex)
        audit(out[:-4], log, PA / out)

    print("=" * 80)
    print(f"RESULT: {len(FAILS)} failure(s); NC {nc_pages} pages, Springer {pages(PA / 'main_springer.pdf')} pages")
    return 0 if not FAILS else 1


if __name__ == "__main__":
    raise SystemExit(main())
