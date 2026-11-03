# -*- coding: utf-8 -*-
r"""Extract the abstract as paste-ready plain text, and check it against the journal limits.

PRL wants an abstract of at most 250 words. The form field takes plain text, so the LaTeX
markup has to go: math mode, \emph, citation commands, escaped percent signs.

    python tools/_p669_abstract_for_form.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MAIN = REPO / "paper3" / "paper_ieee" / "main.tex"
OUT = REPO / "SUBMISSION" / "P3_PRL_revision" / "UPLOAD" / "P3_PRLETTERS-D-26-02378_Abstract.txt"

MATH = {
    r"\Gamma": "Gamma",
    r"\Delta": "Delta",
    r"\beta": "beta",
    r"\eta": "eta",
    r"\tau": "tau",
    r"\lambda": "lambda",
    r"\sigma": "sigma",
    r"\times": "x",
    r"\to": "->",
    r"\le": "<=",
    r"\ge": ">=",
    r"\approx": "~",
    r"\pm": "+-",
    r"\in": " in ",
    r"\cos": "cos",
    r"\exp": "exp",
    r"\langle": "<",
    r"\rangle": ">",
    r"\propto": "proportional to",
    r"\textbf": "",
    r"\noindent": "",
    r"\|": "||",
    r"\%": "%",
    r"\&": "&",
    r"\_": "_",
    r"\{": "{",
    r"\}": "}",
    r"\,": " ",
    r"\;": " ",
    r"\!": "",
    r"\ ": " ",
}

# Commands whose replacement text must NOT be eaten by the generic "strip remaining
# commands" pass. The strip regex matches a backslash plus letters, but it is greedy, so
# "\nabla" is consumed there and never reaches a later string substitution. The fix is to
# swap these for a backslash-free token first, strip, then put the final word back.
PRE = [(r"\nabla", "@@GRAD@@"), (r"\mathrm", "@@RM@@"),
       (r"\propto", "@@PROP@@"), (r"\exp", "@@EXP@@"),
       (r"\textbf", "@@BF@@"), (r"\noindent", "@@NI@@")]
POST = [("@@GRAD@@", "grad "), ("@@RM@@", ""),
        ("@@PROP@@", "proportional to "), ("@@EXP@@", "exp"),
        ("@@BF@@", ""), ("@@NI@@", "")]


def detex(s: str) -> str:
    for k, v in PRE:
        s = s.replace(k, v)
    for k, v in MATH.items():
        s = s.replace(k, v)
    # \emph{x} / \textit{x} / \texttt{x} -> x
    s = re.sub(r"\\[a-zA-Z]+\{([^{}]*)\}", r"\1", s)
    # ^ and _ scripts
    s = re.sub(r"\^\{([^{}]*)\}", r"^\1", s)
    s = re.sub(r"_\{([^{}]*)\}", r"_\1", s)
    # remaining commands
    s = re.sub(r"\\[a-zA-Z]+", "", s)
    # restore the placeholders
    for k, v in POST:
        s = s.replace(k, v)
    s = s.replace("$", "")
    s = s.replace("~", " ")
    s = re.sub(r"\{|\}", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(MAIN, encoding="utf-8", errors="replace").read()
    m = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", t, re.S)
    if not m:
        print("  abstract environment not found")
        return 1
    raw = m.group(1)
    # the abstract environment also holds the keywords line; separate them
    kw = re.search(r"\\noindent\s*\\textbf\{([^}]*)\}\s*(.*)$", raw, re.S)
    if kw:
        keywords = detex(kw.group(2))
        raw = raw[:kw.start()]
    else:
        keywords = ""
    txt = detex(raw)
    words = len(txt.split())
    print(f"  raw LaTeX: {len(raw)} characters")
    print(f"  plain text: {len(txt)} characters, {words} words  "
          f"({'OK' if words <= 250 else 'OVER 250'})")
    if keywords:
        print(f"  keywords ({len(keywords)} chars): {keywords}")
    print()
    print("=" * 100)
    print(txt)
    print("=" * 100)
    print()
    if any(ch in txt for ch in "\\${}"):
        print("  NOTE: residual LaTeX characters present")
    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(txt + "\n")
        print(f"  wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
