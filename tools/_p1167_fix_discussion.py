# -*- coding: utf-8 -*-
r"""Finish the E/G rewrite: fix the G note's framing and bring the main text's limitation paragraph in line.

Two edits, each asserted:

1. The closing paragraph of supplement G referred to "an earlier version of this section", which is meaningless to
   a reader of a manuscript that has not been submitted. It is replaced by a statement about *which representation
   is the text side*, arguing why the caption is the right choice and reporting what the alternative gives -- the
   same disclosure, framed as a measurement choice rather than as a document history.

2. `discussion.tex` still quotes the superseded numbers (18.0 / 66.5 / 87.9 and the 73.1-95.1 against 47.8-78.8
   overlap) and still calls the LLaVA run "a scoped null result". That paragraph is replaced with the corrected
   readings of both decoder experiments and the combined reading.

    python tools/_p1167_fix_discussion.py [--apply]
"""
from __future__ import annotations

import argparse
import io
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SUPP = REPO / "paper合" / "sections" / "supplement.tex"
DISC = REPO / "paper合" / "sections" / "discussion.tex"

OLD_G_NOTE = """A note on the earlier version of this section: it reported this model as a scoped null result, on a measurement
that took the instruction prompt as the text side (the sequence carried no caption) and gave a text-only arm
identical to frozen. The text side here is the caption, and the null is replaced by the ordering above. The
measurement convention matters as much as the model does, which is why both decoder tables now state the
construction explicitly."""

NEW_G_NOTE = """The choice of text side is not free, and we state it because this model is sensitive to it. These are
image--caption pairs, so the caption is the text the image is paired with; taking the instruction prompt instead
--- the sequence then carries no caption at all --- makes the text side depend on the image only through attention,
and the same adapters then give a text-only arm indistinguishable from frozen. We take the caption as the text side
throughout, which is also the convention of the dual-encoder experiments, and both decoder tables state the
construction for that reason."""

DISC_START = "Second, our study covers contrastive dual-encoder architectures and one decoder-based VLM."
DISC_END = "rather than as a contradiction."

NEW_DISC = r"""Second, our study covers contrastive dual-encoder architectures and two decoder-based VLMs. The
Qwen2-VL-2B model under strict freezing reproduces the framework's qualitative behaviour: the gap decays under every
arm, and adapting the vision tower alone is again the weakest choice, reducing the measured gap by
$89.4\pm1.0\%$ against $96.7\pm0.3\%$ for text-only and $98.6\pm0.4\%$ for both-positions over thirteen seeds, with
disjoint seed ranges and a centroid gap that ranks the arms identically
(Section~\ref{sec:vlm} of the supplement). The larger LLaVA-1.5-7B model was run under a generation objective
rather than a contrastive one, so its magnitudes are not comparable with those; there every arm widens the gap, and
the vision side widens it most ($+121.5\pm16.3\%$ against $+95.7\pm7.9\%$ and $+73.3\pm7.5\%$), with the text-only
and both-position spreads disjoint (Section~\ref{sec:llava} of the supplement). The two decoder experiments
therefore place the vision side in the same role from opposite directions: it is the arm that closes the gap least
when closing it is the objective, and the arm that widens it most when it is not, while the text side is the most
favourable in both. Our reading is that the vision side is the side through which the measured gap is least
controllable. The scope qualifications remain: two decoder models, small training sets, and a reading that depends
on the caption being defined as the text side --- with the instruction prompt as the text side the same adapters
give a text-only arm indistinguishable from frozen, which is why both decoder tables state their construction
explicitly."""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    t = io.open(SUPP, encoding="utf-8").read()
    n = t.count(OLD_G_NOTE)
    print(f"  supplement G note occurrences: {n}")
    if n != 1:
        print("  !! expected exactly one")
        return 1
    t = t.replace(OLD_G_NOTE, NEW_G_NOTE, 1)

    d = io.open(DISC, encoding="utf-8").read()
    i, j = d.find(DISC_START), d.find(DISC_END)
    print(f"  discussion anchors: start={i} end={j}")
    if not (0 <= i < j):
        print("  !! discussion anchors not found")
        return 1
    old_chunk = d[i:j + len(DISC_END)]
    print(f"  replacing {len(old_chunk)} chars of the limitation paragraph")
    d = d[:i] + NEW_DISC + d[j + len(DISC_END):]

    if not a.apply:
        print("  (dry run)")
        return 0
    io.open(SUPP, "w", encoding="utf-8", newline="").write(t)
    io.open(DISC, "w", encoding="utf-8", newline="").write(d)
    print("\n  written both files")
    s2 = io.open(SUPP, encoding="utf-8").read()
    d2 = io.open(DISC, encoding="utf-8").read()
    for label, cond in (
        ("supplement no longer says 'earlier version of this section'", "earlier version of this section" not in s2),
        ("supplement no longer says 'scoped null result'", "scoped null result" not in s2),
        ("discussion has the corrected E numbers", "89.4\\pm1.0" in d2),
        ("discussion has the corrected G numbers", "121.5\\pm16.3" in d2),
        ("discussion no longer quotes 87.9", "87.9" not in d2),
        ("discussion no longer quotes 66.5", "66.5" not in d2),
        ("discussion no longer says scoped null result", "scoped null result" not in d2),
        ("discussion cites both supplement sections", "sec:llava" in d2 and "sec:vlm" in d2),
    ):
        print(f"  {'OK  ' if cond else 'FAIL'} {label}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
