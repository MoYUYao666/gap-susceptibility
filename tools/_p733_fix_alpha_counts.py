# -*- coding: utf-8 -*-
r"""Rewrite Paper A's alpha-sign sentence to the counts the archive actually supports.

The paper says "across the 222 fits we archived, alpha < 0 in 203; the 19 exceptions are ten of the
fifty Adapter fits (largest +0.061), four LoRA fits (largest +0.011) and all three CLIP BitFit
fits".

The published archive holds 215 fits with an alpha: 196 negative and 19 non-negative. The
exception count and its largest value are unchanged (19, +0.060828 -> +0.061), but the total and
the negative count are not, and the family decomposition differs (14 adapter, 4 loco, 1 loco2 ...
in the auxiliary files) - so the old sentence cannot stand as written.

Why 215 and not 222: outputs/analysis/ode_ledger.json has a single commit and already held 96 runs
in it, so the 103-run revision the earlier audit recorded never existed in the repository. Seven
fits from an earlier development run are therefore absent and cannot be recovered.

The replacement names the five archived files, so a reader can reproduce the count exactly instead
of taking it on trust. That is the same standard the rest of the paper's data statement claims.

    python tools/_p733_fix_alpha_counts.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import re
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PA = REPO / "paper合"

# (file, old, new)
EDITS = [
    # conclusion.tex
    ("sections/conclusion.tex",
     r"Across the $222$ fits we archived, $\alpha < 0$ in $203$; the $19$ exceptions are ten "
     r"of the fifty Adapter fits (largest $+0.061$), four LoRA fits (largest $+0.011$) and all "
     r"three CLIP BitFit fits ($\alpha \approx +4\times10^{-4}$, i.e.\ numerically zero)",
     r"Across the $215$ fits we archived, $\alpha < 0$ in $196$; the $19$ exceptions are "
     r"fourteen of the fifty Adapter fits (largest $+0.061$), four LoRA fits fitted "
     r"leave-one-configuration-out (largest $+0.011$) and all three CLIP BitFit fits "
     r"($\alpha \approx +4\times10^{-4}$, i.e.\ numerically zero)"),
    # validation.tex, first occurrence
    ("sections/validation.tex",
     r"$\alpha$ is negative for the large majority of PEFT configurations ($203$ of the $222$ "
     r"fits we archived)",
     r"$\alpha$ is negative for the large majority of PEFT configurations ($196$ of the $215$ "
     r"fits we archived)"),
    ("sections/validation.tex",
     r"(ten Adapter fits up to $+0.061$, four LoRA fits up to $+0.011$, and the three CLIP "
     r"BitFit fits at $\alpha \approx +4\times10^{-4}$)",
     r"(fourteen Adapter fits up to $+0.061$, four leave-one-configuration-out LoRA fits up to "
     r"$+0.011$, and the three CLIP BitFit fits at $\alpha \approx +4\times10^{-4}$)"),
    ("sections/validation.tex",
     r"$\alpha$ is negative for $203$ of the $222$ archived fits on both Flickr30k and COCO",
     r"$\alpha$ is negative for $196$ of the $215$ archived fits on both Flickr30k and COCO"),
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    ok = True
    for rel, old, new in EDITS:
        p = PA / rel
        t = io.open(p, encoding="utf-8", errors="replace").read()
        n = t.count(old)
        print(f"  {rel:<28} occurrences={n}")
        if n != 1:
            ok = False
            print(f"     !! expected exactly one")
            if n:
                for m in re.finditer(re.escape(old), t):
                    ln = t[:m.start()].count("\n") + 1
                    print(f"        L{ln}")
            continue
        if a.apply:
            bak = p.with_suffix(p.suffix + ".bak_p733")
            if not bak.exists():
                shutil.copy2(p, bak)
            io.open(p, "w", encoding="utf-8", newline="").write(t.replace(old, new))
            print("     rewritten")
    if not a.apply:
        print("  (dry run)")
        return 0

    print()
    print("  residual check for the old numbers:")
    for rel in ("sections/conclusion.tex", "sections/validation.tex", "main_nc.tex"):
        t = io.open(PA / rel, encoding="utf-8", errors="replace").read()
        for num in ("222", "203", "215", "196"):
            for m in re.finditer(r"(?<![\d.])" + num + r"(?![\d.])", t):
                ln = t[:m.start()].count("\n") + 1
                seg = " ".join(t[max(0, m.start() - 90):m.start() + 90].split())
                if re.search(r"fit|alpha|archiv|R\^2|exception", seg, re.I):
                    print(f"     {rel}:{ln} [{num}] ...{seg[:170]}...")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
