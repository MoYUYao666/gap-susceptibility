# -*- coding: utf-8 -*-
r"""Chase the two numbers the responses quote but the manuscript text does not seem to contain.

- 0.2057  the random-allocation p-value
- 7,237,632  the matched parameter budget

Either they are in the paper in a different form, or the responses cite numbers a reviewer
cannot check - which would be a real problem in a rebuttal.

    python tools/_p634_chase_missing_numbers.py [--apply]
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
PAPER = REPO / "paper3" / "paper_ieee"
PKG = REPO / "SUBMISSION" / "P3_PRL_revision"
OUT = REPO / "outputs" / "analysis" / "missing_numbers.json"

TARGETS = {
    "0.2057": [r"0\.2057", r"0\.21\b", r"2057"],
    "7,237,632": [r"7,?237,?632", r"7237632", r"7\.24\s*M", r"7\.2\s*M", r"7,237"],
}


def read(p: Path) -> str:
    try:
        return io.open(p, encoding="utf-8", errors="replace").read()
    except Exception:
        return ""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    print("=" * 96)
    print("Where do these numbers appear at all?")
    print("=" * 96)
    # gather every text artefact that could carry them
    corpus = {}
    for p in list(PAPER.rglob("*.tex")) + list(PKG.rglob("*.tex")) + list(PKG.rglob("*.md")):
        corpus[str(p.relative_to(REPO))] = read(p)
    for p in (PKG / "manuscript").glob("*.pdf"):
        corpus[f"[pdf] {p.name}"] = ""
    print(f"  scanned {len(corpus)} text artefacts under paper3/ and SUBMISSION/")

    for num, pats in TARGETS.items():
        print()
        print(f"  ── {num}")
        hits = []
        for name, t in corpus.items():
            for pat in pats:
                for m in re.finditer(pat, t):
                    ln = t[:m.start()].count("\n") + 1
                    seg = " ".join(t[max(0, m.start() - 110):m.start() + 110].split())
                    hits.append((name, ln, m.group(0), seg))
        if not hits:
            print("     no match in any .tex/.md")
        for name, ln, g, seg in hits[:8]:
            print(f"     {name}:{ln}  '{g}'")
            print(f"        {seg[:190]}")

    print()
    print("=" * 96)
    print("Does the compiled PDF contain them? (text extraction)")
    print("=" * 96)
    for pdf in ["main.pdf", "supplementary.pdf"]:
        p = PKG / "manuscript" / pdf
        if not p.exists():
            continue
        r = subprocess.run(["pdftotext", "-q", "-layout", str(p), "-"], capture_output=True)
        t = r.stdout.decode("utf-8", errors="replace")
        flat = re.sub(r"[\s\u00ad]+", "", t)
        print(f"  {pdf}: {len(t):,} chars extracted")
        for num, pats in TARGETS.items():
            found = num.replace(",", "") in flat
            print(f"     {num:<12} present: {found}")
            if found:
                i = flat.find(num.replace(",", ""))
                print(f"        context: ...{flat[max(0,i-90):i+90]}...")
    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(
            {"checked": sorted(corpus)}, ensure_ascii=False, indent=1))
        print()
        print(f"  Wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
