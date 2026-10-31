# -*- coding: utf-8 -*-
"""Print the exact source sentences that the simplification pass will replace (read-only helper)."""
import io

S = io.open(r"D:\Realdesktop\Wan\Important\New\paper合\sections\conclusion.tex", encoding="utf-8").read()

for token in ("Across the $215$ fits", "protective effect from"):
    i = S.find(token)
    print("===", token, "at", i, "===")
    print(repr(S[max(0, i - 80): i + 620]))
    print()

V = io.open(r"D:\Realdesktop\Wan\Important\New\paper合\sections\validation.tex", encoding="utf-8").read()
for token in ("validated by 383", "of the $215$ fits", "of the $215$ archived"):
    i = V.find(token)
    print("===", token, "at", i, "===")
    print(repr(V[max(0, i - 120): i + 260]))
    print()
