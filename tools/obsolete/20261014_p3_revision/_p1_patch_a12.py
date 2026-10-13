# -*- coding: utf-8 -*-
"""P1 patch A12: the Setup disclosure asserted a result the control had not produced yet
("the qualitative ordering of the positions is unchanged").  Dropped; the new section
states whatever the control actually shows."""
import io
import os
import sys

ROOT = r"D:\Realdesktop\Wan\Important\New"
OLD = "Section~\\ref{sec:strictcontrol} reports a control experiment in which every non-adapter parameter is frozen, isolating the adapter-only manipulation; the qualitative ordering of the positions is unchanged, and the corresponding limit is stated there."
NEW = "Section~\\ref{sec:strictcontrol} reports a control experiment in which every non-adapter parameter is frozen, isolating the adapter-only manipulation."
P = os.path.join(ROOT, "paper", "sections", "methodology.tex")
src = io.open(P, encoding="utf-8").read()
if src.count(OLD) != 1:
    print("FAIL: found %d" % src.count(OLD))
    sys.exit(1)
io.open(P, "w", encoding="utf-8", newline="").write(src.replace(OLD, NEW, 1))
print("PATCH A12 APPLIED")
