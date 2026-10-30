# -*- coding: utf-8 -*-
r"""Produce the final copy-pasteable abstract for Paper A.

Source of truth: `paper合/abstract_nc.tex` (the standalone abstract file, whose text is copied verbatim from
`main_nc.tex`). LaTeX is converted with an explicit macro map: dashes, inline maths (spacing around = < > ± ×, proper
Unicode minus, superscripts such as R^2 -> R²), emphasis macros. The script refuses to write unless the result has no
LaTeX residue, no double spaces, no space before punctuation, and no more than 250 words.

Outputs:
  SUBMISSION/PaperA_Neurocomputing/Abstract.txt   (single paragraph, UTF-8)
  refreshes the Abstract section of PORTAL_TEXT.md

    python tools/_p1251_copyable_abstract.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import os
import re

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PA = os.path.join(REPO, "paper合")
PKG = os.path.join(REPO, "SUBMISSION", "PaperA_Neurocomputing")

SUPER = {"2": "²", "3": "³", "1": "¹", "4": "⁴", "-1": "⁻¹", "−1": "⁻¹",
         "2/3": "⅔", "1/2": "½"}
MACROS = {
    r"\%": "%", r"\pm": "±", r"\beta": "β", r"\Delta": "Δ", r"\times": "×", r"\approx": "≈",
    r"\le": "≤", r"\ge": "≥", r"\to": "→", r"\cdot": "·", r"\dots": "…", r"\ldots": "…",
    r"\alpha": "α", r"\sigma": "σ", r"\tau": "τ", r"\Gamma": "Γ",
    r"\;": " ", r"\,": "", r"\ ": " ", r"\quad": " ",
}


def math_to_text(body: str) -> str:
    body = re.sub(r"\^\{?(-?\d+(?:/\d+)?)\}?",
                  lambda m: SUPER.get(m.group(1), "^" + m.group(1)), body)
    for k in sorted(MACROS, key=len, reverse=True):
        body = body.replace(k, MACROS[k])
    body = body.replace("-", "−")
    body = re.sub(r"\s*([=<>])\s*", r" \1 ", body)
    body = re.sub(r"\s*([±×≈])\s*", r" \1 ", body)
    return " " + body + " "


def convert(tex: str) -> str:
    s = tex
    s = re.sub(r"\\(emph|textbf|textit|mathrm|text|url)\{([^{}]*)\}", r"\2", s)
    s = re.sub(r"\\cite[tp]?\{[^{}]*\}", "", s)
    s = re.sub(r"\\ref\{[^{}]*\}", "", s)
    s = re.sub(r"\$([^$]*)\$", lambda m: math_to_text(m.group(1)), s)
    for k in sorted(MACROS, key=len, reverse=True):
        s = s.replace(k, MACROS[k])
    s = s.replace(r"\_", "_").replace("---", "—").replace("--", "–")
    s = re.sub(r"\\[a-zA-Z]+\*?", " ", s)
    s = re.sub(r"[{}$]", " ", s)
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"\s+([,.;:!?%])", r"\1", s)
    s = re.sub(r"\(\s+", "(", s)
    s = re.sub(r"\s+\)", ")", s)
    s = re.sub(r"(\d)(?=[A-Za-z]{3,})", r"\1 ", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    tex = io.open(os.path.join(PA, "abstract_nc.tex"), encoding="utf-8").read()
    m = re.search(r"\\section\*\{Abstract\}\s*(.*?)\s*\\vspace", tex, re.S)
    assert m, "Abstract section not found"
    text = convert(m.group(1))

    problems = []
    if "\\" in text or "{" in text or "}" in text:
        problems.append("LaTeX residue")
    if "  " in text:
        problems.append("double space")
    if re.search(r"\s[,.;:%]", text):
        problems.append("space before punctuation")
    words = len(text.split())
    if words > 250:
        problems.append(f"{words} words > 250")
    for sym in ("β", "±", "R²", "–"):
        if sym not in text:
            problems.append(f"missing symbol {sym!r}")
    print(f"  words: {words} | problems: {problems if problems else 'none'}")

    print("\n=== COPY-PASTE ABSTRACT ===")
    print(text)
    print("=== END ===\n")
    if problems:
        return 1
    if not a.apply:
        print("  (dry run)")
        return 0
    io.open(os.path.join(PKG, "Abstract.txt"), "w", encoding="utf-8", newline="").write(text + "\n")
    print("  wrote SUBMISSION/PaperA_Neurocomputing/Abstract.txt")

    portal = os.path.join(PKG, "PORTAL_TEXT.md")
    p = io.open(portal, encoding="utf-8").read()
    p = re.sub(r"## Abstract \(\d+ words\)", f"## Abstract ({words} words)", p)
    p = re.sub(r"(## Abstract \(\d+ words\)\n\n)(.*?)(\n\n## Keywords)",
               lambda mm: mm.group(1) + text + mm.group(3), p, flags=re.S)
    io.open(portal, "w", encoding="utf-8", newline="").write(p)
    print("  refreshed PORTAL_TEXT.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
