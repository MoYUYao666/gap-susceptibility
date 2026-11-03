# -*- coding: utf-8 -*-
r"""Recompile Paper A and run the whole pre-submission check set that P3 went through.

Checks, in the order they matter:
 1. the document compiles: 0 errors
 2. no unresolved references or citations, no "??" in the PDF
 3. the new data availability text is in the PDF, the stale wording is gone
 4. no severed LaTeX commands (the "abla" / "oindent" damage class)
 5. encoding is valid UTF-8 everywhere in the sources
 6. no Chinese characters in anything that ships
 7. no internal document paths, placeholders or TODO markers
 8. the abstract is within the journal's 250-word limit
 9. every figure referenced exists

    python tools/_p689_paperhe_fullcheck.py [--apply]
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
OUT = REPO / "outputs" / "analysis" / "paperhe_fullcheck.json"

DOI = "10.5281/zenodo.23341223"
STALE = ["currently private", "will be made public upon publication",
         "No new data were generated", "Data will be made available on request"]
SEVERED = [r"(?m)^\s*abla\b", r"(?m)^\s*oindent\b", r"\\abla", r"\\oindent"]
PLACEHOLDERS = ["TODO", "TBD", "FIXME", "XXX", "PLACEHOLDER", "to be inserted",
                "REPOSITORY DOI", "lorem ipsum"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    ok = True
    report = {}

    print("=" * 104)
    print("1. compile")
    print("=" * 104)
    if a.apply:
        for cmd in (["pdflatex", "-interaction=nonstopmode", "main_nc.tex"],
                    ["bibtex", "main_nc"],
                    ["pdflatex", "-interaction=nonstopmode", "main_nc.tex"],
                    ["pdflatex", "-interaction=nonstopmode", "main_nc.tex"]):
            r = subprocess.run(cmd, cwd=str(PA), capture_output=True)
            print(f"  {' '.join(cmd[:2]):<26} rc={r.returncode}")
        log = PA / "main_nc.log"
        lt = io.open(log, encoding="utf-8", errors="replace").read()
        errs = re.findall(r"^! (.*)$", lt, re.M)
        pages = re.findall(r"Output written on main_nc\.pdf \((\d+) pages", 
                           subprocess.run(["pdflatex", "-interaction=nonstopmode",
                                           "-draftmode", "main_nc.tex"],
                                          cwd=str(PA), capture_output=True
                                          ).stdout.decode("utf-8", "replace"))
        print(f"  errors: {len(errs)}")
        for e in errs[:6]:
            print(f"     ! {e[:120]}")
        ok = ok and not errs
        report["latex_errors"] = len(errs)
        u = re.findall(r"Reference `([^']+)' .* undefined", lt)
        c = re.findall(r"Citation `([^']+)' .* undefined", lt)
        print(f"  undefined references: {len(u)} {u[:6]}")
        print(f"  undefined citations : {len(c)} {c[:6]}")
        ok = ok and not u and not c
        report["undefined_refs"] = u
        report["undefined_cites"] = c
    else:
        print("  (dry run)")

    pdf = PA / "main_nc.pdf"
    if pdf.exists():
        r = subprocess.run(["pdfinfo", str(pdf)], capture_output=True)
        info = r.stdout.decode("utf-8", errors="replace")
        pg = re.search(r"Pages:\s+(\d+)", info)
        r = subprocess.run(["pdftotext", "-q", "-layout", str(pdf), "-"], capture_output=True)
        txt = r.stdout.decode("utf-8", errors="replace")
        print()
        print("=" * 104)
        print(f"2. compiled PDF: {pg.group(1) if pg else '?'} pages")
        print("=" * 104)
        print(f"  '??' occurrences: {txt.count('??')}")
        ok = ok and txt.count("??") == 0
        report["pages"] = int(pg.group(1)) if pg else None
        print()
        print("=" * 104)
        print("3. data availability in the PDF")
        print("=" * 104)
        flat = re.sub(r"[\s\u00ad]+", "", txt)
        new_ok = DOI.replace(" ", "") in flat
        print(f"  {'OK ' if new_ok else 'MISSING'} contains the DOI {DOI}")
        ok = ok and new_ok
        for s in STALE:
            n = flat.count(s.replace(" ", ""))
            good = n == 0
            ok = ok and good
            print(f"  {'OK ' if good else f'STILL x{n}'} stale wording absent: {s[:56]}")
        report["doi_in_pdf"] = new_ok

    print()
    print("=" * 104)
    print("4-7. source hygiene")
    print("=" * 104)
    srcs = [PA / "main_nc.tex"] + sorted((PA / "sections").glob("*.tex")) + \
           [PA / "references.bib"]
    issues = {"severed": [], "encoding": [], "cjk": [], "placeholder": []}
    for p in srcs:
        try:
            raw = p.read_bytes()
            t = raw.decode("utf-8")
        except UnicodeDecodeError as e:
            issues["encoding"].append(f"{p.name}: {e}")
            continue
        for pat in SEVERED:
            for m in re.finditer(pat, t):
                issues["severed"].append(f"{p.name}:{t[:m.start()].count(chr(10))+1} {m.group(0)[:30]}")
        if re.search(r"[\u4e00-\u9fff]", t):
            issues["cjk"].append(p.name)
        for ph in PLACEHOLDERS:
            if ph in t:
                issues["placeholder"].append(f"{p.name}: {ph}")
    for k, v in issues.items():
        print(f"  {'OK ' if not v else 'ISSUES'} {k}: {len(v)}")
        for x in v[:6]:
            print(f"        {x}")
    ok = ok and not any(issues.values())
    report["hygiene"] = issues

    print()
    print("=" * 104)
    print("8. abstract length")
    print("=" * 104)
    tex = io.open(PA / "main_nc.tex", encoding="utf-8", errors="replace").read()
    am = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", tex, re.S)
    if am:
        body = re.sub(r"\$[^$]*\$", " MATHTOKEN ", am.group(1))
        body = re.sub(r"\\[a-zA-Z]+\{([^{}]*)\}", lambda m: m.group(1), body)
        body = re.sub(r"\\[a-zA-Z]+", " ", body)
        words = len([w for w in body.split() if re.search(r"[A-Za-z0-9]", w)])
        print(f"  {words} words (limit 250) -> {'OK' if words <= 250 else 'OVER'}")
        ok = ok and words <= 250
        report["abstract_words"] = words

    print()
    print("=" * 104)
    print("9. figures")
    print("=" * 104)
    missing = []
    for p in srcs:
        if p.suffix != ".tex":
            continue
        t = io.open(p, encoding="utf-8", errors="replace").read()
        for m in re.finditer(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}", t):
            g = m.group(1).strip()
            cand = [PA / g, PA / (g + ".png"), PA / (g + ".pdf"),
                    PA / "figures" / Path(g).name]
            if not any(c.exists() for c in cand):
                missing.append(f"{p.name}: {g}")
    print(f"  missing figures: {len(missing)}")
    for m in missing[:10]:
        print(f"     {m}")
    ok = ok and not missing
    report["missing_figures"] = missing

    print()
    print("=" * 104)
    print(f"OVERALL: {'ALL CHECKS PASSED' if ok else 'SOMETHING NEEDS ATTENTION'}")
    print("=" * 104)
    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps(report, ensure_ascii=False, indent=1))
        print(f"  wrote {OUT.relative_to(REPO)}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
