# -*- coding: utf-8 -*-
r"""IEEEtran ignores \abovecaptionskip for table captions; insert an explicit gap between the tabular and \caption."""
import io
import re

P = "paper3/paper_ieee/supplementary/supplementary.tex"
t = io.open(P, encoding="utf-8").read()

if "\\tabcaptiongap" in t:
    print("already patched")
    raise SystemExit(0)

# define a macro in the preamble
marker = "\\usepackage{placeins}"
macro = "\\newcommand{\\tabcaptiongap}{\\vspace{4pt plus 1pt minus 1pt}}\n" + marker
t = t.replace(marker, macro, 1)

# insert the gap before every \caption that directly follows a tabular end inside a table float
pat = re.compile(r"(\\end\{tabular\*?\})\s*\n(\s*\\caption\{)")
t2, n = pat.subn(lambda m: m.group(1) + "\n\\tabcaptiongap\n" + m.group(2), t)
io.open(P, "w", encoding="utf-8", newline="").write(t2)
print("tabcaptiongap inserted before %d table captions" % n)