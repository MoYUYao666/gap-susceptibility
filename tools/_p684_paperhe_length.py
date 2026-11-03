# -*- coding: utf-8 -*-
r"""Establish the real length of the Paper A manuscript, and whether the package README is stale.

The package README says 56 pages; pdfinfo says 63. Since the operator is about to submit, the
number has to be right, and the README's other claims should be spot-checked at the same time
rather than trusted.

    python tools/_p684_paperhe_length.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PA = REPO / "paper合"
NC = PA / "NC_submission"
OUT = REPO / "outputs" / "analysis" / "paperhe_length.json"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    report = {}

    print("=" * 104)
    print("1. page counts as reported by the PDF tooling")
    print("=" * 104)
    for label, p in (("package Manuscript.pdf", NC / "Manuscript.pdf"),
                     ("live main_nc.pdf", PA / "main_nc.pdf"),
                     ("Springer variant", PA / "main_springer.pdf")):
        if not p.exists():
            print(f"  {label:<26} missing")
            continue
        r = subprocess.run(["pdfinfo", str(p)], capture_output=True)
        info = r.stdout.decode("utf-8", errors="replace")
        pages = re.search(r"Pages:\s+(\d+)", info)
        psize = re.search(r"Page size:\s+(.*)", info)
        print(f"  {label:<26} pages={pages.group(1) if pages else '?':<5} "
              f"size={psize.group(1).strip() if psize else '?'}")
        report[label] = {"pages": int(pages.group(1)) if pages else None}

    print()
    print("=" * 104)
    print("2. what the README claims, line by line, versus the measurement")
    print("=" * 104)
    rdm = NC / "README.md"
    txt = io.open(rdm, encoding="utf-8", errors="replace").read()
    claims = re.findall(r"\*\*(\d+)\s*(?:页|words|词|条)\*\*", txt)
    print(f"  numbers asserted in bold in README.md: {claims}")
    for line in txt.splitlines():
        if any(k in line for k in ("页", "words", "词", "条", "摘要", "Highlights")):
            print("    " + line.strip()[:150])

    print()
    print("=" * 104)
    print("3. structure of the compiled manuscript: what is on each page")
    print("=" * 104)
    r = subprocess.run(["pdftotext", "-q", "-layout", str(NC / "Manuscript.pdf"), "-"],
                       capture_output=True)
    pages = r.stdout.decode("utf-8", errors="replace").split("\f")
    print(f"  {len(pages)} text sections extracted")
    markers = ["Abstract", "Keywords", "Introduction", "Related Work", "Empirical",
               "Theory", "Validation", "Discussion", "Conclusion", "Declaration",
               "Data availability", "Funding", "CRediT", "References",
               "Appendix", "Supplementary"]
    for mk in markers:
        hits = [i + 1 for i, pg in enumerate(pages) if mk.lower() in pg.lower()]
        if hits:
            print(f"  {mk:<20} first on page {hits[0]:>3}   ({len(hits)} page(s) mention it)")

    print()
    print("=" * 104)
    print("4. is the README stale, or is it describing a different file?")
    print("=" * 104)
    print(f"  README.md      modified {subprocess.run(['cmd','/c','dir','/T:W',str(rdm)],capture_output=True).stdout.decode('utf-8','replace').splitlines()[-2][:60] if False else ''}")
    for p in (rdm, NC / "Manuscript.pdf", NC / "latex_source.zip", PA / "main_nc.tex"):
        print(f"  {p.name:<22} {p.stat().st_size:>10,} bytes  mtime "
              f"{__import__('datetime').datetime.fromtimestamp(p.stat().st_mtime):%Y-%m-%d %H:%M}")

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps(report, ensure_ascii=False, indent=1))
        print()
        print(f"  wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
