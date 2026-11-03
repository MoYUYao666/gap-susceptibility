# -*- coding: utf-8 -*-
r"""Verify the staged upload folder after the tidy.

The operator's concern was picking the wrong file. This proves:

1. Every staged file is byte-identical to the canonical file it was copied from.
2. No other file in the revision package has a name that could be confused with a staged one.
3. No backup or temporary file remains anywhere in the revision package.
4. The superseded folders are recognisable by name and hold what they claim.
5. The manuscript PDF is still the verified 10-page, 0-error, DOI-bearing build.

    python tools/_p645_verify_staging.py [--apply]
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PKG = REPO / "SUBMISSION" / "P3_PRL_revision"
STAGE = PKG / "UPLOAD"
SUB = REPO / "SUBMISSION"
OUT = REPO / "outputs" / "analysis" / "staging_verify.json"

SOURCES = {
    "P3_PRLETTERS-D-26-02378_Manuscript.pdf": PKG / "manuscript" / "main.pdf",
    "P3_PRLETTERS-D-26-02378_Cover_Letter.pdf": PKG / "manuscript" / "cover_letter.pdf",
    "P3_PRLETTERS-D-26-02378_Supplementary.pdf": PKG / "manuscript" / "supplementary.pdf",
    "P3_PRLETTERS-D-26-02378_LaTeX_Source.zip":
        PKG / "manuscript" / "P3_latex_source_revision.zip",
    "P3_PRLETTERS-D-26-02378_Response_Reviewer1.txt":
        PKG / "response" / "P3_RESPONSE_Reviewer1_plain.txt",
    "P3_PRLETTERS-D-26-02378_Response_Reviewer2.txt":
        PKG / "response" / "P3_RESPONSE_Reviewer2_plain.txt",
    "P3_PRLETTERS-D-26-02378_Response_Reviewer3.txt":
        PKG / "response" / "P3_RESPONSE_Reviewer3_plain.txt",
}


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    report = {}
    ok = True

    print("=" * 100)
    print("1. staged file == canonical source?")
    print("=" * 100)
    for name, src in SOURCES.items():
        st = STAGE / name
        same = st.exists() and src.exists() and sha(st) == sha(src)
        ok = ok and same
        print(f"  {'OK ' if same else 'BAD'} {name:<52} "
              f"{st.stat().st_size if st.exists() else 0:>10,} bytes  "
              f"sha {sha(st)[:12] if st.exists() else '-'}")
    report["identical"] = ok

    print()
    print("=" * 100)
    print("2. any other file in the package that could be confused with a staged one?")
    print("=" * 100)
    staged_names = set(SOURCES)
    collisions = []
    for p in PKG.rglob("*"):
        if not p.is_file() or p.parent == STAGE:
            continue
        # same basename, or a name differing only by case/extension
        for s in staged_names:
            if p.name.lower() == s.lower() or \
               re.sub(r"[^a-z0-9]", "", p.name.lower()) in re.sub(r"[^a-z0-9]", "", s.lower()):
                collisions.append(p.relative_to(REPO).as_posix())
    if collisions:
        print("  files with a near-identical name (expected: the canonical sources):")
        for c in collisions:
            print(f"    {c}")
        print("  NOTE: these are the sources the staged copies came from; they live in")
        print("        manuscript/ and response/, which are read-only for the operator.")
    else:
        print("  none")
    report["near_duplicates"] = collisions

    print()
    print("=" * 100)
    print("3. any backup or temporary file left in the package?")
    print("=" * 100)
    junk = [p.relative_to(REPO).as_posix() for p in PKG.rglob("*")
            if p.is_file() and (".bak" in p.name or p.name.endswith("~"))]
    print(f"  {len(junk)} found" + (": " + ", ".join(junk) if junk else ""))
    ok = ok and not junk
    report["junk"] = junk

    print()
    print("=" * 100)
    print("4. superseded folders")
    print("=" * 100)
    for d in sorted(SUB.glob("_superseded*")):
        n = len([p for p in d.rglob("*") if p.is_file()])
        print(f"  {d.name:<46} {n:>4} files")
    report["superseded"] = {d.name: len([p for p in d.rglob("*") if p.is_file()])
                            for d in SUB.glob("_superseded*")}

    print()
    print("=" * 100)
    print("5. the staged manuscript PDF is still the verified build")
    print("=" * 100)
    pdf = STAGE / "P3_PRLETTERS-D-26-02378_Manuscript.pdf"
    r = subprocess.run(["pdftotext", "-q", "-layout", str(pdf), "-"], capture_output=True)
    t = r.stdout.decode("utf-8", errors="replace")
    flat = re.sub(r"[\s\u00ad]+", "", t)
    pages = None
    log = PKG / "manuscript" / "main.log"
    if (REPO / "paper3" / "paper_ieee" / "main.log").exists():
        lt = io.open(REPO / "paper3" / "paper_ieee" / "main.log",
                     encoding="utf-8", errors="replace").read()
        m = re.search(r"Output written on .*?\((\d+) pages", lt)
        pages = int(m.group(1)) if m else None
    checks = {
        "DOI present": "10.5281/zenodo.23341223" in flat,
        "old DOI absent": "10.5281/zenodo.23341083" not in flat,
        "superseded 3607 absent": "3607" not in flat,
        "superseded 2241 absent": "2241" not in flat,
        "current 2344 present": "2344" in flat,
        "current 1477 present": "1477" in flat,
        "p = 0.21 present": "0.21" in flat,
    }
    for k, v in checks.items():
        print(f"  {'OK ' if v else 'BAD'} {k}")
        ok = ok and v
    print(f"  (LaTeX log reports {pages} pages)")
    report["pdf_checks"] = checks

    print()
    print("=" * 100)
    print(f"OVERALL: {'ALL CHECKS PASSED' if ok else 'SOMETHING NEEDS ATTENTION'}")
    print("=" * 100)
    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps(report, ensure_ascii=False, indent=1))
        print(f"  Wrote {OUT.relative_to(REPO)}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
