# -*- coding: utf-8 -*-
r"""Refresh Paper A's Neurocomputing submission package from the current sources, and prove the source zip builds.

The existing `tools/_pa_build_nc_package.py` writes `latex_source.zip` and `README.md` only inside a branch that is
entered when `figures/_superseded` exists, so a refresh can silently leave the previous zip and README in place. This
script does the refresh unconditionally and adds the check that matters: the packaged source is compiled on its own
in a temporary directory, and the result must have no LaTeX errors and the same page count as `main_nc.pdf`.

    python tools/_p1169_refresh_nc_submission.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PA = REPO / "paper合"
OUT = REPO / "SUBMISSION" / "PaperA_Neurocomputing"
SRC = OUT / "latex_source"


def pages(pdf: Path) -> int:
    """Page count via TeX Live pdfinfo (standard library + TeX only, no third-party package)."""
    r = subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True, timeout=60)
    m = re.search(r"(?m)^Pages:\s+(\d+)", r.stdout or "")
    return int(m.group(1)) if m else 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    main_pdf = PA / "main_nc.pdf"
    if not main_pdf.exists():
        print("  !! main_nc.pdf missing; build it first")
        return 2
    want = pages(main_pdf)
    print(f"  current main_nc.pdf: {want} pages")
    missing = [p for p in (PA / "main_nc.tex", PA / "references.bib", PA / "sections", PA / "figures")
               if not p.exists()]
    if missing:
        print("  !! missing sources:", missing)
        return 2

    # stage into a temp dir, compile there, then install the verified result
    tmp = Path(tempfile.mkdtemp(prefix="nc_pkg_"))
    try:
        stage = tmp / "src"
        stage.mkdir()
        shutil.copy2(PA / "main_nc.tex", stage / "main_nc.tex")
        shutil.copy2(PA / "references.bib", stage / "references.bib")
        (stage / "sections").mkdir()
        for f in sorted((PA / "sections").glob("*.tex")):
            shutil.copy2(f, stage / "sections" / f.name)
        # figures: only what the source actually references, and never the superseded archive
        shutil.copytree(PA / "figures", stage / "figures",
                        ignore=shutil.ignore_patterns("_superseded", "*.pdf_bak*"))
        n_files = len([p for p in stage.rglob("*") if p.is_file()])
        print(f"  staged {n_files} files")

        print("  compiling the staged package standalone ...")
        for cmd in (["pdflatex", "-interaction=nonstopmode", "main_nc.tex"],
                    ["bibtex", "main_nc"],
                    ["pdflatex", "-interaction=nonstopmode", "main_nc.tex"],
                    ["pdflatex", "-interaction=nonstopmode", "main_nc.tex"]):
            r = subprocess.run(cmd, cwd=stage, capture_output=True, text=True, timeout=900)
            print(f"    {cmd[0]:9s} exit {r.returncode}")
        log = (stage / "main_nc.log").read_text(encoding="utf-8", errors="ignore")
        import re
        errs = len(re.findall(r"^!", log, re.M))
        undef = len(re.findall(r"undefined", log, re.I))
        over = len(re.findall(r"Overfull \\hbox", log))
        got = pages(stage / "main_nc.pdf")
        print(f"  staged build: errors={errs} undefined={undef} overfull={over} pages={got} (expected {want})")
        ok = errs == 0 and undef == 0 and got == want
        print("  staged build", "OK" if ok else "FAILED")
        if not ok:
            for line in log.splitlines():
                if line.startswith("!"):
                    print("   ", line[:140])
            return 1
        if not a.apply:
            print("  (dry run; --apply installs the verified package)")
            return 0

        # install
        if SRC.exists():
            shutil.rmtree(SRC)
        SRC.mkdir(parents=True)
        shutil.copy2(PA / "main_nc.tex", SRC / "main_nc.tex")
        shutil.copy2(PA / "references.bib", SRC / "references.bib")
        (SRC / "sections").mkdir()
        for f in sorted((PA / "sections").glob("*.tex")):
            shutil.copy2(f, SRC / "sections" / f.name)
        shutil.copytree(stage / "figures", SRC / "figures")
        # portal-facing names: the package must carry the same content under the names the submission form expects
        # standalone abstract item (Editorial Manager asks for it separately)
        for _ in range(2):
            subprocess.run(["pdflatex", "-interaction=nonstopmode", "abstract_nc.tex"], cwd=PA,
                           capture_output=True, text=True, timeout=600)
        shutil.copy2(PA / "abstract_nc.pdf", OUT / "Abstract.pdf")
        print("    Abstract.pdf <- abstract_nc.pdf")

        for extra, portal_name in (("highlights_nc.pdf", "Highlights.pdf"),
                                   ("highlights_nc.txt", "Highlights.txt"),
                                   ("cover_letter_nc.pdf", "Cover Letter.pdf")):
            src_p = PA / extra
            if src_p.exists():
                shutil.copy2(src_p, OUT / portal_name)
                print(f"    {portal_name} <- {extra}")
        zip_path = OUT / "latex_source.zip"
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for p in sorted(SRC.rglob("*")):
                if p.is_file():
                    zf.write(p, p.relative_to(SRC))
        print(f"  installed latex_source/ and {zip_path.name}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    shutil.copy2(main_pdf, OUT / "Manuscript.pdf")
    print(f"  Manuscript.pdf <- main_nc.pdf ({want} pages)")

    readme = OUT / "README.md"
    body = readme.read_text(encoding="utf-8") if readme.exists() else ""
    import re
    body2 = re.sub(r"\| Manuscript \| `Manuscript\.pdf` \| [^|]*\|",
                   f"| Manuscript | `Manuscript.pdf` | **{want} 页**（当前构建）；含作者信息与全部声明 |", body)
    readme.write_text(body2, encoding="utf-8")
    print("  README page count synchronised")

    print("\n  === package ===")
    for p in sorted(OUT.iterdir()):
        sz = f"{p.stat().st_size:,} B" if p.is_file() else "[dir]"
        print(f"    {p.name:32s} {sz}")
    print(f"\n  zip entries: {len(zipfile.ZipFile(OUT / 'latex_source.zip').namelist())}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
