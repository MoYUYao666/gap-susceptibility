# -*- coding: utf-8 -*-
r"""Rebuild the Springer variant too, and audit the highlights.

The Nature-style variant (main_springer.tex) shares sections/conclusion.tex, which changed, so
leaving it unbuilt would leave one packaged PDF inconsistent with its own source.

The highlights need checking because in the P3 revision the highlights turned out to be stale
and still advertised withdrawn claims - and they are a file the editorial office reads.

    python tools/_p691_springer_and_highlights.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PA = REPO / "paper合"
NC = PA / "NC_submission"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    ok = True

    print("=" * 104)
    print("1. Springer variant (shares sections/, so it must be rebuilt)")
    print("=" * 104)
    if a.apply:
        for cmd in (["pdflatex", "-interaction=nonstopmode", "main_springer.tex"],
                    ["bibtex", "main_springer"],
                    ["pdflatex", "-interaction=nonstopmode", "main_springer.tex"],
                    ["pdflatex", "-interaction=nonstopmode", "main_springer.tex"]):
            r = subprocess.run(cmd, cwd=str(PA), capture_output=True)
        log = PA / "main_springer.log"
        lt = io.open(log, encoding="utf-8", errors="replace").read()
        errs = re.findall(r"^! (.*)$", lt, re.M)
        r = subprocess.run(["pdfinfo", str(PA / "main_springer.pdf")], capture_output=True)
        pg = re.search(r"Pages:\s+(\d+)", r.stdout.decode("utf-8", "replace"))
        print(f"  pages={pg.group(1) if pg else '?'}  errors={len(errs)}")
        for e in errs[:5]:
            print(f"     ! {e[:110]}")
        ok = ok and not errs
    else:
        print("  (dry run)")

    print()
    print("=" * 104)
    print("2. highlights: which file, how many bullets, how long")
    print("=" * 104)
    cands = [NC / "Highlights.txt", PA / "highlights_nc.txt", NC / "Highlights.pdf",
             PA / "highlights_nc.pdf"]
    for p in cands:
        if not p.exists():
            print(f"  missing: {p.relative_to(REPO)}")
            continue
        if p.suffix == ".txt":
            t = io.open(p, encoding="utf-8", errors="replace").read()
            print(f"  {p.relative_to(REPO)}  ({p.stat().st_size:,} bytes)")
            bullets = [l.strip(" -•\t") for l in t.splitlines() if l.strip()]
            for b in bullets:
                if b.lower() in ("highlights", ""):
                    continue
                flag = "OK " if len(b) <= 85 else f"TOO LONG {len(b)}"
                print(f"      [{flag:>12}] {b[:90]}")
        else:
            r = subprocess.run(["pdftotext", "-q", "-layout", str(p), "-"],
                               capture_output=True)
            t = r.stdout.decode("utf-8", errors="replace")
            print(f"  {p.relative_to(REPO)}  ({p.stat().st_size:,} bytes, "
                  f"{t.count(chr(12))+1} pages)")
            for line in t.splitlines():
                s = line.strip()
                if len(s) > 30 and not s.lower().startswith("highlights"):
                    flag = "OK " if len(s) <= 85 else f"TOO LONG {len(s)}"
                    print(f"      [{flag:>12}] {s[:90]}")

    print()
    print("=" * 104)
    print("3. do the highlights assert anything the paper does not support?")
    print("=" * 104)
    hl = NC / "Highlights.txt"
    if hl.exists():
        t = io.open(hl, encoding="utf-8", errors="replace").read()
        risky = {
            "unique / only admissible statistic": r"unique|only admissible",
            "sharp phase transition": r"sharp|phase transition",
            "causal language": r"causal|proves?|establishes?",
            "beats / outperforms": r"beats?|outperform",
            "reduces uncertainty by Nx": r"reduces? uncertainty|\d+\s*[x×]",
        }
        for label, pat in risky.items():
            m = re.findall(pat, t, re.I)
            print(f"  {'CHECK' if m else 'ok   '} {label}: {m if m else ''}")
        ok = ok and not any(re.findall(p, t, re.I) for p in risky.values())
    else:
        print("  Highlights.txt not found")

    print()
    print(f"  OVERALL: {'OK' if ok else 'SOMETHING NEEDS ATTENTION'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
