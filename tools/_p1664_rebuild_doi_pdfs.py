"""Rebuild the five live manuscripts after the v2.5 DOI change and verify page counts.

Each manuscript is compiled twice with the TeX Live 2025 `pdflatex` on PATH; the page count is read
from the fresh log ("Output written on ... (N pages") and compared with the frozen constants in
`tools/_p1454_final_verify.py`. The same logs are scanned for errors, undefined references, undefined
citations and overfull boxes, because a DOI string edit must not introduce any of them.

The page-count constants are re-read from `_p1454_final_verify.py` at run time rather than hard-coded,
so this script cannot drift from the gate it is protecting.

Usage:
    python tools/_p1664_rebuild_doi_pdfs.py [--apply]
    (--apply actually runs pdflatex; without it the script only lists what it would build)
"""

from __future__ import annotations

import argparse
import io
import os
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

# (working directory, tex file, pdf file) - the five live manuscripts plus the Paper A Springer variant
TARGETS = [
    ("paper_a1", "main.tex", "main.pdf"),
    ("paper合", "main_nc.tex", "main_nc.pdf"),
    ("paper合", "main_springer.tex", "main_springer.pdf"),
    ("paper3/paper_ieee", "main.tex", "main.pdf"),
    ("paper_a2", "main_ieee.tex", "main_ieee.pdf"),
    ("paper_review_prl", "main_prl.tex", "main_prl.pdf"),
]

PAGES_RE = re.compile(r"Output written on .*?(\d+) pages")


def expected_pages() -> dict:
    """Read the PAGES constant out of the final-verification script.

    The constant looks like `{"paper_a1/main.pdf": (64,), ...}` - values are 1-tuples of the allowed
    page counts - and it is keyed by the **full relative path**, because two different manuscripts are
    both called `main.pdf`.
    """
    src = io.open(REPO / "tools" / "_p1454_final_verify.py", encoding="utf-8").read()
    m = re.search(r"PAGES\s*=\s*\{(.*?)\n\}", src, re.S)
    if not m:
        return {}
    out = {}
    for k, v in re.findall(r'"([^"]+)"\s*:\s*\(?(\d+)', m.group(1)):
        out[k.replace("\\", "/")] = int(v)
    return out


def scan_log(log_path: Path) -> dict:
    text = io.open(log_path, encoding="utf-8", errors="replace").read()
    return {
        "errors": len(re.findall(r"^! ", text, re.M)),
        "undef_ref": len(re.findall(r"LaTeX Warning: Reference [^\n]*?undefined", text)),
        "undef_cite": len(re.findall(r"(?:LaTeX|Package natbib) Warning: Citation [^\n]*?undefined", text)),
        "overfull_hbox": len(re.findall(r"^Overfull \\hbox", text, re.M)),
        "overfull_vbox": len(re.findall(r"^Overfull \\vbox", text, re.M)),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    exp = expected_pages()
    print("expected pages from _p1454_final_verify.PAGES:", exp)
    rc = 0
    rows = []
    for wd, tex, pdf in TARGETS:
        d = REPO / wd
        if not (d / tex).is_file():
            print("  [FAIL] missing %s" % (d / tex))
            rc = 2
            continue
        want = exp.get("%s/%s" % (wd, pdf))
        print("\n== %s/%s (expect %s pages) ==" % (wd, tex, want))
        if not args.apply:
            print("   would run pdflatex twice")
            continue
        passes = 0
        for i in (1, 2):
            proc = subprocess.run(["pdflatex", "-interaction=nonstopmode", "-halt-on-error", tex],
                                  cwd=str(d), capture_output=True, text=True, errors="replace")
            passes += 1
            last = [l for l in proc.stdout.splitlines() if l.strip()][-1:] or [""]
            print("   pass %d rc=%d  %s" % (i, proc.returncode, last[0][:90]))
            if proc.returncode != 0:
                rc = 2
                break
        log = (d / tex).with_suffix(".log")
        pdf_path = d / pdf
        if not pdf_path.is_file():
            print("   [FAIL] %s not produced" % pdf)
            rc = 2
            continue
        text = io.open(log, encoding="utf-8", errors="replace").read()
        m = PAGES_RE.search(text)
        got = int(m.group(1)) if m else None
        s = scan_log(log)
        ok = (got == want) and s["errors"] == 0 and s["undef_ref"] == 0 and \
             s["undef_cite"] == 0 and s["overfull_hbox"] == 0 and s["overfull_vbox"] == 0
        print("   pages=%s (want %s) errors=%d uref=%d ucite=%d ohbox=%d ovbox=%d  => %s"
              % (got, want, s["errors"], s["undef_ref"], s["undef_cite"],
                 s["overfull_hbox"], s["overfull_vbox"], "OK" if ok else "MISMATCH"))
        rows.append((wd, tex, got, want, s, ok))
        if not ok:
            rc = 2

    if args.apply:
        print("\n== summary ==")
        for wd, tex, got, want, s, ok in rows:
            print("  %-28s %-18s pages %-4s want %-4s %s"
                  % (wd, tex, got, want, "OK" if ok else "MISMATCH"))
    return rc


if __name__ == "__main__":
    sys.exit(main())
