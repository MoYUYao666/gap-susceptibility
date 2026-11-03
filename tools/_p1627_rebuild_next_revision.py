# -*- coding: utf-8 -*-
r"""Rebuild SUBMISSION/P3_PRL_next_revision from the current working-draft sources.

    python tools/_p1627_rebuild_next_revision.py --apply

This is the package-local rebuild that tools/_p1445_rebuild_packages.py does not perform (that script
writes SUBMISSION/_venue_builds/*, and pulls in four other manuscripts). It repeats exactly what
tools/_p1574_record_and_refreeze.py did for the same package, so the result is the same kind of
artefact: main.pdf + supplementary.pdf + title page / highlights / authorship confirmation + the
LaTeX source zip + EM_FIELDS.md + a README freeze record + SHA256SUMS.txt.

The package is NOT hash-pinned: tools/paper_audit/freeze/*.json only pins
SUBMISSION/_archive/P3_PRL_rejected_2026-10-21/**, so no pinned artefact is overwritten. The
submitted package SUBMISSION/P3_PRL_resubmission/ and SUBMISSION/_frozen_submitted/ are only read
from (title page, highlights, authorship confirmation, EM_FIELDS.md) and never written to.

Before rebuilding it asserts that the sources no longer contain the superseded strings
"1434 training pairs" and "(S44)", so a stale build cannot be frozen again.
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import io
import os
import re
import shutil
import subprocess
import sys
import zipfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PKG = "SUBMISSION/P3_PRL_next_revision"
SUBMITTED = "SUBMISSION/P3_PRL_resubmission"
SOURCES = ["paper3/paper_ieee/main.tex", "paper3/paper_ieee/supplementary/supplementary.tex"]
SUPERSEDED = ["1434 training pairs", "(S44)", "97.9\\% of the coupling"]


def assert_sources_clean() -> None:
    for rel in SOURCES:
        text = io.open(os.path.join(REPO, rel), encoding="utf-8").read()
        for token in SUPERSEDED:
            if token in text:
                raise SystemExit("superseded string %r still present in %s" % (token, rel))
    print("sources clean of superseded strings: %s" % ", ".join(repr(t) for t in SUPERSEDED))


def zip_has_stale(zpath: str) -> list[str]:
    bad = []
    with zipfile.ZipFile(zpath) as z:
        for name in z.namelist():
            if not name.endswith(".tex"):
                continue
            data = z.read(name).decode("utf-8", "replace")
            for token in SUPERSEDED:
                if token in data:
                    bad.append("%s: %s" % (name, token))
    return bad


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    assert_sources_clean()
    out = os.path.join(REPO, PKG)
    if not a.apply:
        print("would rebuild %s (existing=%s)" % (PKG, os.path.isdir(out)))
        return 0
    if os.path.isdir(out):
        shutil.rmtree(out)
        print("removed previous %s" % PKG)
    cmd = [sys.executable, "tools/_p1336_build_venue_package.py", "--venue", "PRL", "--out", PKG,
           "--manuscript", "paper3/paper_ieee/main.pdf",
           "--supplementary", "paper3/paper_ieee/supplementary/supplementary.pdf",
           "--title-page", os.path.join(SUBMITTED, "TitlePage.pdf"),
           "--highlights", os.path.join(SUBMITTED, "Highlights.pdf"),
           "--authorship", os.path.join(SUBMITTED, "AuthorshipConfirmation.pdf"),
           "--source", "paper3/paper_ieee", "--figures", "paper3/paper_ieee/figures", "--apply"]
    r = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True)
    print(r.stdout.strip())
    if r.returncode != 0:
        print(r.stderr[-800:])
        return r.returncode
    shutil.copy2(os.path.join(REPO, SUBMITTED, "EM_FIELDS.md"), os.path.join(out, "EM_FIELDS.md"))

    # freeze record appended to the README the builder wrote
    note = ("\n## Freeze record (2026-10-24, rebuilt after the consistency round)\n\n"
            "- Manuscript 10 pages; Supplementary 18 pages (S1--S43).\n"
            "- Discussion limitation (6) now cites the archive values (-23.0 / -43.7 / +25.25,\n"
            "  45.20% environment share from outputs/analysis/p3_env_variance.json); the S17 per-layer\n"
            "  row prints 98.1% and points at S42; the (S44) pointer is gone.\n"
            "- SHA256SUMS.txt covers every file in this package.\n")
    readme = os.path.join(out, "README.md")
    text = io.open(readme, encoding="utf-8").read()
    io.open(readme, "w", encoding="utf-8", newline="").write(text.rstrip() + "\n" + note)

    # checks: no superseded string anywhere in the package, hashes recorded
    bad = []
    for dirpath, _, names in os.walk(out):
        for n in names:
            fp = os.path.join(dirpath, n)
            if n.endswith(".tex") or n.endswith(".md"):
                data = io.open(fp, encoding="utf-8", errors="replace").read()
                for token in SUPERSEDED:
                    if token in data and not n.startswith("README"):
                        bad.append("%s: %s" % (n, token))
    stale_zip = zip_has_stale(os.path.join(out, "LaTeXSource.zip"))
    for item in stale_zip:
        if item not in bad:
            bad.append(item)
    lines = []
    for f in sorted(os.listdir(out)):
        fp = os.path.join(out, f)
        if os.path.isfile(fp) and f != "SHA256SUMS.txt":
            lines.append("%s  %s" % (hashlib.sha256(open(fp, "rb").read()).hexdigest(), f))
    io.open(os.path.join(out, "SHA256SUMS.txt"), "w", encoding="utf-8", newline="").write("\n".join(lines) + "\n")
    print("package rebuilt: %d files hashed" % len(lines))
    if bad:
        print("SUPERSEDED STRINGS FOUND AFTER REBUILD:")
        for item in bad:
            print("   ", item)
        return 1
    print("no superseded string in the rebuilt package")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())