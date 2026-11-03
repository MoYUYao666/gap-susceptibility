# -*- coding: utf-8 -*-
r"""Systematic number-by-number comparison between the response letters and the manuscript.

Method: extract every numeric token from the three response boxes and from the manuscript
sources, then report numbers that appear in a response but nowhere in the manuscript. Then
for each such number, search the evidence reports to find out where it came from, so the
choice is explicit: either add it to the paper, or cite the form the paper uses.

    python tools/_p635_number_diff.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
RESP = REPO / "SUBMISSION" / "P3_PRL_revision" / "response"
PKG = REPO / "SUBMISSION" / "P3_PRL_revision"
PAPER = REPO / "paper3" / "paper_ieee"
OUT = REPO / "outputs" / "analysis" / "number_diff.json"

# a numeric token: digits with optional decimal part and optional thousands separators
NUM = re.compile(r"\d[\d,]*(?:\.\d+)?")
# noise: years, page numbers, section refs, seed ids, small integers
NOISE = {"1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15",
         "16", "17", "18", "19", "20", "21", "22", "23", "24", "25", "0", "2026", "2025",
         "2024", "2023", "2022", "2021", "2020", "215", "16", "32", "64", "128", "256",
         "512", "1024", "100", "1000", "0.5", "0.1", "0.01", "0.001", "1.0", "0.0"}


def read(p: Path) -> str:
    try:
        return io.open(p, encoding="utf-8", errors="replace").read()
    except Exception:
        return ""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    # corpus: what the reviewer can read
    paper_files = [PAPER / "main.tex"] + sorted((PAPER / "sections").glob("*.tex")) + \
                  sorted((PAPER / "supplementary").glob("*.tex"))
    paper = "\n".join(read(p) for p in paper_files)
    paper_nums = set(NUM.findall(paper))
    paper_nums |= {n.replace(",", "") for n in paper_nums}

    def in_paper(n: str) -> bool:
        return n in paper_nums or n.replace(",", "") in paper_nums

    print(f"  Manuscript: {len(paper_files)} files, {len(paper_nums)} distinct numeric tokens")
    print()
    rows = []
    for p in sorted(RESP.glob("*_plain.txt")):
        t = read(p)
        nums = [n for n in NUM.findall(t) if n not in NOISE and len(n) >= 3]
        missing = sorted({n for n in nums if not in_paper(n)},
                         key=lambda s: (-len(s), s))
        print("=" * 96)
        print(f"{p.name}: {len(set(nums))} distinct numeric tokens, "
              f"{len(missing)} not found in the manuscript")
        print("=" * 96)
        for n in missing:
            # where does it come from?
            origin = []
            for q in (PKG / "evidence").glob("*.md"):
                if n in read(q):
                    origin.append(q.name)
            for q in (PKG / "evidence").glob("*.json"):
                if n in read(q):
                    origin.append(q.name)
            print(f"    {n:<14} evidence: {', '.join(origin[:3]) if origin else '(not in evidence either)'}")
            rows.append({"file": p.name, "number": n, "evidence": origin[:3]})
        print()
    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(
            {"missing": rows}, ensure_ascii=False, indent=1))
        print(f"  Wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
