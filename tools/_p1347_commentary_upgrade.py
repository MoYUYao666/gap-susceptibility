# -*- coding: utf-8 -*-
r"""Commentary upgrade: 2026 citations, scope paragraph, six-instance summary table, figure reference and PDF metadata.

Edits the *source* files (MANUSCRIPT.md, _refs_used.json, builder), then the builder regenerates main_prl.tex.

    python tools/_p1347_commentary_upgrade.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MD = os.path.join(REPO, "paper_review_prl", "MANUSCRIPT.md")
REFS = os.path.join(REPO, "paper_review_prl", "_refs_used.json")
BUILDER = os.path.join(REPO, "tools", "_build_prl_tex.py")

NEW_REFS = [
    {"key": "sharma2026readout", "authors": "Aditya Sharma, Divya Saxena",
     "title": "One Geometry, Different Outcomes: Readout-Dependent Effects of the Modality Gap in Vision-Language Models",
     "year": 2026, "venue": "arXiv preprint", "arxiv": "2609.36101"},
    {"key": "yaras2026explaining", "authors": "Can Yaras, Siyi Chen, Peng Wang, Qing Qu",
     "title": "Explaining and Mitigating the Modality Gap in Contrastive Multimodal Learning",
     "year": 2024, "venue": "arXiv preprint", "arxiv": "2412.07909"},
    {"key": "amblard2026quantifying", "authors": "Fran\u00e7ois Role, S\u00e9bastien Meyer, Victor Amblard",
     "title": "Quantifying and reducing the modality gap in both contrastive and generative multimodal vision-language models",
     "year": 2026, "venue": "International Journal of Multimedia Information Retrieval",
     "doi": "10.1007/s13735-026-00423-w"},
]

SCOPE = """

Three analyses published this year sharpen what the six instances are and are not about.
[sharma2026readout] decompose the image-text mean separation and show that modifying the gap changes
zero-shot classification and retrieval in opposite directions, because the mean-separation direction
enters each readout differently; [yaras2026explaining] trace the gap to the gradient flow of the
contrastive objective, where mismatched pairs and a learnable temperature keep it alive; and
[amblard2026quantifying] quantify the gap and its reduction across contrastive and generative models.
These explain *why* the gap matters to a model. This review is about *which reported number* a reader
can trust, and none of them supplies that; where such work bears on a reported comparison it is flagged
in the instance concerned.
"""

TABLE = """

Table 1 collects the six instances in one place, together with the checklist item that would have made
each comparison legitimate.

| Instance | What is usually reported | What is missing | Checklist item |
|---|---|---|---|
| Same model, same benchmark | a single accuracy, without the evaluation subset | which subset (POPE rand/pop/adversarial, MMBench split) | state the benchmark subset and version |
| Protocol change | scores from vanilla and circular protocols side by side | the protocol under which each number was obtained | report the evaluation protocol |
| Parameter count as budget | a trainable-parameter total | which components the budget was composed from | state the budget composition |
| Failure values | NaN or 0 without semantics | whether the run diverged, collapsed or was skipped | define failure semantics |
| Variance | a spread under an unstated convention | seeds, aggregation rule, reported statistic | state the variance convention |
| Freeze as baseline | a frozen model treated as neutral anchor | the initialisation regime and what it fixes | report the initialisation and freeze regime |
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    ops = []

    refs = json.load(io.open(REFS, encoding="utf-8"))
    have = {r["key"] for r in refs}
    add = [r for r in NEW_REFS if r["key"] not in have]
    print(f"  new references: {len(add)}")
    if add:
        refs = refs + add
        ops.append(("refs", REFS, json.dumps(refs, ensure_ascii=False, indent=1)))

    md = io.open(MD, encoding="utf-8").read()
    if "sharma2026readout" not in md:
        anchor = "where our reading rests on an inference rather than on data, we say so."
        assert md.count(anchor) == 1, md.count(anchor)
        md = md.replace(anchor, anchor + SCOPE, 1)
        anchor2 = "### 3.7 What a practitioner can still conclude"
        assert md.count(anchor2) == 1, md.count(anchor2)
        md = md.replace(anchor2, TABLE.strip() + "\n\n" + anchor2, 1)
        ops.append(("manuscript", MD, md))

    b = io.open(BUILDER, encoding="utf-8").read()
    if "pdftitle" not in b:
        old = '        BS + "usepackage{hyperref}",'
        assert b.count(old) == 1
        new = ('        BS + "usepackage{hyperref}",\n'
               '        BS + "hypersetup{pdftitle={" + latex_escape(title) + "}}",')
        b = b.replace(old, new, 1)
        old2 = "    body = md_to_tex(NL.join(lines[body_at:]))"
        assert b.count(old2) == 1
        b = b.replace(old2, old2 + '\n    body = body.replace("Figure 1", BS + "ref{fig:decision}")', 1)
        ops.append(("builder", BUILDER, b))

    print(f"  edits pending: {len(ops)}")
    for name, path, _ in ops:
        print("   -", name, "->", os.path.relpath(path, REPO))
    if not a.apply:
        print("  (dry run)")
        return 0
    for _, path, content in ops:
        io.open(path, "w", encoding="utf-8", newline="").write(content)
    print("  written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
