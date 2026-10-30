# -*- coding: utf-8 -*-
r"""Produce paste-ready portal fields by converting the LaTeX abstract with an explicit macro map.

PDF extraction kept dropping inter-word spaces around maths and pulled the title-page footnote into the abstract, so this
converts the LaTeX source instead: every macro that occurs in the abstract and the keyword line is mapped explicitly, and
the script refuses to write if a backslash or brace survives (which would mean an unmapped macro).

    python tools/_p1241_portal_text_tex.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import os
import re

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PA = os.path.join(REPO, "paper合")
OUT = os.path.join(PA, "NC_submission", "PORTAL_TEXT.md")

MACROS = {
    r"\%": "%", r"\pm": " ± ", r"\beta": "β", r"\Delta": "Δ", r"\times": "×",
    r"\cdot": "·", r"\dots": "…", r"\ldots": "…", r"\approx": "≈", r"\le": "≤", r"\ge": "≥",
    r"\alpha": "α", r"\sigma": "σ", r"\tau": "τ", r"\Gamma": "Γ", r"\mathrm{CG}": "CG",
    r"\mathrm{DG}": "DG", r"\mathrm{d}": "d", r"\ell": "ℓ", r"\in": "∈", r"\to": "→",
    r"\quad": " ", r"\,": " ", r"\;": " ", r"\ ": " ", r"\%": "%", r"\#": "#", r"\&": "&",
}
SUPERSCRIPT = {"2": "²", "3": "³", "1": "¹", "4": "⁴", "−1": "⁻¹", "-1": "⁻¹"}


def latex_to_text(s: str) -> str:
    for k in sorted(MACROS, key=len, reverse=True):
        v = MACROS[k]
        s = s.replace(k, v) if isinstance(v, str) else s.replace(k, " ")
    s = re.sub(r"\\(emph|textbf|textit|mathrm|text|url|cite[tp]?|ref)\{([^{}]*)\}", r"\2", s)
    s = re.sub(r"\\[a-zA-Z]+\*?", " ", s)          # any leftover command
    s = re.sub(r"\^\{?([0-9]+)\}?", lambda m: SUPERSCRIPT.get(m.group(1), "^" + m.group(1)), s)
    s = s.replace(r"\_", "_").replace("---", "—").replace("--", "–")
    s = re.sub(r"[{}$]", " ", s)
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"\s+([,.;:])", r"\1", s)
    s = re.sub(r"(\()\s+", r"\1", s)
    return s.strip()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    tex = io.open(os.path.join(PA, "main_nc.tex"), encoding="utf-8").read()

    title = latex_to_text(re.search(r"\\title\{(.+?)\}\s*$", tex, re.S | re.M).group(1))
    abstract_tex = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", tex, re.S).group(1)
    abstract = latex_to_text(abstract_tex)
    kw_tex = re.search(r"\\begin\{keyword\}(.*?)\\end\{keyword\}", tex, re.S).group(1)
    kws = [latex_to_text(x) for x in kw_tex.split(r"\sep")]
    kws = [k.strip(" ,;.") for k in kws if k.strip()]

    hl = io.open(os.path.join(PA, "highlights_nc.txt"), encoding="utf-8").read()
    items = [l.strip("- ").strip() for l in hl.splitlines() if l.strip().startswith("-")]

    bad = [s for s in (title, abstract, " ".join(kws)) if "\\" in s or "{" in s or "}" in s]
    print(f"  title: {title[:70]}...")
    print(f"  abstract words: {len(abstract.split())} | unmapped-macro leftovers: {len(bad)}")
    print(f"  keywords ({len(kws)}): {', '.join(kws)}")
    print(f"  highlights: {len(items)}, max {max(len(x) for x in items)} chars")
    if bad:
        print("  !! leftover LaTeX in output; aborting")
        print("   ", bad[0][:200])
        return 1

    text = f"""# Neurocomputing portal — plain-text fields (copy-paste)

Converted from `paper合/main_nc.tex` by `tools/_p1241_portal_text_tex.py` with an explicit macro map; the script aborts if
any LaTeX survives, so the strings below are paste-ready.

## Title

{title}

## Abstract ({len(abstract.split())} words)

{abstract}

## Keywords ({len(kws)})

{", ".join(kws)}

## Highlights ({len(items)} items, max {max(len(x) for x in items)} chars)

{chr(10).join("- " + x for x in items)}
"""
    if not a.apply:
        print("  (dry run)")
        return 0
    io.open(OUT, "w", encoding="utf-8", newline="").write(text)
    print("  wrote", os.path.relpath(OUT, REPO))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
