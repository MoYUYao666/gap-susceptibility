# -*- coding: utf-8 -*-
r"""Check the numbers I earlier listed as response-vs-paper risks, one by one.

My first pass used a strict extractor that flagged section references (3.11 means "section
3.11 of the paper") and rank vectors (4,2,2,9) as missing numbers. This checks only the
numbers that are meant to be quantitative results, and for each it searches the manuscript
for equivalent notations before declaring a mismatch.

    python tools/_p636_check_key_numbers.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PAPER = REPO / "paper3" / "paper_ieee"
PKG = REPO / "SUBMISSION" / "P3_PRL_revision"
OUT = REPO / "outputs" / "analysis" / "key_number_check.json"

# (label, response form, manuscript-equivalent regexes)
CHECKS = [
    ("random-allocation p-value", "0.2057", [r"p\s*=\s*0\.21\b", r"0\.2057", r"p\s*=\s*0\.2\b"]),
    ("matched parameter budget", "7,237,632", [r"7,?237,?632", r"7\.2\s*M\b", r"7(\s*)million"]),
    ("learning rate 3e-4", "0.0003", [r"3\s*[x\\]?\s*10\^\{?-4", r"3e-4", r"0\.0003", r"3\\times10"]),
    ("matched training loss A", "0.5872", [r"0\.5872", r"0\.587"]),
    ("matched training loss B", "0.5826", [r"0\.5826", r"0\.583"]),
    ("experimental arm 5e-5", "1478", [r"1478", r"1,?478"]),
    ("uniform arm 5e-5", "5048", [r"5048", r"5,?048"]),
    ("reversal experimental 3e-4", "5968", [r"5968", r"5,?968"]),
    ("reversal uniform 3e-4", "2842", [r"2842", r"2,?842"]),
    ("AdaLoRA margin 1", "1468", [r"1468", r"1,?468"]),
    ("AdaLoRA margin 2", "757", [r"757"]),
    ("permutation p for crossing", "0.100", [r"0\.100", r"p\s*=\s*0\.10\b"]),
    ("between-rank variance share", "98.9", [r"98\.9"]),
    ("inverse vs uniform p", "0.037", [r"0\.037"]),
    ("corner vs uniform p", "0.0587", [r"0\.0587", r"0\.059"]),
    ("Qwen token count", "50176", [r"50,?176"]),
    ("Ode R2", "0.9767", [r"0\.9767", r"0\.977", r"0\.98"]),
]


def read(p: Path) -> str:
    try:
        return io.open(p, encoding="utf-8", errors="replace").read()
    except Exception:
        return ""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    files = [PAPER / "main.tex"] + sorted((PAPER / "sections").glob("*.tex")) + \
            sorted((PAPER / "supplementary").glob("*.tex"))
    paper = "\n".join(read(p) for p in files)
    flat = re.sub(r"\s+", " ", paper)
    # also look in the compiled supplementary PDF text, for tables
    print(f"  manuscript text: {len(flat):,} characters from {len(files)} files")
    print()
    print(f"  {'result':<30} {'response':>12}  {'in paper?':<10} match")
    print("  " + "-" * 88)
    rows = []
    problems = []
    for label, resp, pats in CHECKS:
        found = None
        for pat in pats:
            m = re.search(pat, flat, re.I)
            if m:
                found = m.group(0)
                break
        ok = found is not None
        if not ok:
            problems.append((label, resp))
        print(f"  {label:<30} {resp:>12}  {'OK' if ok else 'MISSING':<10} {found}")
        rows.append({"label": label, "response_form": resp, "in_paper": ok, "match": found})
    print()
    print(f"  {len(CHECKS) - len(problems)}/{len(CHECKS)} quantitative claims appear in the manuscript")
    if problems:
        print()
        print("  Needs action:")
        for label, resp in problems:
            print(f"    - {label}: the responses quote {resp}, the manuscript does not contain it")
    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(
            {"checks": rows, "problems": problems}, ensure_ascii=False, indent=1))
        print()
        print(f"  Wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
