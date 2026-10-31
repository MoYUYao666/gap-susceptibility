# -*- coding: utf-8 -*-
r"""Two blocking checks for Paper A before submission.

1. Duplicate-submission risk. Paper A is P1+P2. Paper 3 (the PRL submission, just revised) is
   a distinct manuscript, and the archived folder paper_ap3 was set aside precisely because
   combining P1+P2+P3 would overlap. If Paper A cites or reuses P3's content, submitting it
   while P3 is under review at PRL is a problem. This looks for P3-specific material inside
   Paper A.

2. Data availability. The PRL review required a real data statement naming a repository and a
   DOI. Paper A must carry the equivalent, and it must sit before the references.

    python tools/_p685_paperhe_blockers.py [--apply]
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
OUT = REPO / "outputs" / "analysis" / "paperhe_blockers.json"

# phrases that are specific to Paper 3
P3_MARKERS = [
    "PRLETTERS", "Pattern Recognition Letters",
    "Gap Susceptibility", "Gamma_k", "rank allocation",
    "AdaLoRA", "zero-shot cross-architecture", "predictive transfer",
    "blank image", "visual token budget",
]


def pdftext(p: Path) -> str:
    r = subprocess.run(["pdftotext", "-q", "-layout", str(p), "-"], capture_output=True)
    return r.stdout.decode("utf-8", errors="replace")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    report = {}
    man = pdftext(NC / "Manuscript.pdf")
    flat = re.sub(r"\s+", " ", man)

    print("=" * 104)
    print("1. does Paper A contain Paper 3 material?")
    print("=" * 104)
    for mk in P3_MARKERS:
        n = len(re.findall(re.escape(mk), flat, re.I))
        flag = "RISK" if n and mk in ("PRLETTERS", "Pattern Recognition Letters") else (
            "note" if n else "ok  ")
        print(f"  {flag} {mk:<34} {n} occurrence(s)")
        if n:
            m = re.search(re.escape(mk), flat, re.I)
            print(f"        ...{flat[max(0, m.start() - 130):m.start() + 150]}...")
    print()
    print(f"  reference to Paper 3's framework name 'Gap Susceptibility': "
          f"{flat.count('Gap Susceptibility')} time(s)")

    print()
    print("=" * 104)
    print("2. data availability in Paper A")
    print("=" * 104)
    for key in ("Data availability", "Data Availability", "data statement"):
        for m in re.finditer(re.escape(key), man, re.I):
            page = man[:m.start()].count("\f") + 1
            seg = " ".join(man[m.start():m.start() + 420].split())
            print(f"  page {page}: {seg[:400]}")
            print()
    has_repo = bool(re.search(r"github\.com|zenodo|10\.5281", man, re.I))
    print(f"  names a repository or DOI: {has_repo}")

    print()
    print("=" * 104)
    print("3. does the source have its own data statement section?")
    print("=" * 104)
    srcs = sorted((PA / "sections").glob("*.tex"))
    for p in srcs:
        t = io.open(p, encoding="utf-8", errors="replace").read()
        if re.search(r"data availability|data statement", t, re.I):
            print(f"  {p.name}")
            for m in re.finditer(r"(?:data availability|data statement)", t, re.I):
                seg = " ".join(t[m.start():m.start() + 400].split())
                print(f"     {seg[:380]}")

    print()
    print("=" * 104)
    print("4. declaration ordering (must precede references)")
    print("=" * 104)
    pages = man.split("\f")
    def first_page(pat: str) -> int | None:
        for i, pg in enumerate(pages, 1):
            if re.search(pat, pg, re.I):
                return i
        return None
    order = {
        "Data availability": first_page(r"data availability"),
        "Funding": first_page(r"\bfunding\b"),
        "Competing interests": first_page(r"competing interest|conflict of interest"),
        "CRediT": first_page(r"\bCRediT\b"),
        "Generative AI": first_page(r"generative ai"),
        "References": first_page(r"^\s*References\s*$|\bReferences\b"),
    }
    for k, v in order.items():
        print(f"  {k:<22} first on page {v}")
    refs = order.get("References")
    bad = [k for k, v in order.items() if k != "References" and v and refs and v > refs]
    print(f"  declarations after references: {bad if bad else 'none'}")
    report["order"] = order
    report["declarations_after_refs"] = bad

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps(report, ensure_ascii=False, indent=1))
        print()
        print(f"  wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
