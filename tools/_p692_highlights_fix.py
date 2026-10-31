# -*- coding: utf-8 -*-
r"""Settle three inconsistencies in the Paper A highlights before submission.

1. NC_submission/Highlights.pdf prints an OLD title ("Protect, Don't Perturb: ..."), while the
   manuscript is titled "Adaptation Site and the Modality Gap: ...". The file the editorial
   office reads therefore names a manuscript that does not exist.
2. The bullet quoting the ODE fit says "median R2 of 0.97" in the package but "0.96" in
   highlights_nc.pdf. The manuscript has to decide which is right.
3. Confirm every bullet's claim is something the manuscript actually states.

    python tools/_p692_highlights_fix.py [--apply]
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
OUT = REPO / "outputs" / "analysis" / "paperhe_highlights.json"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    report = {}

    print("=" * 104)
    print("1. the manuscript's own title and its R2 claims")
    print("=" * 104)
    tex = io.open(PA / "main_nc.tex", encoding="utf-8", errors="replace").read()
    m = re.search(r"\\title\{(.*?)\}", tex, re.S)
    title = " ".join(m.group(1).split()) if m else "?"
    print(f"  title: {title}")
    report["title"] = title

    corpus = tex + "\n".join(
        io.open(p, encoding="utf-8", errors="replace").read()
        for p in (PA / "sections").glob("*.tex"))
    flat = re.sub(r"\s+", " ", corpus)
    print()
    print("  R2 mentions around 0.9x (median or mean):")
    for m in re.finditer(r"[^.]{0,150}R\^?2?[^.]{0,150}", flat):
        seg = m.group(0)
        if re.search(r"0\.9\d", seg):
            print(f"     ...{seg.strip()[:250]}...")
    print()
    for probe in ("median R", "mean R", "0.96", "0.97", "0.949", "0.97"):
        print(f"  occurrences of {probe!r}: {flat.count(probe)}")
    report["r2_probes"] = {p: flat.count(p) for p in ("median R", "0.96", "0.97", "0.949")}

    print()
    print("=" * 104)
    print("2. the highlights files, side by side")
    print("=" * 104)
    for p in (NC / "Highlights.txt", PA / "highlights_nc.txt"):
        t = io.open(p, encoding="utf-8", errors="replace").read()
        print(f"  {p.relative_to(REPO)}: {t.splitlines()[1:3]}")
        print(f"     R2 bullet: "
              f"{[l for l in t.splitlines() if 'R2' in l]}")
    for p in (NC / "Highlights.pdf", PA / "highlights_nc.pdf"):
        r = subprocess.run(["pdftotext", "-q", "-layout", str(p), "-"], capture_output=True)
        t = r.stdout.decode("utf-8", errors="replace")
        head = " ".join(t.split())[:150]
        print(f"  {p.relative_to(REPO)}:")
        print(f"     head: {head}")
        for line in t.splitlines():
            if "R2" in line:
                print(f"     R2 line: {line.strip()[:110]}")

    print()
    print("=" * 104)
    print("3. verdict on the title embedded in the package highlights")
    print("=" * 104)
    r = subprocess.run(["pdftotext", "-q", "-layout", str(NC / "Highlights.pdf"), "-"],
                       capture_output=True)
    ht = " ".join(r.stdout.decode("utf-8", errors="replace").split())
    stale = "Protect" in ht
    current = "Adaptation Site" in ht
    print(f"  package Highlights.pdf carries the OLD title: {stale}")
    print(f"  package Highlights.pdf carries the CURRENT title: {current}")
    report["package_highlights_stale_title"] = stale
    if stale and not current:
        print("  -> the highlights must be rebuilt from the current title")

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps(report, ensure_ascii=False, indent=1))
        print()
        print(f"  wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
