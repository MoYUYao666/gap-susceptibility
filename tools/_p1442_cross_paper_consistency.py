# -*- coding: utf-8 -*-
r"""Cross-manuscript consistency report.

Checks the numbers and protocol constants that the five manuscripts share: page counts claimed in cover letters versus the
built PDFs, DOI strings (only the frozen archive DOIs are allowed), the protocol constants (rank, seeds, epochs) each
manuscript states, and the decimal numbers that appear in two or more manuscripts (for manual review of collisions).

Output: outputs/analysis/cross_paper_consistency.json

    python tools/_p1442_cross_paper_consistency.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import os
import re
from collections import defaultdict

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "outputs", "analysis", "cross_paper_consistency.json")
SOURCES = {
    "A1": ["paper_a1/main.tex"],
    "paperA": ["paper合/main_nc.tex"],
    "P3": ["paper3/paper_ieee/main.tex"],
    "A23": ["paper_a2/main_ieee.tex"],
    "Commentary": ["paper_review_prl/MANUSCRIPT.md"],
}
PDFS = {"A1": "paper_a1/main.pdf", "paperA": "paper合/main_nc.pdf", "P3": "paper3/paper_ieee/main.pdf",
        "A23": "paper_a2/main_ieee.pdf", "Commentary": "paper_review_prl/main_prl.pdf"}
COVERS = {"A1": "paper_a1/cover_letter.tex", "paperA": "paper合/cover_letter_nc.tex",
          "P3": "paper3/paper_ieee/cover_letter.tex", "A23": "paper_a2/cover_letter.tex",
          "Commentary": "paper_review_prl/cover_letter.tex"}
ALLOWED_DOIS = {"10.5281/zenodo.23341223", "10.5281/zenodo.23479164"}
NUM_RE = re.compile(r"(?<![\w.])(\d+\.\d{2,3})(?![\w.])")


def collect(path, seen=None):
    if seen is None:
        seen = set()
    p = os.path.abspath(path)
    if p in seen or not os.path.exists(p):
        return ""
    seen.add(p)
    t = io.open(p, encoding="utf-8", errors="ignore").read()
    for inc in re.finditer(r"\\input\{([^}]+)\}", t):
        t += "\n" + collect(os.path.join(os.path.dirname(p), inc.group(1) + ".tex"), seen)
    for inc in re.finditer(r"\\include\{([^}]+)\}", t):
        t += "\n" + collect(os.path.join(os.path.dirname(p), inc.group(1) + ".tex"), seen)
    return t


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    texts = {k: collect(os.path.join(REPO, v[0])) for k, v in SOURCES.items()}
    report = {"page_counts": {}, "doi_mentions": {}, "protocol_constants": {}, "shared_numbers": {}}
    # 1. page counts: claim in cover letters vs actual PDF
    for name, pdf in PDFS.items():
        p = os.path.join(REPO, pdf)
        if not os.path.exists(p):
            report["page_counts"][name] = {"pdf": None}
            continue
        from pypdf import PdfReader
        n = len(PdfReader(p).pages)
        claim = None
        q = os.path.join(REPO, COVERS[name])
        if os.path.exists(q):
            t = io.open(q, encoding="utf-8", errors="ignore").read()
            m = re.search(r"(\d+)\s*(?:pages|pp\.)", t)
            if m:
                claim = int(m.group(1))
        report["page_counts"][name] = {"pdf": n, "cover_letter_claim": claim,
                                       "ok": (claim is None or claim == n)}
    # 2. DOI strings
    for name, t in texts.items():
        dois = sorted(set(re.findall(r"10\.5281/zenodo\.\d+", t)))
        bad = [d for d in dois if d not in ALLOWED_DOIS]
        report["doi_mentions"][name] = {"dois": dois, "unexpected": bad}
    # 3. protocol constants (contexts)
    pats = {"rank8": r"rank\s*(?:of\s*)?8\b", "merge": r"both[- ](?:tower|position|side)",
            "seeds": r"(?:three|five|two|four|thirteen)\s+seeds", "ten_epochs": r"(?:ten|10)\s+epochs"}
    for name, t in texts.items():
        report["protocol_constants"][name] = {k: len(re.findall(p, t, re.I)) for k, p in pats.items()}
    # 4. shared decimal numbers across manuscripts
    occ = defaultdict(list)
    results_markers = ("%", "pp.", "points", "percent", "\u00d7", "percentage points")
    for name, t in texts.items():
        for m in NUM_RE.finditer(t):
            ctx = t[max(0, m.start() - 70): m.end() + 50].replace("\n", " ")
            if not any(k in ctx for k in results_markers):
                continue
            if "textwidth" in ctx or "linewidth" in ctx or "includegraphics" in ctx:
                continue
            key = m.group(1)
            occ[key].append({"paper": name, "ctx": re.sub(r"\s+", " ", ctx)[:110]})
    shared = {k: v for k, v in occ.items() if len({x["paper"] for x in v}) >= 2}
    report["shared_numbers"] = dict(sorted(shared.items(), key=lambda kv: -len(kv[1]))[:40])
    # print summary
    print("  page counts:")
    for k, v in report["page_counts"].items():
        print(f"    {k}: pdf={v.get('pdf')} claim={v.get('cover_letter_claim')} ok={v.get('ok')}")
    bad = {k: v["unexpected"] for k, v in report["doi_mentions"].items() if v["unexpected"]}
    print("  unexpected DOIs:", bad if bad else "none")
    print("  shared decimal numbers across manuscripts:", len(shared))
    for k, v in list(report["shared_numbers"].items())[:10]:
        papers = sorted({x["paper"] for x in v})
        print(f"    {k}: {papers} | {v[0]['ctx'][:80]}")
    if a.apply:
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(report, indent=1))
        print("  wrote", os.path.relpath(OUT, REPO))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
