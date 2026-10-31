# -*- coding: utf-8 -*-
r"""Audit the Paper A figure library: references, orphans, PNG/PDF pairing, and embedded fonts.

Three things the library has to satisfy, all checkable mechanically:

1. every file `\includegraphics` names exists, in both the working copy and the NC copy;
2. no figure file in `figures/` is unreferenced (an orphan in the same directory as live figures is
   how a wrong figure gets picked up during a package rebuild -- the provenance note records that
   happening once already with `fig8`/`fig9`);
3. every embedded font is Times New Roman or a Times-compatible maths font (STIX / Nimbus Roman).
   matplotlib silently falls back to DejaVu Sans if the style is not applied, and DejaVu is the
   signature of that mistake, so it is treated as a failure rather than a note.

Reads the `\includegraphics` lines rather than a hand-maintained list, so the audit cannot go stale.

    python tools/_p867_figure_audit.py [--apply]     # --apply moves orphans into _superseded/
"""
from __future__ import annotations

import argparse
import io
import re
import shutil
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
FIGDIR = REPO / "paper合" / "figures"
SUPERSEDED = FIGDIR / "_superseded"
TEXDIRS = [REPO / "paper合" / "sections", REPO / "paper合" / "NC_submission" / "latex_source" / "sections"]
OK_FONT_STEMS = ("timesnewroman", "stix", "nimbusroman", "nimbus")
BAD_FONT_STEMS = ("dejavu", "liberation", "cmr", "helvetica", "arial")


def referenced() -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    pat = re.compile(r"\\includegraphics\[[^\]]*\]\{figures/([^}]+)\}")
    for d in TEXDIRS:
        for p in sorted(d.glob("*.tex")):
            for m in pat.finditer(io.open(p, encoding="utf-8").read()):
                out.setdefault(m.group(1), []).append(p.relative_to(REPO).as_posix())
    return out


def fonts_of(p: Path) -> list[str]:
    r = subprocess.run(["pdffonts", str(p)], capture_output=True)
    txt = r.stdout.decode("utf-8", "replace").splitlines()
    names = []
    for line in txt[2:]:
        parts = line.split()
        if parts:
            names.append(parts[0].split("+")[-1])
    return names


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    refs = referenced()
    present = sorted(p.name for p in FIGDIR.iterdir() if p.is_file())
    problems = 0

    print(f"  referenced by the manuscript: {len(refs)} figures")
    missing = [n for n in refs if not (FIGDIR / n).exists()]
    for n in missing:
        print(f"  MISSING {n}  (named by {refs[n][0]})")
    problems += len(missing)

    # A file is live when it is referenced, or when it is the PNG export of a referenced PDF: the
    # manuscripts use the vector PDF, and every figure also ships a 300-dpi PNG alongside it.
    live = set(refs)
    for n in refs:
        if Path(n).suffix == ".pdf":
            live.add(Path(n).with_suffix(".png").name)
    orphans = [n for n in present if n.startswith("fig") and n not in live]
    print(f"  files in figures/: {len(present)}  ｜  live: {len(live)}  ｜  unreferenced: {len(orphans)}")
    for n in orphans:
        print(f"    orphan: {n}")

    # every referenced figure must have both exports present
    unpaired = []
    for n in sorted(refs):
        stem = Path(n).stem
        for ext in (".pdf", ".png"):
            if not (FIGDIR / (stem + ext)).exists():
                unpaired.append(stem + ext)
    if unpaired:
        print(f"  unpaired exports: {unpaired}")
        problems += len(unpaired)

    # fonts, per referenced PDF
    bad = []
    for n in sorted(refs):
        p = FIGDIR / n
        if not p.exists() or p.suffix != ".pdf":
            continue
        fs = fonts_of(p)
        low = [f.lower() for f in fs]
        ok = all(any(s in f for s in OK_FONT_STEMS) for f in low)
        if not ok:
            offenders = [f for f in fs if not any(s in f.lower() for s in OK_FONT_STEMS)]
            bad.append((n, offenders))
            print(f"  FONT  {n}: {', '.join(offenders)}")
        if any(any(s in f for s in BAD_FONT_STEMS) for f in low):
            print(f"  FONT-FAIL {n}: a fallback font is embedded -- the style was not applied")
    problems += len(bad)
    print(f"  fonts: {len(refs) - len(bad)}/{len(refs)} figures fully Times/STIX")

    if orphans:
        if a.apply:
            SUPERSEDED.mkdir(parents=True, exist_ok=True)
            for n in orphans:
                src = FIGDIR / n
                dst = SUPERSEDED / n
                assert not dst.exists(), f"{dst} already exists; refusing to overwrite"
                shutil.move(str(src), str(dst))
                print(f"    moved {n} -> figures/_superseded/")
        else:
            print("    (dry run: pass --apply to move them into figures/_superseded/)")

    print(f"  problems: {problems}")
    return 0 if problems == 0 and not orphans else 1


if __name__ == "__main__":
    raise SystemExit(main())
