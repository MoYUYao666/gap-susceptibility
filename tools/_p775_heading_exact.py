# -*- coding: utf-8 -*-
r"""Compare the exact heading titles in the rebuilt supplementary PDF.

The previous check matched substrings, so "Downstream check (summary)" was counted as a repeat of
"Downstream check". This extracts heading-like lines and compares them exactly, which is what the
reader sees.

    python tools/_p775_heading_exact.py --apply
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
OUT = REPO / "outputs" / "analysis" / "supp_heading_exact.json"

# headings as they appear in the source, for an exact presence test
EXPECT_ONCE = [
    "Comparison with Prior Work",
    "Rank Scaling and $\\Gamma$ Evolution",
    "Second-Dataset Validation (ShareGPT)",
    "Sample Size Robustness",
]
EXPECT_SUMMARY = ["Downstream check (summary)", "Decoder VLM (summary)"]


def pdftext(p: Path) -> str:
    r = subprocess.run(["pdftotext", "-q", "-layout", str(p), "-"], capture_output=True)
    return r.stdout.decode("utf-8", errors="replace")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    pdf = REPO / "paper3" / "paper_ieee" / "supplementary" / "supplementary.pdf"
    t = pdftext(pdf)
    lines = [re.sub(r"\s+", " ", l).strip() for l in t.splitlines()]
    # heading lines: short, no trailing sentence punctuation
    heads = [l for l in lines if 3 <= len(l) <= 70 and not l.endswith((".", ",", ";"))]

    print("=" * 100)
    print(f"{pdf.relative_to(REPO)}  ({pdf.stat().st_size:,} bytes, {t.count(chr(12)) + 1} pages)")
    print("=" * 100)
    print("  candidate heading lines, with exact repeat counts:")
    counts = {}
    for h in heads:
        counts[h] = counts.get(h, 0) + 1
    for h, n in sorted(counts.items(), key=lambda kv: -kv[1]):
        if n > 1:
            print(f"    [{n}x] {h}")
    repeated = {h: n for h, n in counts.items() if n > 1}
    print(f"  exactly repeated heading lines: {len(repeated)}")

    print()
    print("=" * 100)
    print("  expected headings from the fixed source")
    print("=" * 100)
    ok = True
    flat = re.sub(r"\s+", " ", t)
    for h in EXPECT_ONCE:
        needle = re.sub(r"\s+", " ", h.replace("$\\Gamma$", "Γ"))
        n = flat.count(needle)
        good = n == 1
        ok = ok and good
        print(f"    [{'ok  ' if good else 'FAIL'}] {h:<40} occurrences: {n}")
    for h in EXPECT_SUMMARY:
        n = flat.count(h)
        good = n >= 1
        ok = ok and good
        print(f"    [{'ok  ' if good else 'FAIL'}] {h:<40} occurrences: {n}")

    print()
    print(f"  OVERALL: {'HEADINGS UNIQUE' if ok and not repeated else 'STILL REPEATED'}")

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps({"repeated_lines": repeated}, ensure_ascii=False, indent=1),
                       encoding="utf-8")
        print(f"  wrote {OUT.relative_to(REPO)}")
    return 0 if (ok and not repeated) else 1


if __name__ == "__main__":
    raise SystemExit(main())
