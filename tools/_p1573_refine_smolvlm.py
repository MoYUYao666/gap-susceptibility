# -*- coding: utf-8 -*-
"""Refine S44/S17 now that the SmolVLM sign change is stable across three seeds."""
import io

SUPP = "paper3/paper_ieee/supplementary/supplementary.tex"
t = io.open(SUPP, encoding="utf-8").read()

old_cap = ("SmolVLM-500M third-family control: the sign changes between $r=5$ and $r=6$ (means $%+.1f$ and $%+.1f$), but\n"
           "the $r=6$ effect is close to zero, so this control does not establish a robust crossing outside LLaVA-1.5; together with\n"
           "the Qwen2-VL-2B control (S41) it keeps the claim bounded.")
new_cap = ("SmolVLM-500M third-family control: the sign changes between $r=5$ and $r=6$ in every seed (means $%+.1f$ and\n"
           "$%+.1f$), so the crossing pattern is not exclusive to LLaVA-1.5; the $r=6$ magnitude is small and the Qwen\n"
           "controls (S20, S41) still bound the claim, so this is reported as a replication in a second family rather than\n"
           "as a universal property.")
if old_cap in t:
    t = t.replace(old_cap, new_cap, 1)
else:
    print("S44 caption pattern not found (check formatting)")
old_row = ("third-family crossing (SmolVLM-500M) & not established & sign change present but $r=6$ effect near zero "
           "(S44) \\\\")
new_row = ("crossing pattern in a second family (SmolVLM-500M) & replicated, small magnitude & sign change in three "
           "seeds; Qwen controls bound the scope (S44) \\\\")
if old_row in t:
    t = t.replace(old_row, new_row, 1)
else:
    print("S17 row pattern not found")
io.open(SUPP, "w", encoding="utf-8", newline="").write(t)
print("refined S44/S17")
