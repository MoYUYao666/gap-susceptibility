# -*- coding: utf-8 -*-
r"""Update the main text's supplement pointers to match the reordered supplement.

Section numbering after `tools/_p890`:

    S1 axiom derivation          S6 decoder VLM
    S2 experimental details      S7 downstream check
    S3 GFAP error bound          S8 transfer reasoning + companion ODE
    S4 per-block Gamma           S9 deferred proofs + related detail
    S5 rank scaling                 (comparison with prior work, ShareGPT, sample-size table)

So the main text's pointers become: sample-size S3 -> S9, second dataset S3 -> S9, rank scaling
S4 -> S5, comparison with prior work S5 -> S9; the downstream check already pointed at S7 and stays.
The summary sentence in `main.tex` said "Supplementary Sections S1--S6" and becomes "S1--S9".

Numbers only: no sentence of the manuscript changes. Each edit is anchored on the exact line read from
the file.

    python tools/_p891_p3_main_pointers.py [--apply]
"""
from __future__ import annotations

import argparse
import io
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
P3 = REPO / "paper3" / "paper_ieee"
EXP = P3 / "sections" / "experiments.tex"
MAIN = P3 / "main.tex"

# line numbers in sections/experiments.tex as audited on 2026-10-15
EDITS = [
    (187, "Supplementary Section~S3", "Supplementary Section~S9", "sample-size robustness"),
    (189, "Supplementary Section~S3", "Supplementary Section~S9", "second dataset (ShareGPT)"),
    (297, "Supplementary Section~S7", "Supplementary Section~S7", "downstream check (unchanged)"),
    (420, "Supplementary Section~S4", "Supplementary Section~S5", "rank scaling"),
    (425, "Supplementary Section~S5", "Supplementary Section~S9", "comparison with prior work"),
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    exp = EXP.read_text(encoding="utf-8")
    lines = exp.split("\n")
    for ln, old, new, why in EDITS:
        text = lines[ln - 1]
        assert old in text, f"line {ln} does not contain {old!r}: {text[:90]!r}"
        if old != new:
            lines[ln - 1] = text.replace(old, new, 1)
        print(f"  experiments.tex:{ln}  {old} -> {new}   ({why})")
    exp_out = "\n".join(lines)

    main_t = MAIN.read_text(encoding="utf-8")
    c = main_t.count("Supplementary Sections~S1--S6")
    assert c == 1, f"expected the S1--S6 range once in main.tex, found {c}"
    main_out = main_t.replace("Supplementary Sections~S1--S6", "Supplementary Sections~S1--S9", 1)
    print("  main.tex  Supplementary Sections~S1--S6 -> S1--S9   (summary sentence)")

    if not a.apply:
        print("  (dry run)")
        return 0

    EXP.write_text(exp_out, encoding="utf-8", newline="")
    MAIN.write_text(main_out, encoding="utf-8", newline="")

    check = EXP.read_text(encoding="utf-8").split("\n")
    for ln, _o, new, why in EDITS:
        assert new in check[ln - 1], f"line {ln} was not updated ({why})"
    assert "S1--S9" in MAIN.read_text(encoding="utf-8")
    print("  written and verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
