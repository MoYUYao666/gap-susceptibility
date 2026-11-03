# -*- coding: utf-8 -*-
"""Print the remaining exact source fragments to be replaced (read-only helper)."""
import io

ROOT = r"D:\Realdesktop\Wan\Important\New\paper合\sections"

V = io.open(ROOT + r"\validation.tex", encoding="utf-8").read()
i = V.find("of the $215$ fits")
print("=== validation parenthetical ===")
print(repr(V[i - 40: i + 520]))
print()

I = io.open(ROOT + r"\introduction.tex", encoding="utf-8").read()
for tok in ("We validate the ODE framework across 55", "This paper examines that suggestion across 383",
            "spanning 383 experiments across three adaptation"):
    j = I.find(tok)
    print("===", tok[:40], "at", j, "===")
    print(repr(I[j: j + 260]))
    print()

SUP = io.open(ROOT + r"\supplement.tex", encoding="utf-8").read()
k = SUP.find("a further 55 ODE-fitting runs")
print("=== supplement sentence ===")
print(repr(SUP[k: k + 240]))
