# -*- coding: utf-8 -*-
r"""Remove the two hyperref warnings the Springer build reports.

1. `bookmark levels` warning: the class does not load `bookmark`, so an outline jump between levels is repaired with a
   warning. Loading `bookmark` plus `bookmarksdepth=3` makes the outline consistent (headings here never go deeper
   than three levels, which is also the journal's rule).
2. `Token not allowed in a PDF string (Unicode): removing math shift`: headings that contain `$...$` are put into the
   PDF outline as raw strings. Wrap each math run in `\texorpdfstring{$...$}{plain}` so the outline gets plain text.

Both fixes are applied at copy time inside the ML package builder, so a rebuild cannot regress them.
"""
import io
import os
import re

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
P = "tools/_p1720_build_ml_package.py"
t = io.open(P, encoding="utf-8").read()

helper = '''
def pdfstring_headings(text: str) -> str:
    r"""Wrap math inside sectioning titles in \\texorpdfstring so the PDF outline stays plain text."""
    def wrap_math(m):
        title = m.group(3)
        def one_seg(mm):
            maths = mm.group(1)
            plain = re.sub(r"[^0-9A-Za-z]+", " ", maths).strip() or "formula"
            return "\\\\texorpdfstring{$%s$}{%s}" % (maths, plain)
        title = re.sub(r"\\$([^$]*)\\$", one_seg, title)
        return "\\\\" + m.group(1) + "{" + title + "}"
    return re.sub(r"\\\\(section|subsection|subsubsection|paragraph)\\{([^{}]*\\$[^{}]*)\\}", wrap_math, text)

'''

if "def pdfstring_headings" not in t:
    m = re.search(r"\ndef main\(", t)
    assert m, "no def main() in the builder"
    t = t[:m.start()] + helper + t[m.start():]

anchor = '        (SRC / f.name).write_text(t, encoding="utf-8", newline="\\n")'
assert anchor in t, "section write site missing"
inject = "        t = pdfstring_headings(t)\n"
if inject not in t:
    t = t.replace(anchor, inject + anchor, 1)

# preamble: load bookmark and cap the outline depth at three levels (also the journal's heading rule)
pre = r"\documentclass[pdflatex,sn-mathphys-num,onecolumn,oneside]{sn-jnl}"
if "\\\\usepackage{bookmark}" not in t:
    t = t.replace(pre, pre + "\n\\usepackage{bookmark}\n\\hypersetup{bookmarksdepth=3}", 1)

io.open(P, "w", encoding="utf-8", newline="").write(t)
print("builder patched: bookmark package, outline depth 3, texorpdfstring for math in headings")
