# -*- coding: utf-8 -*-
r"""Remove the duplicate appendix headings.

The reframed appendix files carry two competing numbering schemes: hand-lettered unnumbered headings
(``\subsection*{I.4 The LoRA configuration space ...}``) immediately followed by the real descriptive heading
(``\subsection{LoRA Configuration Space}``). In the built PDF this printed two headings in a row with mismatched
numbers ("I.4 ..." next to "K.3 ..."). Fix at the builder level so a rebuild cannot regress:

  1. a manual lettered sub-heading followed by a real ``\subsection`` is dropped (the real one stays);
  2. a manual lettered sub-heading with no real twin becomes a real ``\subsection`` with the prefix stripped.
"""
import io
import os
import re

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
P = "tools/_p1720_build_ml_package.py"
t = io.open(P, encoding="utf-8").read()

m = re.search(r"\ndef journal_appendix\(text: str, first: bool\) -> str:.*?(?=\ndef )", t, re.S)
assert m, "journal_appendix not found"

NEW = '''
def journal_appendix(text: str, first: bool) -> str:
    r"""Journal appendix format plus duplicate-heading cleanup.

    - real appendix sections A, B, ... with decimal sub-numbering instead of hand-lettered `section*` headings;
    - separate table/figure/equation numbering inside an appendix;
    - one heading per block: a hand-lettered `subsection*{I.4 ...}` is dropped when the real descriptive
      `subsection{...}` follows it, and converted to a real subsection otherwise.
    """
    setup = ("\\\\appendix\\n"
             "\\\\counterwithin*{table}{section}\\\\counterwithin*{figure}{section}"
             "\\\\counterwithin*{equation}{section}\\n"
             "\\\\renewcommand{\\\\thetable}{\\\\Alph{section}.\\\\arabic{table}}\\n"
             "\\\\renewcommand{\\\\thefigure}{\\\\Alph{section}.\\\\arabic{figure}}\\n"
             "\\\\renewcommand{\\\\theequation}{\\\\Alph{section}.\\\\arabic{equation}}\\n")
    # 1) drop a hand-lettered sub-heading that is immediately followed by the real one
    text = re.sub(r"\\\\subsection\\*\\{[A-Z]\\.\\d+[^}]*\\}\\s*(?=\\\\subsection\\{)", "", text)
    # 2) anything still hand-lettered becomes a real subsection, prefix stripped
    text = re.sub(r"\\\\subsection\\*\\{[A-Z]\\.(\\d+)\\s+([^}]*)\\}", lambda m: "\\\\subsection{" + m.group(2) + "}", text)
    # 3) sections: numbered appendix sections replace the hand-lettered ones
    text = re.sub(r"\\\\section\\*\\{([A-Z])\\.(\\d+)\\s+([^}]*)\\}", lambda m: "\\\\subsection{" + m.group(3) + "}", text)
    text = re.sub(r"\\\\section\\*\\{([A-Z])\\.\\s+([^}]*)\\}", lambda m: "\\\\section{" + m.group(2) + "}", text)
    text = re.sub(r"\\\\section\\*\\{([^}]*)\\}", lambda m: "\\\\section{" + m.group(1) + "}", text)
    if first and "\\\\appendix" not in text:
        text = setup + text
    return text

'''

t = t[:m.start()] + NEW + t[m.end():]
io.open(P, "w", encoding="utf-8", newline="").write(t)
print("journal_appendix replaced with the duplicate-heading-aware version")
