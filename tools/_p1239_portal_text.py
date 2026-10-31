# -*- coding: utf-8 -*-
r"""Prepare the plain-text fields a portal form asks for, so submission is a copy-paste job.

Elsevier Editorial Manager typically asks for: title, abstract (paste), keywords, highlights (file or paste), cover
letter (file), and the manuscript/source files. This writes a single reference file with the exact strings taken from the
manuscript sources (no retyping, so no drift).

    python tools/_p1239_portal_text.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import os
import re

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PA = os.path.join(REPO, "paper合")
OUT = os.path.join(PA, "NC_submission", "PORTAL_TEXT.md")


def plain(tex: str) -> str:
    t = re.sub(r"(?m)%.*$", "", tex)
    t = re.sub(r"\\emph\{([^{}]*)\}", r"\1", t)
    t = re.sub(r"\\textbf\{([^{}]*)\}", r"\1", t)
    t = re.sub(r"\\url\{([^{}]*)\}", r"\1", t)
    t = re.sub(r"\\text\{([^{}]*)\}", r"\1", t)
    t = re.sub(r"\$([^$]*)\$", lambda m: m.group(1).replace("\\", ""), t)
    t = re.sub(r"\\[a-zA-Z]+\*?(\[[^\]]*\])?", " ", t)
    t = re.sub(r"[{}$~]", " ", t)
    t = t.replace("--", "-")
    return re.sub(r"\s+", " ", t).strip()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    main_tex = io.open(os.path.join(PA, "main_nc.tex"), encoding="utf-8").read()

    title = ""
    m = re.search(r"\\title\{(.+?)\}\s*\n", main_tex, re.S)
    if m:
        title = plain(m.group(1))
    abs_m = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", main_tex, re.S)
    abstract = plain(abs_m.group(1)) if abs_m else ""
    kw_m = re.search(r"\\begin\{keyword\}(.*?)\\end\{keyword\}", main_tex, re.S)
    keywords = plain(kw_m.group(1)).replace("\\sep", ",") if kw_m else ""
    keywords = re.sub(r"\s*,\s*", ", ", keywords).strip(" ,")

    hl = io.open(os.path.join(PA, "highlights_nc.txt"), encoding="utf-8").read().strip()
    hl_items = [l.strip("- ").strip() for l in hl.splitlines() if l.strip().startswith("-")]

    text = f"""# Neurocomputing portal — plain-text fields (copy-paste)

Source: `paper合/NC_submission/` package built 2026-10-17/18; every string below is extracted from the manuscript
sources by `tools/_p1239_portal_text.py`, not retyped.

## Title

{title}

## Abstract ({len(abstract.split())} words)

{abstract}

## Keywords

{keywords}

## Highlights ({len(hl_items)} items, max {max(len(x) for x in hl_items)} chars)

{chr(10).join("- " + x for x in hl_items)}
"""
    print(f"  title: {title[:60]}...")
    print(f"  abstract words: {len(abstract.split())}")
    print(f"  keywords: {keywords}")
    print(f"  highlights: {len(hl_items)} items")
    if not a.apply:
        print("  (dry run)")
        return 0
    io.open(OUT, "w", encoding="utf-8", newline="").write(text)
    print("  wrote", os.path.relpath(OUT, REPO))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
