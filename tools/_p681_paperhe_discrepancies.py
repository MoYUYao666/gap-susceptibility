# -*- coding: utf-8 -*-
r"""Resolve three discrepancies found in the Paper A package before submission.

1. Abstract length. The package README claims 246 words; a naive count of everything between
   "Abstract" and "Keywords" gives 263. The Guide's limit is 250, so this decides whether the
   package is compliant.
2. Page count. The README says 56 pages; splitting the extracted text on form feeds gives 65.
   One of the two is wrong.
3. Manuscript.pdf differs byte-wise from the live main_nc.pdf although both are 925,934 bytes.
   If the difference is only a timestamp, it is harmless; if it is content, the package is
   stale.

    python tools/_p681_paperhe_discrepancies.py [--apply]
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
PA = REPO / "paper合"
NC = PA / "NC_submission"
OUT = REPO / "outputs" / "analysis" / "paperhe_discrepancies.json"


def pdftotext(p: Path) -> str:
    r = subprocess.run(["pdftotext", "-q", "-layout", str(p), "-"], capture_output=True)
    return r.stdout.decode("utf-8", errors="replace")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    report = {}

    print("=" * 104)
    print("1. abstract: exact text and count, several ways")
    print("=" * 104)
    man = pdftotext(NC / "Manuscript.pdf")
    # the abstract sits between the word Abstract and the Keywords line
    m = re.search(r"\bAbstract\b(.*?)\bKeywords\b", man, re.S | re.I)
    if not m:
        m = re.search(r"\bAbstract\b(.*?)\n\s*\n", man, re.S | re.I)
    if m:
        abs_raw = m.group(1)
        abs_txt = " ".join(abs_raw.split())
        print(f"  raw slice: {len(abs_raw)} characters")
        print(f"  whitespace-normalised: {len(abs_txt)} characters, "
              f"{len(abs_txt.split())} words")
        report["abstract_words"] = len(abs_txt.split())
        # a second count that drops standalone page numbers and hyphenation artefacts
        cleaned = re.sub(r"(?<=\w)-\s+(?=\w)", "", abs_txt)
        print(f"  after joining hyphenated line breaks: {len(cleaned.split())} words")
        print()
        print("  text:")
        print("  " + abs_txt[:1400])
    else:
        print("  abstract boundaries not located")

    print()
    print("=" * 104)
    print("2. page count: what the PDF itself reports")
    print("=" * 104)
    for label, p in (("package Manuscript.pdf", NC / "Manuscript.pdf"),
                     ("live main_nc.pdf", PA / "main_nc.pdf")):
        r = subprocess.run(["pdfinfo", str(p)], capture_output=True)
        info = r.stdout.decode("utf-8", errors="replace")
        pages = re.search(r"Pages:\s+(\d+)", info)
        ffs = pdftotext(p).count("\f")
        print(f"  {label:<26} pdfinfo Pages={pages.group(1) if pages else '?'}   "
              f"form-feeds={ffs}")
        report[label] = {"pdfinfo_pages": int(pages.group(1)) if pages else None,
                         "form_feeds": ffs}

    print()
    print("=" * 104)
    print("3. why do the two PDFs differ?")
    print("=" * 104)
    a1 = (NC / "Manuscript.pdf").read_bytes()
    a2 = (PA / "main_nc.pdf").read_bytes()
    print(f"  sizes       : {len(a1):,} vs {len(a2):,}  equal={len(a1) == len(a2)}")
    print(f"  sha256      : {hashlib.sha256(a1).hexdigest()[:16]} vs "
          f"{hashlib.sha256(a2).hexdigest()[:16]}")
    diff = [i for i in range(min(len(a1), len(a2))) if a1[i] != a2[i]]
    print(f"  differing byte positions: {len(diff)}")
    if diff:
        lo, hi = diff[0], diff[-1]
        print(f"  range: {lo} .. {hi} of {len(a1):,}")
        print(f"  sample at first difference:")
        print(f"    package: {a1[max(0,lo-40):lo+60]!r}")
        print(f"    live   : {a2[max(0,lo-40):lo+60]!r}")
    # is the text identical?
    t1, t2 = pdftotext(NC / "Manuscript.pdf"), pdftotext(PA / "main_nc.pdf")
    print(f"  extracted text identical: {t1 == t2}")
    report["byte_identical"] = a1 == a2
    report["text_identical"] = t1 == t2

    print()
    print("=" * 104)
    print("4. the live source's own abstract, counted the same way")
    print("=" * 104)
    tex = io.open(PA / "main_nc.tex", encoding="utf-8", errors="replace").read()
    am = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", tex, re.S)
    if am:
        raw = am.group(1)
        for pat, label in ((r"\\[a-zA-Z]+\{([^{}]*)\}", "latex-wrappers removed"),
                           (r"\$[^$]*\$", "math removed")):
            raw = re.sub(pat, r"\1", raw)
        txt = " ".join(raw.split())
        print(f"  from main_nc.tex: {len(txt.split())} words, {len(txt)} characters")
        report["tex_abstract_words"] = len(txt.split())
        print("  " + txt[:600])
    else:
        print("  no abstract environment in main_nc.tex")

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps(report, ensure_ascii=False, indent=1))
        print()
        print(f"  wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
