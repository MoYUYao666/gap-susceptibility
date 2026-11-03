# -*- coding: utf-8 -*-
r"""Simplify and correct the experiment-count claims: one denominator, one alpha-sign statement.

Operator decision (2026-10-17, option A): adopt the **96 per-run ODE fits** that are actually archived, and simplify the
number soup. The manuscript currently carries four mutually inconsistent counts:

  * 383 experiments (7 real sites) -- decomposition "221 catalogue + 162 ODE fits", but 162 fits were never archived;
  * 215 fits / 196 negative -- summed from a mixed audit that adds ledger 96 + LOCO 33 + LOCO2 33 (the same 33 twice) +
    Adapter 50 + BitFit 3;
  * 55 archived LoRA runs (correct, but a subset);
  * 96 per-run fits (`ode_ledger.json`, fully reproducible by `tools/_p1_ledger.py`).

After this pass the paper says, in total:

  * **317 experiments = 221 catalogued + 96 ODE fits**, stated once in the conclusion and once in the validation
    section; the abstract, introduction and empirical section drop the number and keep only the scope words;
  * **92 of 96 ODE fits have alpha < 0; the four exceptions are all Adapter fits** (LoRA 55/55 and full-FT 11/11 are
    negative), stated once;
  * the composition of the 96 (55 LoRA + 30 Adapter + 11 full-FT) appears once, in the appendix catalogue;
  * "55 LoRA runs (49 Flickr30k, 6 MS-COCO)" survives only where the fits are actually described.

    python tools/_p1179_simplify_counts.py [--apply]
"""
from __future__ import annotations

import argparse
import io
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SEC = REPO / "paper合" / "sections"
PA = REPO / "paper合"

CONC = SEC / "conclusion.tex"
VAL = SEC / "validation.tex"
INT = SEC / "introduction.tex"
EMP = SEC / "empirical.tex"
SUP = SEC / "supplement.tex"

EDITS = [
    # ---- conclusion ----
    (CONC, "spanning 383 experiments across six backbones",
     "spanning 317 experiments across six backbones"),
    (CONC, r"LoRA's protective effect from $\alpha < 0$ for 196 of the 215 archived fits",
     r"LoRA's protective effect from $\alpha < 0$ across the archived ODE fits"),
    (CONC,
     r"Across the $215$ fits we archived, $\alpha < 0$ in $196$; the $19$ exceptions are fourteen of the fifty Adapter "
     r"fits (largest $+0.061$), four LoRA fits fitted leave-one-configuration-out (largest $+0.011$) and all three "
     r"CLIP BitFit fits ($\alpha \approx +4\times10^{-4}$, i.e.\ numerically zero), so we state the protective bound "
     r"as the dominant rather than a universal regime, and $\beta$ is stable across PEFT and full fine-tuning under "
     r"matched settings ($\beta_{\text{full}} = 0.159$).",
     r"Across the $96$ archived ODE fits, $\alpha < 0$ in $92$; the four exceptions are all Adapter fits (largest "
     r"$+0.011$), so we state the protective bound as the dominant rather than a universal regime. $\beta$ is stable "
     r"across PEFT and full fine-tuning under matched settings ($\beta_{\text{full}} = 0.159$)."),
    (CONC, "we validated the ODE across 55 archived LoRA runs (49 on Flickr30k, 6 on MS-COCO), each fitted separately.",
     "we validated the ODE against the archived LoRA runs, each fitted separately."),
    # ---- validation ----
    (VAL, "validated by 383 experiments spanning", "validated by 317 experiments spanning"),
    (VAL,
     r"($196$ of the $215$ fits we archived), which supports the protective bound while leaving a minority of "
     r"counter-examples that we report in Section~\ref{sec:discussion} (fourteen Adapter fits up to $+0.061$, four "
     r"leave-one-configuration-out LoRA fits up to $+0.011$, and the three CLIP BitFit fits at "
     r"$\alpha \approx +4\times10^{-4}$).",
     r"($92$ of the $96$ fits we archived), which supports the protective bound while leaving a small minority of "
     r"counter-examples that we report in Section~\ref{sec:discussion} (four Adapter fits up to $+0.011$)."),
    (VAL, r"$\alpha$ is negative for $196$ of the $215$ archived fits on both Flickr30k and COCO",
     r"$\alpha$ is negative for $92$ of the $96$ archived fits on both Flickr30k and COCO"),
    # ---- introduction: drop the fragile totals, keep the scope words ----
    (INT, "This paper examines that suggestion across 383 experiments over six backbones",
     "This paper examines that suggestion across six backbones"),
    (INT, "spanning 383 experiments across three adaptation methods, six backbones, and two datasets",
     "spanning three adaptation methods, six backbones, and two datasets"),
    (INT, "We validate the ODE framework across 55 archived LoRA runs (49 on Flickr30k, 6 on MS-COCO) spanning the rank sweep",
     "We validate the ODE framework against the archived LoRA runs spanning the rank sweep"),
    # ---- empirical: "383 catalogued runs" was a third, contradictory meaning ----
    (EMP, "additional to the 383 catalogued runs", "additional to the experiments catalogued here"),
    # ---- appendix catalogue: the one place that states the composition ----
    (SUP, "a further 55 ODE-fitting runs are archived",
     "a further 96 ODE-fitting runs (55 LoRA, 30 Adapter and 11 full fine-tuning) are archived"),
    # ---- front matter / abstract of both builds ----
    (PA / "main_nc.tex", "Validation spans 383 experiments over six backbones and three adaptation methods",
     "Validation spans six backbones and three adaptation methods"),
    (PA / "main_springer.tex", "Validation spans 383 experiments over six backbones and three adaptation methods",
     "Validation spans six backbones and three adaptation methods"),
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    staged = {}
    for path, old, new in EDITS:
        txt = staged.get(path) or io.open(path, encoding="utf-8").read()
        n = txt.count(old)
        tag = path.name
        print(f"  {tag:<18} occ={n}  {old[:58]!r}")
        if n != 1:
            print("  !! expected exactly one occurrence; aborting")
            return 1
        staged[path] = txt.replace(old, new, 1)

    if not a.apply:
        print("\n  (dry run)")
        return 0
    for path, txt in staged.items():
        io.open(path, "w", encoding="utf-8", newline="").write(txt)
    print(f"\n  written {len(staged)} files")

    print("\n  === residual check ===")
    alltxt = "".join(io.open(p, encoding="utf-8").read()
                     for p in list(SEC.glob("*.tex")) + [PA / "main_nc.tex", PA / "main_springer.tex"])
    checks = [
        ("no '383 experiments'", "383 experiments" not in alltxt),
        ("no '$215$ fits'", "$215$ fits" not in alltxt),
        ("no '$196$ of'", "$196$ of" not in alltxt),
        ("no '19 exceptions'", "19$ exceptions" not in alltxt and "19 exceptions" not in alltxt),
        ("317 present", "317 experiments" in alltxt),
        ("92 of the 96 present", "$92$ of the $96$" in alltxt),
        ("96 composition in appendix once", alltxt.count("a further 96 ODE-fitting runs") == 1),
        ("old numeric 0.383 untouched", "0.383" in alltxt),
    ]
    for label, ok in checks:
        print(f"  {'OK  ' if ok else 'FAIL'} {label}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
