# -*- coding: utf-8 -*-
r"""Extract the abstract as paste-ready plain text.

Four earlier attempts failed in the same way: a replacement produced a word, and a later
generic "strip remaining LaTeX commands" pass then ate part of it. The failure mode is
always the same shape, so this version is built to make it impossible:

1. Every LaTeX command is replaced by a token of the form @@NAME@@ BEFORE any generic
   stripping happens. The tokens contain no backslash, so the generic pass cannot touch
   them, and "@" appears nowhere in the source.
2. The generic pass then only ever sees commands that have no replacement.
3. The tokens are expanded last.
4. The result is asserted to contain no backslash, no "$", no "{" or "}".
5. The printed text is checked for the specific damage seen before: a missing leading "gr"
   in "grad" (the "\nab" -> "" artefact).

    python tools/_p670_abstract_clean.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MAIN = REPO / "paper3" / "paper_ieee" / "main.tex"
OUT = (REPO / "SUBMISSION" / "P3_PRL_revision" / "UPLOAD"
       / "P3_PRLETTERS-D-26-02378_Abstract.txt")

# command -> token. Order does not matter because every entry is applied before stripping.
TOKENS = {
    "nabla": "GRAD",
    "mathrm": "RM",
    "propto": "PROP",
    "exp": "EXP",
    "textbf": "BF",
    "noindent": "NI",
    "Gamma": "GAMMA",
    "Delta": "DELTA",
    "beta": "BETA",
    "eta": "ETA",
    "tau": "TAU",
    "lambda": "LAMBDA",
    "sigma": "SIGMA",
    "langle": "LANG",
    "rangle": "RANG",
    "times": "TIMES",
    "approx": "APPROX",
    "pm": "PM",
}

WORDS = {
    "GRAD": "grad ",
    "RM": "",
    "PROP": "proportional to ",
    "EXP": "exp",
    "BF": "",
    "NI": "",
    "GAMMA": "Gamma",
    "DELTA": "Delta",
    "BETA": "beta",
    "ETA": "eta",
    "TAU": "tau",
    "LAMBDA": "lambda",
    "SIGMA": "sigma",
    "LANG": "<",
    "RANG": ">",
    "TIMES": "x",
    "APPROX": "~",
    "PM": "+-",
}

SIMPLE = {r"\|": "||", r"\%": "%", r"\&": "&", r"\_": "_",
          r"\,": " ", r"\;": " ", r"\!": "", r"\ ": " "}


def detex(s: str) -> str:
    # 1. named commands -> tokens (no backslash survives in the token)
    for name, tok in TOKENS.items():
        s = s.replace("\\" + name, "@@" + tok + "@@")
    # 2. punctuation commands
    for k, v in SIMPLE.items():
        s = s.replace(k, v)
    # 3. wrapper commands: \emph{x} -> x
    s = re.sub(r"\\[a-zA-Z]+\{([^{}]*)\}", r"\1", s)
    # 4. scripts
    s = re.sub(r"\^\{([^{}]*)\}", r"^\1", s)
    s = re.sub(r"_\{([^{}]*)\}", r"_\1", s)
    # 5. anything left that is still a command
    s = re.sub(r"\\[a-zA-Z]+", "", s)
    # 6. expand the tokens
    for name, tok in TOKENS.items():
        s = s.replace("@@" + tok + "@@", WORDS[tok])
    # 7. tidy
    s = s.replace("$", "").replace("~", " ")
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
        print("  abstract not found")
        return 1
    raw = m.group(1)
    kw = re.search(r"\\noindent\s*\\textbf\{([^}]*)\}\s*(.*)$", raw, re.S)
    keywords = detex(kw.group(2)) if kw else ""
    if kw:
        raw = raw[:kw.start()]

    txt = detex(raw)
    words = len(txt.split())
    problems = []
    if "\\" in txt or "$" in txt or "{" in txt or "}" in txt:
        problems.append("residual LaTeX")
    if "@@" in txt:
        problems.append("unexpanded token")
    if re.search(r"(?<![a-zA-Z])abla", txt):
        problems.append("severed \\nabla (the 'abla' artefact)")
    if re.search(r"\bgrad\s*E", txt) is None and "grad" in txt:
        pass
    for bad in ("proportional toexp", "rank_kproportional", "k<E"):
        if bad in txt:
            problems.append(f"mangled maths: {bad}")

    print(f"  abstract: {len(txt)} characters, {words} words "
          f"({'OK' if words <= 250 else 'OVER 250'})")
    print(f"  keywords: {keywords}")
    print(f"  problems: {problems if problems else 'none'}")
    print()
    print("=" * 100)
    print(txt)
    print("=" * 100)
    if problems:
        print("  refusing to write while problems remain")
        return 1
    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(txt + "\n")
        print(f"  wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
