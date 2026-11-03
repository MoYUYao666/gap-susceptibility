# -*- coding: utf-8 -*-
r"""Create Paper A's standalone Abstract file and wire it into the package build.

Editorial Manager asks for the abstract as its own upload item for this journal. The text is extracted from
`paper合/main_nc.tex` (raw LaTeX, so the maths renders exactly as in the manuscript) into a standalone
`paper合/abstract_nc.tex`, compiled to `abstract_nc.pdf`, and copied into the package as `Abstract.pdf`. The package
builder `_p1169` is patched so a rebuild reproduces the file, and the audit profile records it.

    python tools/_p1247_add_abstract_file.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import os
import re
import shutil
import subprocess

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PA = os.path.join(REPO, "paper合")
PKG = os.path.join(REPO, "SUBMISSION", "PaperA_Neurocomputing")
BUILDER = os.path.join(REPO, "tools", "_p1169_refresh_nc_submission.py")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    tex = io.open(os.path.join(PA, "main_nc.tex"), encoding="utf-8").read()

    title = re.search(r"\\title\{", tex)
    i = title.start() + len(r"\title{")
    depth, j = 1, i
    while depth and j < len(tex):
        if tex[j] == "{":
            depth += 1
        elif tex[j] == "}":
            depth -= 1
        j += 1
    title_raw = tex[i:j - 1].strip()

    ab = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", tex, re.S)
    kw = re.search(r"\\begin\{keyword\}(.*?)\\end\{keyword\}", tex, re.S)
    assert ab and kw, "abstract/keyword block not found"
    abstract_raw = ab.group(1).strip()
    keyword_raw = kw.group(1).strip()

    standalone = r"""\documentclass[11pt]{article}
\usepackage[a4paper,margin=2.5cm]{geometry}
\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage{amsmath,amssymb}
\usepackage{url}
\usepackage{parskip}
\pagestyle{empty}
\newcommand{\sep}{\ \textbullet\ }

\begin{document}

\begin{center}
{\large\bfseries %s}
\end{center}

\section*{Abstract}

%s

\vspace{0.8em}
\noindent\textbf{Keywords:} %s

\end{document}
""" % (title_raw, abstract_raw, keyword_raw)

    out = os.path.join(PA, "abstract_nc.tex")
    print(f"  standalone abstract tex: {len(standalone)} chars")
    if not a.apply:
        print("  (dry run)")
        return 0
    io.open(out, "w", encoding="utf-8", newline="").write(standalone)

    for _ in range(2):
        r = subprocess.run(["pdflatex", "-interaction=nonstopmode", "abstract_nc.tex"], cwd=PA,
                           capture_output=True, text=True, timeout=600)
    log = io.open(os.path.join(PA, "abstract_nc.log"), encoding="utf-8", errors="ignore").read()
    errs = len(re.findall(r"^!", log, re.M))
    from pypdf import PdfReader
    npages = len(PdfReader(os.path.join(PA, "abstract_nc.pdf")).pages)
    words = len(re.findall(r"\b[A-Za-z][A-Za-z-]*\b", re.sub(r"\\[a-zA-Z]+|[{}$]", " ", abstract_raw)))
    print(f"  abstract_nc.pdf: {npages} page(s), LaTeX errors={errs}, approx words={words}")
    if errs or npages != 1:
        print("  !! abstract file failed validation")
        return 1

    shutil.copy2(os.path.join(PA, "abstract_nc.pdf"), os.path.join(PKG, "Abstract.pdf"))
    print("  installed package/Abstract.pdf")

    # patch the builder so a rebuild reproduces the file
    b = io.open(BUILDER, encoding="utf-8").read()
    anchor = """        for extra, portal_name in (("highlights_nc.pdf", "Highlights.pdf"),"""
    add = """        # standalone abstract item (Editorial Manager asks for it separately)
        for _ in range(2):
            subprocess.run(["pdflatex", "-interaction=nonstopmode", "abstract_nc.tex"], cwd=PA,
                           capture_output=True, text=True, timeout=600)
        shutil.copy2(PA / "abstract_nc.pdf", OUT / "Abstract.pdf")
        print("    Abstract.pdf <- abstract_nc.pdf")

"""
    if "Abstract.pdf <- abstract_nc.pdf" not in b:
        n = b.count(anchor)
        print(f"  builder anchor: {n}")
        assert n == 1
        b = b.replace(anchor, add + anchor, 1)
        io.open(BUILDER, "w", encoding="utf-8", newline="").write(b)
        print("  builder patched")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
