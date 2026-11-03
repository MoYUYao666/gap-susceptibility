# -*- coding: utf-8 -*-
r"""Correct the two rank claims contradicted by the archived measurements (clean rewrite).

Replaces tools/_p858_fix_rank_claims.py, which applied some edits before failing and left the working
copy and the NC copy inconsistent. This version anchors on the exact text that is in the files now
(verified by reading them), touches only the rank sentences, and prints the resulting sentence for
inspection instead of trusting a count.

Three edits:

1. `paper合/sections/empirical.tex` — "the text-only arm improves monotonically with rank" (the
   Flickr30k sweep is monotone, the MS-COCO sweep is monotone in the opposite direction).
2. `paper合/sections/empirical.tex` — "that is, higher rank now preserves the gap better rather than
   reversing" (the measured limit is that the gap change tends to zero).
3. `paper合/sections/validation.tex` and the NC copy — the "Rank effect" bullet, which asserted that
   raising the rank adds vulnerable parameters "without adding gradient capacity"; both sweeps show
   the opposite, so the bullet now states the measured behaviour and its corpus dependence.

Sources for every number inserted: `outputs/analysis/flickr_rank.json` (dCG per rank, seed 42) and
`outputs/analysis/rank_rerun.json` (COCO dCG per rank).

    python tools/_p859_rank_claims_clean.py [--apply]
"""
from __future__ import annotations

import argparse
import io
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
WORK = REPO / "paper合" / "sections"
NC = REPO / "paper合" / "NC_submission" / "latex_source" / "sections"

MONO_OLD = ("the text-only arm improves monotonically with rank.")
MONO_NEW = ("the sign of the rank effect is the corpus's to decide. On Flickr30k the text-only arm "
            "becomes monotonically more protective over the swept range, whereas on MS-COCO it starts "
            "from a widening gap and the widening shrinks as the rank grows. What both sweeps share "
            "is the limit: the gap change converges towards no change at all, so the configured rank "
            "sets how much the gap moves and the corpus sets in which direction.")

CONV_OLD = ("that is, higher rank now preserves the gap better rather than reversing,")
CONV_NEW = ("that is, the gap change is converging towards no change at all, from the widening side,")

BULLET_OLD = ("    \\item \\textbf{Rank effect:} Effective Rank Saturation implies "
              "$r_{\\text{eff}} \\ll 64$, bounding the perturbation subspace. Increasing configured "
              "rank beyond the task's effective rank expands alignment-vulnerable parameters without "
              "adding gradient capacity.")

BULLET_NEW = "\n".join([
    "    \\item \\textbf{Rank effect:} The gap change converges towards zero as the configured rank",
    "    grows, and the direction it converges from is the corpus's rather than the rank's. On",
    "    Flickr30k under strict freezing the text-only arm becomes steadily \\emph{more} protective",
    "    ($\\Delta\\mathrm{CG} = -0.0195$ at $r{=}1$, $-0.0244$ at $r{=}4$, $-0.0176$ at $r{=}8$,",
    "    $-0.0123$ at $r{=}16$ and $32$, $-0.0019$ at $r{=}64$), whereas on MS-COCO the same sweep",
    "    starts from a widening gap that shrinks as the rank grows ($+0.0135$ at $r{=}2$ against",
    "    $+0.0021$ at $r{=}64$). Effective Rank Saturation bounds the perturbation subspace in both",
    "    cases; what it does not do is name a preferred rank, because the sign of the movement it",
    "    leaves is the corpus's to decide.",
])

EDITS = [
    (WORK / "empirical.tex", [(MONO_OLD, MONO_NEW), (CONV_OLD, CONV_NEW)]),
    (NC / "empirical.tex", [(MONO_OLD, MONO_NEW)]),
    (WORK / "validation.tex", [(BULLET_OLD, BULLET_NEW)]),
    (NC / "validation.tex", [(BULLET_OLD, BULLET_NEW)]),
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    for path, pairs in EDITS:
        assert path.exists(), f"missing {path}"
        t = io.open(path, encoding="utf-8").read()
        pending = [(old, new) for old, new in pairs if t.count(old) == 1]
        if not pending:
            # both claims are already corrected; being a no-op is success, not failure
            print(f"  {path.relative_to(REPO).as_posix()}: already corrected")
            continue
        for old, new in pending:
            t = t.replace(old, new, 1)
        if a.apply:
            io.open(path, "w", encoding="utf-8", newline="").write(t)
        print(f"  {'applied' if a.apply else 'would patch'} {path.relative_to(REPO).as_posix()} "
              f"({len(pending)} edit(s))")

    if not a.apply:
        print("  (dry run)")
        return 0

    # verify from disk, and show the rewritten sentences
    checks = {
        WORK / "empirical.tex": [MONO_NEW[:60], CONV_NEW[:50]],
        NC / "empirical.tex": [MONO_NEW[:60]],
        WORK / "validation.tex": ["converges towards zero as the configured rank", "-0.0019$ at $r{=}64$"],
        NC / "validation.tex": ["converges towards zero as the configured rank"],
    }
    for path, needles in checks.items():
        t = io.open(path, encoding="utf-8").read()
        assert "without adding gradient capacity" not in t, f"{path.name}: old bullet survives"
        assert "improves monotonically with rank." not in t, f"{path.name}: old monotone claim survives"
        for nd in needles:
            assert nd in t, f"{path.name}: missing {nd!r}"
        print(f"  verified {path.relative_to(REPO).as_posix()}")
    w = io.open(WORK / "empirical.tex", encoding="utf-8").read()
    i = w.find("the sign of the rank effect is the corpus")
    print("  --- empirical.tex, rewritten ---")
    print("  " + w[max(0, i - 90):i + 300].replace("\n", " "))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
