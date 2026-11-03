# -*- coding: utf-8 -*-
r"""Add the held-out validation figures that reviewers R1-W2, R3-2 and the AE asked for.

The paper already reports cluster-robust inference, a family-clustered bootstrap and a mixed
model, and its abstract refers to "a held-out analysis" without quoting numbers. The archive holds
the numbers: leave-one-family-out (12 folds, out-of-sample R2 0.449 pooled / 0.396 median, 8 of 12
folds beating the constant baseline) and leave-one-design-cell-out (6 folds, 0.236 / 0.227, 4 of 6).

Those are worth stating, including the unfavourable part: a third of the folds do not beat the
constant baseline, and the worst fold is SigLIP in both schemes. Reporting the cross-validated
figure without the per-fold spread is what drew the original criticism.

    python tools/_p744_add_holdout.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import re
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PA = REPO / "paper合"
PUB = REPO / "publish_clean"
OUT = REPO / "outputs" / "analysis" / "holdout_sentence.json"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    d = json.loads((PUB / "outputs/analysis/pr_stats_hardened.json").read_text(
        encoding="utf-8", errors="ignore"))
    ho = d["holdout"]
    fam = ho["leave_one_family_out"]
    cell = ho["leave_one_design_cell_out"]

    def r2(x):
        return f"{x:.3f}"

    def frac(x):
        return f"{int(round(x * 100))}\\%"

    sentence = (
        f"To check that this is not in-sample fitting, we refit the slope on training folds only "
        f"and evaluate it on held-out ones: leaving one experiment family out ({fam['n_folds']} "
        f"folds) gives an out-of-sample $R^2$ of ${r2(fam['r2_oos_pooled'])}$ pooled and "
        f"${r2(fam['r2_oos_median_fold'])}$ at the median fold, with "
        f"${frac(fam['frac_folds_beat_constant'])}$ of folds beating the training-fold constant "
        f"baseline; leaving one dataset$\\times$model cell out ({cell['n_folds']} folds) gives "
        f"${r2(cell['r2_oos_pooled'])}$ and ${r2(cell['r2_oos_median_fold'])}$, with "
        f"${frac(cell['frac_folds_beat_constant'])}$ of folds beating it. The association therefore "
        f"transfers, but not uniformly: in both schemes the weakest fold is SigLIP, where the "
        f"ordering is known to reverse, which is why we report an association with its per-fold "
        f"spread rather than a predictive relation."
    )
    print("=" * 108)
    print("sentence to insert")
    print("=" * 108)
    print("  " + sentence)
    print()

    target = PA / "sections" / "empirical.tex"
    t = io.open(target, encoding="utf-8", errors="replace").read()
    # anchor: the resampling-checks passage that governs the association
    anchors = [
        r"neither attenuates it toward zero\.",
        r"surviving within-family dependence; neither attenuates it toward zero\.",
    ]
    chosen = None
    for pat in anchors:
        m = re.search(pat, t)
        if m:
            chosen = m
            break
    if not chosen:
        print("  !! anchor not found in validation.tex")
        return 1
    print(f"  anchor found at line {t[:chosen.start()].count(chr(10)) + 1}:")
    print(f"     ...{' '.join(t[max(0, chosen.start() - 160):chosen.end() + 60].split())[:320]}...")
    print()
    if not a.apply:
        print("  (dry run)")
        return 0
    new = t[:chosen.end()] + " " + sentence + t[chosen.end():]
    bak = target.with_suffix(".tex.bak_p744")
    if not bak.exists():
        shutil.copy2(target, bak)
    io.open(target, "w", encoding="utf-8", newline="").write(new)
    print("  inserted")
    t2 = io.open(target, encoding="utf-8", errors="replace").read()
    for k in ("out-of-sample", f"{fam['n_folds']} folds", f"{cell['n_folds']} folds",
              "weakest fold is SigLIP"):
        print(f"  {'OK ' if k in t2 else 'BAD'} {k}")
    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(
            {"sentence": sentence, "family": fam, "cell": cell}, ensure_ascii=False, indent=1))
        print(f"  wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
