# -*- coding: utf-8 -*-
r"""Extract every number Paper A states, with the sentence it sits in.

This is the input to the claim ledger: the ledger must cover the numbers the paper actually
asserts, so the first step is to list them rather than guess.

Runs over the compiled manuscript sections (the prose the reader sees), splits into sentences,
and reports each sentence containing a decimal number or a large integer.

    python tools/_p699_paperhe_numbers.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PA = REPO / "paper合"
OUT = REPO / "outputs" / "analysis" / "paperhe_numbers.json"

# numbers worth chasing: decimals (results) and integers >= 3 digits (counts)
DEC = re.compile(r"\b\d+\.\d+\b")
INT = re.compile(r"\b\d{3,}\b")
# things that look numeric but are references, years, page or section numbers
NOISE = re.compile(r"(19|20)\d{2}|\bsec|section|table|figure|eq\.|ref\b", re.I)


def detex(s: str) -> str:
    s = re.sub(r"\\[a-zA-Z]+\{([^{}]*)\}", lambda m: m.group(1), s)
    s = re.sub(r"\\[a-zA-Z]+", " ", s)
    s = s.replace("{", " ").replace("}", " ").replace("$", " ")
    s = re.sub(r"\s+", " ", s)
    return s


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    files = [PA / "main_nc.tex"] + sorted((PA / "sections").glob("*.tex"))
    found: dict[str, list[dict]] = {}
    for p in files:
        raw = io.open(p, encoding="utf-8", errors="replace").read()
        txt = detex(raw)
        # sentence split
        for sent in re.split(r"(?<=[.!?])\s+", txt):
            if NOISE.search(sent) and not DEC.search(sent):
                continue
            nums = sorted(set(DEC.findall(sent)) | set(INT.findall(sent)))
            nums = [n for n in nums if n not in ("2026", "2025", "2024", "2023", "2022")]
            if not nums:
                continue
            found.setdefault(p.name, []).append(
                {"numbers": nums, "sentence": sent.strip()[:400]})

    total = 0
    for f, rows in found.items():
        print("=" * 104)
        print(f)
        print("=" * 104)
        for r in rows:
            total += len(r["numbers"])
            print(f"  {' '.join(r['numbers'])[:60]:<62}")
            print(f"      {r['sentence'][:220]}")
        print()
    print(f"  total numeric tokens across {len(found)} files: {total}")

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps(found, ensure_ascii=False, indent=1))
        print(f"  wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
