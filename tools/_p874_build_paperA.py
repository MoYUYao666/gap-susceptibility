# -*- coding: utf-8 -*-
r"""Build Paper A: three pdflatex passes around one bibtex pass, with per-pass logs and checks.

Why this exists: the ad-hoc build used PowerShell's `*>>`, which **truncates** the log the first time a
command writes to a non-existent file and appends only afterwards. So the surviving `main_nc.log` held
the last pass alone, and its natbib "Citation undefined" warnings (which are normal in pass 1, before
bibtex has run) looked like a real defect. This script keeps one log per pass so the final pass can be
audited on its own.

Checks on the final pass, all of which must be zero: LaTeX errors, undefined citations, undefined
references, and "Float too large for page". It also reports the number of bibliography entries, the
citation keys used in the sources, and any key that is cited but missing from the .bib (or vice versa).

    python tools/_p874_build_paperA.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import re
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PA = REPO / "paper合"
LOGS = REPO / "outputs" / "analysis"


def run(cmd: list[str], log: Path) -> int:
    r = subprocess.run(cmd, cwd=PA, capture_output=True)
    out = (r.stdout or b"") + (r.stderr or b"")
    log.write_bytes(out)
    return r.returncode


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not a.apply:
        print("  (dry run; pass --apply to build)")
        return 0

    steps = [
        (["pdflatex", "-interaction=nonstopmode", "main_nc.tex"], "pass1.log", 0),
        (["bibtex", "main_nc"], "bibtex.log", 0),
        (["pdflatex", "-interaction=nonstopmode", "main_nc.tex"], "pass2.log", 0),
        (["pdflatex", "-interaction=nonstopmode", "main_nc.tex"], "pass3.log", 0),
    ]
    for cmd, name, _ in steps:
        rc = run(cmd, LOGS / f"_pa_{name}")
        print(f"  {name:<12} exit {rc}")

    # LaTeX asks for another pass when a \ref or a page number moved; a 62-page document with a new
    # appendix needs a few. Keep going until the request stops, so the page count audited below is the
    # converged one rather than an intermediate.
    for extra in range(4, 8):
        txt = (LOGS / f"_pa_pass{extra - 1}.log").read_text(encoding="utf-8", errors="replace")
        if "Rerun to get cross-references right" not in txt and "Label(s) may have changed" not in txt:
            break
        rc = run(["pdflatex", "-interaction=nonstopmode", "main_nc.tex"], LOGS / f"_pa_pass{extra}.log")
        print(f"  pass{extra:<8} exit {rc}  (convergence)")

    # the highest-numbered pass log that exists is the one to audit
    finals = sorted(LOGS.glob("_pa_pass*.log"), key=lambda p: int(p.stem.split("pass")[-1]))
    final_name = finals[-1].name
    print(f"  auditing {final_name}")
    final = (LOGS / final_name).read_text(encoding="utf-8", errors="replace")
    errs = re.findall(r"^!.*$", final, re.M)
    cites = re.findall(r"Package natbib Warning: Citation `([^']+)' .*undefined", final)
    refs = re.findall(r"LaTeX Warning: Reference `([^']+)' .*undefined", final)
    floats = re.findall(r"Float too large for page", final)
    print()
    print(f"  LaTeX errors:            {len(errs)}")
    print(f"  undefined citations:     {len(cites)} {sorted(set(cites))[:5]}")
    print(f"  undefined references:    {len(refs)} {sorted(set(refs))[:5]}")
    print(f"  floats too large:        {len(floats)}")
    print(f"  rerun requested:         {'Rerun to get' in final}")

    # bibliography coverage
    bib = (PA / "references.bib").read_text(encoding="utf-8", errors="replace")
    bib_keys = set(re.findall(r"@\w+\{([^,]+),", bib))
    used: set[str] = set()
    for d in (PA / "sections", PA / "NC_submission" / "latex_source" / "sections"):
        for p in d.glob("*.tex"):
            t = p.read_text(encoding="utf-8", errors="replace")
            for m in re.finditer(r"\\cite[tp]?\{([^}]+)\}", t):
                used |= {k.strip() for k in m.group(1).split(",") if k.strip()}
    for p in PA.glob("*.tex"):
        t = p.read_text(encoding="utf-8", errors="replace")
        for m in re.finditer(r"\\cite[tp]?\{([^}]+)\}", t):
            used |= {k.strip() for k in m.group(1).split(",") if k.strip()}
    missing = sorted(used - bib_keys)
    unused = sorted(bib_keys - used)
    print()
    print(f"  bib entries:             {len(bib_keys)}")
    print(f"  keys cited in sources:   {len(used)}")
    print(f"  cited but not in .bib:   {len(missing)} {missing[:6]}")
    print(f"  in .bib but never cited: {len(unused)} {unused[:6]}")

    bbl = PA / "main_nc.bbl"
    n_bbl = len(re.findall(r"\\bibitem", bbl.read_text(encoding="utf-8", errors="replace"))) \
        if bbl.exists() else 0
    print(f"  entries in main_nc.bbl:  {n_bbl}")
    pdf = PA / "main_nc.pdf"
    if pdf.exists():
        import pypdf
        print(f"  pages:                   {len(pypdf.PdfReader(pdf).pages)}")
    ok = not errs and not cites and not refs and not floats and not missing
    print()
    print("  " + ("BUILD CLEAN" if ok else "BUILD HAS PROBLEMS"))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
