# -*- coding: utf-8 -*-
r"""Re-stage everything from the canonical sources, then verify.

My mistake: the UPLOAD/ copies were made before the title change, so the staged response
files still carried the old title and no title-change note. Copies must always be made after
the sources stop changing, and then verified - this does both.

    python tools/_p651_restage_and_verify.py [--apply]
"""
from __future__ import annotations

import argparse
import hashlib
import io
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PKG = REPO / "SUBMISSION" / "P3_PRL_revision"
STAGE = PKG / "UPLOAD"
PAPER = REPO / "paper3" / "paper_ieee"
MS = "P3_PRLETTERS-D-26-02378"

PAIRS = [
    (PKG / "manuscript" / "main.pdf", f"{MS}_Manuscript.pdf"),
    (PKG / "manuscript" / "cover_letter.pdf", f"{MS}_Cover_Letter.pdf"),
    (PKG / "manuscript" / "supplementary.pdf", f"{MS}_Supplementary.pdf"),
    (PKG / "manuscript" / "P3_latex_source_revision.zip", f"{MS}_LaTeX_Source.zip"),
    (PKG / "response" / "P3_RESPONSE_Reviewer1_plain.txt", f"{MS}_Response_Reviewer1.txt"),
    (PKG / "response" / "P3_RESPONSE_Reviewer2_plain.txt", f"{MS}_Response_Reviewer2.txt"),
    (PKG / "response" / "P3_RESPONSE_Reviewer3_plain.txt", f"{MS}_Response_Reviewer3.txt"),
]


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    print("  1) rebuild the LaTeX source archive (main text + supplementary)")
    if a.apply:
        r = subprocess.run([sys.executable,
                            str(REPO / "tools" / "_p666_build_full_source_zip.py"), "--apply"],
                           cwd=str(REPO), capture_output=True)
        for l in r.stdout.decode("utf-8", errors="replace").splitlines():
            if "wrote P3" in l or "integrity" in l or "OK " in l or "BAD " in l:
                print(f"     {l.strip()}")

    print()
    print("  2) re-stage every file from its canonical source")
    for src, name in PAIRS:
        if not src.exists():
            print(f"     MISSING source {src}")
            continue
        print(f"     {name:<52} <- {src.name}  ({src.stat().st_size:,} bytes)")
        if a.apply:
            import shutil
            shutil.copy2(src, STAGE / name)

    print()
    print("  3) verify staged == source")
    ok = True
    for src, name in PAIRS:
        st = STAGE / name
        same = st.exists() and sha(st) == sha(src)
        ok = ok and same
        print(f"     {'OK ' if same else 'BAD'} {name:<52} sha {sha(st)[:12] if st.exists() else '-'}")

    print()
    print("  4) response files: plain text, no markdown, carries the title note")
    for _, name in PAIRS:
        if not name.endswith(".txt"):
            continue
        t = io.open(STAGE / name, encoding="utf-8").read()
        # markdown EMPHASIS only: **bold** or a *word*. A bare "*" next to punctuation or
        # inside a path/pattern (runs[*], main/*.json) is legitimate technical notation.
        emphasis = re.findall(r"\*\*[^*\n]+\*\*|(?<![\w*])\*[A-Za-z][^*\n]{0,60}\*(?![\w*])", t)
        stars = len(emphasis)
        note = "Title. The title has changed" in t
        cjk = len(re.findall(r"[\u4e00-\u9fff]", t))
        latex = len(re.findall(r"\\[a-zA-Z]{2,}", t))
        good = note and stars == 0 and cjk == 0 and latex == 0
        ok = ok and good
        print(f"     {'OK ' if good else 'BAD'} {name:<52} note={note} emphasis={stars} "
              f"cjk={cjk} latex={latex}  ({len(t):,} chars)")
        if emphasis:
            for e in emphasis[:4]:
                print(f"          emphasis found: {e[:80]}")

    print()
    print("  5) PDFs: new title in, old title out")
    for _, name in PAIRS:
        if not name.endswith(".pdf"):
            continue
        r = subprocess.run(["pdftotext", "-q", "-layout", str(STAGE / name), "-"],
                           capture_output=True)
        t = re.sub(r"[\s\u00ad]+", "", r.stdout.decode("utf-8", errors="replace"))
        new = "Zero-ShotCross-ArchitectureRankAllocation" in t
        old = "GradientStructureLaws" in t
        good = new and not old
        ok = ok and good
        print(f"     {'OK ' if good else 'BAD'} {name:<52} new={new} old={old}")

    print()
    print(f"  OVERALL: {'ALL CHECKS PASSED' if ok else 'SOMETHING NEEDS ATTENTION'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
