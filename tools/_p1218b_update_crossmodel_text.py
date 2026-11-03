# -*- coding: utf-8 -*-
"""Replace the SigLIP sentence using a whitespace-tolerant regex (the source line breaks differ from the guess)."""
import ast
import io
import os
import re

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAIN = os.path.join(REPO, "paper_a1", "main.tex")

PAT = re.compile(r"SigLIP base-patch16-224 could not be scored.*?so we do not report a SigLIP row\.", re.S)

NEW = (r"SigLIP base-patch16-224 reproduces the same direction once its text tower is pooled at the maximum length the"
       "\n"
       r"model was trained with (with the shorter default padding its zero-shot baseline collapses to $1.86\%$ and the row is"
       "\n"
       r"meaningless): the frozen model sits at $\mathrm{CG}=1.116$ with $73.3\%$ top-1, and contraction at $a=0.5$ raises"
       "\n"
       r"\emph{both} to $1.168$ and $88.3\%$ ($+15.0$ points, against $+19.0$ on CLIP and $+19.4$ on OpenCLIP). The"
       "\n"
       r"return-branch dissociation is present on all three models but needs a larger gap difference to appear on SigLIP: at"
       "\n"
       r"$\Delta\mathrm{CG}=0.197$ it carries $27.1$ points ($\lambda=0.5$: $\mathrm{CG}=0.551$, $64.8\%$; $\lambda=2$:"
       "\n"
       r"$\mathrm{CG}=0.354$, $37.7\%$)---the same $27.1$ points OpenCLIP shows at $0.066$.")

t = io.open(MAIN, encoding="utf-8").read()
hits = PAT.findall(t)
print("  matches:", len(hits))
assert len(hits) == 1, "expected exactly one SigLIP sentence"
t = PAT.sub(lambda _m: NEW, t, count=1)
io.open(MAIN, "w", encoding="utf-8", newline="").write(t)
ast.parse("pass")
print("  replaced; length", len(t))
