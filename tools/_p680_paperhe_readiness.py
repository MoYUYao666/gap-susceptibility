# -*- coding: utf-8 -*-
r"""Reading-only status check for Paper A before submission.

Establishes, from files rather than memory:
- what the compiled manuscript says about itself (title, pages, abstract)
- what the submission package contains and whether it is current
- what the Neurocomputing guide requires, where the repo has it
- what the handoff's most recent entries about this paper say
- which P3 lessons transfer (data statement with DOI, authorship confirmation, page limit)

    python tools/_p680_paperhe_readiness.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PA = REPO / "paper合"
NC = PA / "NC_submission"
OUT = REPO / "outputs" / "analysis" / "paperhe_readiness.json"


def pdftotext(p: Path) -> str:
    if not p.exists():
        return ""
    r = subprocess.run(["pdftotext", "-q", "-layout", str(p), "-"], capture_output=True)
    return r.stdout.decode("utf-8", errors="replace")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    report: dict = {}

    print("=" * 104)
    print("1. the compiled manuscript in the package")
    print("=" * 104)
    for name in ("Manuscript.pdf", "Cover Letter.pdf", "Highlights.pdf"):
        p = NC / name
        if not p.exists():
            print(f"  MISSING  {name}")
            continue
        t = pdftotext(p)
        pages = t.count("\f") + 1
        print(f"  {name:<20} {p.stat().st_size:>9,} bytes  ~{pages} pages  "
              f"{datetime.fromtimestamp(p.stat().st_mtime):%Y-%m-%d %H:%M}")
        report[name] = {"bytes": p.stat().st_size, "pages": pages}
    man = pdftotext(NC / "Manuscript.pdf")
    if man:
        head = " ".join(man[:1400].split())
        print()
        print("  manuscript first 700 characters:")
        print("    " + head[:700])
    print()
    print("  abstract word count:", end=" ")
    m = re.search(r"Abstract[—\-–:]?\s*(.*?)(?:Keywords|1\.\s*Introduction|I\.\s*INTRODUCTION)",
                  man, re.S | re.I)
    if m:
        words = len(m.group(1).split())
        print(f"{words} ({'OK' if words <= 250 else 'OVER 250'})")
        report["abstract_words"] = words
    else:
        print("not located")

    print()
    print("=" * 104)
    print("2. package contents vs what the package says")
    print("=" * 104)
    rdm = NC / "README.md"
    if rdm.exists():
        txt = io.open(rdm, encoding="utf-8", errors="replace").read()
        print("  README.md says:")
        for line in txt.splitlines()[:30]:
            if line.strip():
                print("    " + line[:150])

    print()
    print("=" * 104)
    print("3. does the package match the current sources?")
    print("=" * 104)
    src_zip = NC / "latex_source.zip"
    print(f"  latex_source.zip    {src_zip.stat().st_size:>9,}  "
          f"{datetime.fromtimestamp(src_zip.stat().st_mtime):%Y-%m-%d %H:%M}")
    print(f"  main_nc.pdf (live)  {(PA / 'main_nc.pdf').stat().st_size:>9,}  "
          f"{datetime.fromtimestamp((PA / 'main_nc.pdf').stat().st_mtime):%Y-%m-%d %H:%M}")
    print(f"  Manuscript.pdf      {(NC / 'Manuscript.pdf').stat().st_size:>9,}  "
          f"{datetime.fromtimestamp((NC / 'Manuscript.pdf').stat().st_mtime):%Y-%m-%d %H:%M}")
    same = (PA / "main_nc.pdf").read_bytes() == (NC / "Manuscript.pdf").read_bytes()
    print(f"  live main_nc.pdf == package Manuscript.pdf: {same}")

    print()
    print("=" * 104)
    print("4. Neurocomputing requirements available in the repo?")
    print("=" * 104)
    for pat in ("*neuro*", "*NEURO*", "*nc_guide*", "*els*guide*"):
        for p in REPO.glob(f"docs/**/{pat}"):
            print(f"  {p.relative_to(REPO)}  ({p.stat().st_size:,} bytes)")
    guides = REPO / "docs" / "guides"
    if guides.exists():
        for p in sorted(guides.iterdir()):
            print(f"  docs/guides/{p.name}  ({p.stat().st_size:,} bytes)")

    print()
    print("=" * 104)
    print("5. P3 lessons that apply, as checks against this package")
    print("=" * 104)
    checks = {
        "Data statement present in manuscript": "data statement" in man.lower()
                                                 or "data availability" in man.lower(),
        "Manuscript names a repository or DOI": bool(re.search(r"zenodo|10\.5281|github", man, re.I)),
        "Funding statement present": bool(re.search(r"funding|grant", man, re.I)),
        "AI declaration present": bool(re.search(r"generative ai|claude|deepseek|llm", man, re.I)),
        "Competing interests present": "competing interest" in man.lower()
                                       or "conflict of interest" in man.lower(),
        "Highlights file present": (NC / "Highlights.pdf").exists(),
        "Cover letter present": (NC / "Cover Letter.pdf").exists(),
        "Title page present separately": any("title" in p.name.lower() for p in NC.iterdir()),
    }
    for k, v in checks.items():
        print(f"  {'OK ' if v else 'TO CHECK'} {k}")
    report["checks"] = checks

    print()
    print("=" * 104)
    print("6. latest handoff entries mentioning this paper")
    print("=" * 104)
    h = io.open(REPO / "HANDOFF.md", encoding="utf-8", errors="replace").read()
    hits = [m.start() for m in re.finditer(r"paper合|Paper A|Neurocomputing", h)]
    seen = set()
    shown = 0
    for pos in hits:
        line_start = h.rfind("\n", 0, pos) + 1
        ln = h[:pos].count("\n") + 1
        if ln // 40 in seen:
            continue
        seen.add(ln // 40)
        seg = " ".join(h[max(0, pos - 200):pos + 260].split())
        print(f"  L{ln}: {seg[:300]}")
        shown += 1
        if shown >= 8:
            break

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps(report, ensure_ascii=False, indent=1))
        print()
        print(f"  wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
