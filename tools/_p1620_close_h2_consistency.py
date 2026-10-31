# -*- coding: utf-8 -*-
r"""Close two consistency items the Section H.2 round flagged:

1. `provenance_appendix.tex` claims to list every results float but has no `tab:decoderladder` row.
2. The Data availability sentence names only Appendix Sections E and G; Section H.2's archives are on the public
   repository (main) and are NOT in the v2.3 deposit, so the sentence must say that precisely instead of implying
   the deposit covers them.
"""
import io
import os
import re

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(REPO)

# --- 1. appendix row -------------------------------------------------------------------------------
p = "paper合/sections/provenance_appendix.tex"
t = io.open(p, encoding="utf-8").read()
if "tab:decoderladder" not in t:
    lines = t.splitlines()
    idx = None
    for i, ln in enumerate(lines):
        if ln.lstrip().startswith("\\raggedright tab:vlm"):
            idx = i
            break
    assert idx is not None, "no tab:vlm row to anchor on"
    # find the end of that row (it may wrap over several physical lines, ending with the row terminator)
    end = idx
    while end < len(lines) and "\\\\" not in lines[end]:
        end += 1
    row = ("\\raggedright tab:decoderladder & \\raggedright\\path{tools/_p1612_objective_control_multimodel.py} & "
           "\\raggedright\\path{decoder_attribution_*.json} & verified \\\\")
    lines.insert(end + 1, row)
    io.open(p, "w", encoding="utf-8", newline="").write("\n".join(lines) + "\n")
    print("appendix row added after line", end + 1)

# --- 2. Data availability -------------------------------------------------------------------------
nc_old = ("(v2.3, 24 October 2026), which includes the decoder-model records of Appendix Sections E and G")
nc_new = ("(v2.3, 24 October 2026), which includes the decoder-model records of Appendix Sections E and G; the "
          "matched-ladder records of Appendix Section H.2 are on the public repository\n"
          "(\\url{https://github.com/MoYUYao666/gap-susceptibility}), which carries them at and after that release")
q = "paper合/main_nc.tex"
s = io.open(q, encoding="utf-8").read()
if nc_old in s:
    io.open(q, "w", encoding="utf-8", newline="").write(s.replace(nc_old, nc_new, 1))
    print("main_nc data availability updated")
else:
    print("WARNING: main_nc sentence not matched")

sp_old = "(version DOI \\texttt{10.5281/zenodo.23609295}; v2.3, 24 October 2026), which includes the decoder-model records of Appendix Sections E and G."
sp_new = ("(version DOI \\texttt{10.5281/zenodo.23609295}; v2.3, 24 October 2026), which includes the decoder-model "
          "records of Appendix Sections E and G; the matched-ladder records of Appendix Section H.2 are on the public "
          "repository (\\url{https://github.com/MoYUYao666/gap-susceptibility}).")
r = "paper合/main_springer.tex"
s = io.open(r, encoding="utf-8").read()
if sp_old in s:
    io.open(r, "w", encoding="utf-8", newline="").write(s.replace(sp_old, sp_new, 1))
    print("main_springer data availability updated")
else:
    print("WARNING: springer sentence not matched")