# -*- coding: utf-8 -*-
r"""Give the Machine Learning build the appendix format its guide asks for.

The reframed draft carries the appendices as hand-lettered unnumbered sections
(``\section*{A. Complete Experiment Catalog}``, ``\section*{A.1 ...}``). Springer asks for real
appendix sections A, B, ... with decimal sub-numbering and separate numbering of tables, figures and
equations inside an appendix (Table A.1, Fig. A.1, Eq. (A.1)). All in-text references go through
``\ref``, so they update automatically - no manual remapping is needed.

The helper is applied to the two appendix section files at copy time, so a rebuild cannot regress it.
"""
import io
import os
import re

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
P = "tools/_p1720_build_ml_package.py"
t = io.open(P, encoding="utf-8").read()
if "def journal_appendix" in t:
    print("already wired")
    raise SystemExit(0)

FUNC = '''
def journal_appendix(text: str, first: bool) -> str:
    r"""Journal appendix format: real appendix sections with decimal sub-numbering and separate
    table/figure/equation numbers (Table A.1, Fig. A.1, Eq. (A.1)). References use \\ref, so they
    follow the new numbers automatically."""
    setup = ("\\\\appendix\\n"
             "\\\\counterwithin*{table}{section}\\\\counterwithin*{figure}{section}"
             "\\\\counterwithin*{equation}{section}\\n"
             "\\\\renewcommand{\\\\thetable}{\\\\Alph{section}.\\\\arabic{table}}\\n"
             "\\\\renewcommand{\\\\thefigure}{\\\\Alph{section}.\\\\arabic{figure}}\\n"
             "\\\\renewcommand{\\\\theequation}{\\\\Alph{section}.\\\\arabic{equation}}\\n")
    text = re.sub(r"\\\\section\\*\\{([A-Z])\\.(\\d+)\\s+([^}]*)\\}", lambda m: "\\\\subsection{" + m.group(3) + "}", text)
    text = re.sub(r"\\\\section\\*\\{([A-Z])\\.\\s+([^}]*)\\}", lambda m: "\\\\section{" + m.group(2) + "}", text)
    text = re.sub(r"\\\\section\\*\\{([^}]*)\\}", lambda m: "\\\\section{" + m.group(1) + "}", text)
    if first and "\\\\appendix" not in text:
        text = setup + text
    return text

'''

m = re.search(r"\ndef main\(", t)
assert m, "no def main()"
t = t[:m.start()] + FUNC + t[m.start():]

anchor = '        (SRC / f.name).write_text(t, encoding="utf-8", newline="\\n")'
assert anchor in t, "section write site not found"
inject = ('        if f.name.startswith(("95_", "96_")):\n'
          '            t = journal_appendix(t, first=f.name.startswith("95_"))\n')
t = t.replace(anchor, inject + anchor, 1)
io.open(P, "w", encoding="utf-8", newline="").write(t)
print("journal_appendix wired")
