# -*- coding: utf-8 -*-
r"""Add the LLaVA reference, and point the main text's limitation paragraph at the new supplement section.

`paper合/references.bib` has no LLaVA entry, and the supplement section cites it, so the build would leave an
undefined citation. The main text already discusses the decoder model in its limitations; one sentence is
appended there so the new section is reachable from the body rather than orphaned in the supplement.

    python tools/_p1056_llava_ref_and_pointer.py [--apply]
"""
from __future__ import annotations

import argparse
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
BIB = REPO / "paper合" / "references.bib"
DISC = REPO / "paper合" / "sections" / "discussion.tex"

BIB_ENTRY = r"""
@inproceedings{liu2023llava,
  title     = {Visual Instruction Tuning},
  author    = {Liu, Haotian and Li, Chunyuan and Wu, Qingyang and Lee, Yong Jae},
  booktitle = {Advances in Neural Information Processing Systems},
  volume    = {36},
  pages     = {34892--34916},
  year      = {2023}
}
"""

# appended to the limitation item that discusses the decoder model, so the new section is cited from the body
POINTER = (" A larger decoder model, LLaVA-1.5-7B, was run under the same strict-freezing protocol; its "
           "text-only arm does not move the metric at all, but the pipeline that could run on the available "
           "device measures a different gap definition, so we report it as a scoped null result with its "
           "reason in Section~\\ref{sec:llava} of the supplement rather than as a contradiction.")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    bib = BIB.read_text(encoding="utf-8")
    disc = DISC.read_text(encoding="utf-8")

    need_bib = "liu2023llava" not in bib
    need_ptr = "sec:llava" not in disc
    print(f"  bibliography entry needed: {need_bib}")
    print(f"  main-text pointer needed:  {need_ptr}")
    if not (need_bib or need_ptr):
        print("  already done")
        return 0
    if not a.apply:
        print("  (dry run)")
        return 0

    if need_bib:
        BIB.write_text(bib.rstrip("\n") + "\n" + BIB_ENTRY, encoding="utf-8", newline="")
        print("  added liu2023llava to references.bib")

    if need_ptr:
        # the sentence goes at the end of the limitation item that mentions the decoder model
        key = "The decoder results above are therefore bfloat16, which reproduces bit for bit."
        assert disc.count(key) == 1, "the anchor sentence was not found exactly once"
        disc = disc.replace(key, key + POINTER, 1)
        DISC.write_text(disc, encoding="utf-8", newline="")
        print("  added the pointer to Section F in the limitations paragraph")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
