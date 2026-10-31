# -*- coding: utf-8 -*-
r"""Staged package build check: every venue package's LaTeX source must compile standalone.

For each SUBMISSION/_venue_builds package, the latex_source.zip is extracted into a temporary directory, the main document
is compiled (pdflatex twice), and the result is compared with the shipped Manuscript.pdf: errors in the log, page count,
undefined references/citations, overfull boxes.

Output: outputs/analysis/staged_package_check.json

    python tools/_p1444_staged_package_check.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import os
import re
import shutil
import subprocess
import tempfile
import zipfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.join(REPO, "SUBMISSION", "_venue_builds")
OUT = os.path.join(REPO, "outputs", "analysis", "staged_package_check.json")


def find_main(d, want_pages=None):
    cands = []
    for f in os.listdir(d):
        if f.endswith(".tex"):
            p = os.path.join(d, f)
            t = io.open(p, encoding="utf-8", errors="ignore").read()
            if "\\documentclass" in t and "\\begin{document}" in t:
                cands.append(f)
    cands.sort(key=lambda x: (0 if x.startswith("main") else 1, len(x)))
    if want_pages is None:
        return cands[0] if cands else None
    best = cands[0] if cands else None
    for f in cands[:3]:
        errs, undef, over, pages, _ = compile_pdf(d, f)
        if pages is not None and pages == want_pages:
            return f
    return best


def compile_pdf(d, tex, passes=2):
    log = None
    main_src = io.open(os.path.join(d, tex), encoding="utf-8", errors="ignore").read()
    r = subprocess.run(["pdflatex", "-interaction=nonstopmode", tex], cwd=d, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=900)
    log = (r.stdout or "") + "\n" + (r.stderr or "")
    if "\\bibliography{" in main_src:
        stem = tex[:-4]
        rb = subprocess.run(["bibtex", stem], cwd=d, capture_output=True, text=True, encoding="utf-8",
                            errors="replace", timeout=300)
        log += "\n" + (rb.stdout or "") + "\n" + (rb.stderr or "")
    for _ in range(passes):
        r = subprocess.run(["pdflatex", "-interaction=nonstopmode", tex], cwd=d, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=900)
        log = (r.stdout or "") + "\n" + (r.stderr or "")
    stem = tex[:-4]
    pdf = os.path.join(d, stem + ".pdf")
    errs = len(re.findall(r"(?m)^!", log or ""))
    undef = len(re.findall(r"Reference .*undefined", log or "")) + len(re.findall(r"Citation .*undefined", log or ""))
    over = len(re.findall(r"Overfull \\hbox", log or ""))
    pages = None
    if os.path.exists(pdf):
        from pypdf import PdfReader
        pages = len(PdfReader(pdf).pages)
    return errs, undef, over, pages, log


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    report = {}
    for name in sorted(os.listdir(ROOT)):
        pk = os.path.join(ROOT, name)
        if not os.path.isdir(pk):
            continue
        z = os.path.join(pk, "LaTeXSource.zip")
        if not os.path.exists(z):
            z = os.path.join(pk, "latex_source.zip")
        entry = {"package": name}
        if not os.path.exists(z):
            entry["status"] = "no latex_source.zip"
            report[name] = entry
            continue
        tmp = tempfile.mkdtemp(prefix="staged_")
        try:
            with zipfile.ZipFile(z) as zf:
                zf.extractall(tmp)
            shipped_pages0 = None
            sp0 = os.path.join(pk, "Manuscript.pdf")
            if os.path.exists(sp0):
                from pypdf import PdfReader
                shipped_pages0 = len(PdfReader(sp0).pages)
            main_tex = find_main(tmp, want_pages=shipped_pages0)
            if not main_tex:
                entry["status"] = "no main tex"
            else:
                errs, undef, over, pages, _ = compile_pdf(tmp, main_tex)
                shipped = None
                sp = os.path.join(pk, "Manuscript.pdf")
                if os.path.exists(sp):
                    from pypdf import PdfReader
                    shipped = len(PdfReader(sp).pages)
                entry.update({"status": "ok" if errs == 0 else "compile_errors", "main": main_tex,
                              "errors": errs, "undefined": undef, "overfull": over,
                              "staged_pages": pages, "shipped_pages": shipped,
                              "page_match": (pages is not None and shipped is not None and pages == shipped)})
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
        report[name] = entry
        print(f"  {name}: {entry.get('status')} errors={entry.get('errors')} "
              f"pages={entry.get('staged_pages')}/{entry.get('shipped_pages')}")
    if a.apply:
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(report, indent=1))
        print("  wrote", os.path.relpath(OUT, REPO))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
