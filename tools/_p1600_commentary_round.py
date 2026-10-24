# -*- coding: utf-8 -*-
r"""Apply the Commentary round: 13 verified prose cuts, the two-decisions table, and Figure 1 retirement.

Sources: `docs/commentary_compression_and_table.md` (cuts §2, table §3.2, placement §3.6).
Edits `paper_review_prl/MANUSCRIPT.md` (the builder's source) and `tools/_build_prl_tex.py`.

    python tools/_p1600_commentary_round.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import os
import re

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(REPO)
MD = "paper_review_prl/MANUSCRIPT.md"
BUILDER = "tools/_build_prl_tex.py"

CUTS = [
    # C1 (delete a sentence)
    ("The sites available for adaptation are not interchangeable; the choice is constrained by architecture and task data.",
     ""),
    # C2
    ("The two settings answer different questions and their results do not transfer: a method that improves ImageNet "
     "transfer has not thereby been shown to improve instruction following.",
     "Their results do not transfer: a method that improves ImageNet transfer has not thereby been shown to improve "
     "instruction following."),
    # C3
    ("This strategy is attractive because it is the only one that can in principle transfer across base models; the "
     "evidence that it does so remains thin, and we return to this in §3.6.",
     "This strategy is attractive because it is the only one that can in principle transfer across base models, though "
     "the evidence that it does so remains thin."),
    # C4
    ("Each is stated so that a reader can check it against the cited sources; where our reading rests on an inference "
     "rather than on data, we say so.",
     "Where our reading rests on an inference rather than on data, we say so."),
    # C5
    ("The two papers may be reporting the same quantity, or different quantities; the published text does not determine "
     "which. We deliberately do not claim that the values disagree, because that claim would require knowing the "
     "evaluation protocol of the second paper, which is precisely what is missing. The instance is useful for what it "
     "demonstrates: comparing these numbers across papers is not a legitimate operation, and the reason is a reporting "
     "omission rather than an error.",
     "The two papers may be reporting the same quantity or different quantities; the published text does not determine "
     "which. We do not claim that the values disagree: that would require the second paper's evaluation protocol, which "
     "is precisely what is missing. Comparing these numbers across papers is therefore not a legitimate operation, for "
     "a reason of omission rather than error."),
    # C6
    ("The remedy is trivial — state the number of runs and the convention — and its absence is a common reason why "
     "otherwise careful results cannot be re-used. A comparison whose dispersion convention is unstated cannot be "
     "combined with another.",
     "The remedy is trivial — state the number of runs and the convention — and without it an otherwise careful "
     "comparison cannot be combined with another."),
    # C7
    ("This instance is a direct consequence of the siting decision of §2.1: without a stated site, the description of "
     "what was adapted is incomplete.",
     "This instance follows from the siting decision of §2.1: without a stated site, the description is incomplete."),
    # C8 (delete the bold lead-in paragraph)
    ("**How the items map onto the failures of §3.** The correspondence is one to one, which is the justification for "
     "each item's inclusion rather than an appeal to good practice in general.",
     ""),
    # C9
    ("The list cannot be shortened much further: items 5 and 6 look like one until one notices that a paper can state "
     "its rank while leaving the division unstated, and items 9 and 10 separate a design fact from a reporting "
     "convention.",
     "The list cannot be shortened much further: a paper can state its rank while leaving the division unstated "
     "(items 5 and 6), and items 9 and 10 separate a design fact from a reporting convention."),
    # C10
    ("**From aspiration to acceptance test.** Each item can be checked by a reader in a minute: item 1 requires the "
     "exact checkpoint (not just the model family); item 4 an absolute parameter count as well as a fraction; item 5 "
     "the rank array or the word ``uniform''; item 9 the number of runs and the dispersion convention. A paper that "
     "passes these tests enters a comparison table without correspondence with its authors, which is the operational "
     "meaning of the reporting standard.",
     "**From aspiration to acceptance test.** Each item can be checked by a reader in a minute; a paper that passes "
     "them enters a comparison table without correspondence with its authors, which is the operational meaning of the "
     "reporting standard."),
    # C11
    ("The instances are not allegations of error: in each case the information needed for comparison is absent rather "
     "than wrong, and the checklist in §4 is the minimum that removes these obstacles.",
     "The instances are not allegations of error: the information needed for comparison is absent rather than wrong."),
    # C12
    ("The two are governed by different variables — architecture and data volume for the first, the target metric for "
     "the second — and they are routinely conflated, which is why many published numbers cannot share a table.",
     "The two are governed by different variables — architecture and data volume for the first, the target metric for "
     "the second — and they are routinely conflated."),
    # C13
    ("And it is argumentative rather than systematic: the instances in §3 are individual cases chosen because each is "
     "checkable against its source, not a sample from which frequencies can be estimated.",
     "It is argumentative rather than systematic: the instances in §3 are cases checkable against their sources, not a "
     "sample (§3.7)."),
]

TABLE = """
**Table 2.** Adaptation families on the two decisions. Placements follow the sources cited in the last
column and the statements of §2.1 and §2.2; where a family defines no rule for dividing a parameter
budget, the third column says so rather than assigning a strategy.

| Family | Where capacity goes | How the budget is divided | Cited as |
|---|---|---|---|
| LoRA / DoRA | Language backbone; vision encoder frozen | Uniform rank across the targeted projections | [hu2021lora; liu2024dora] |
| AdaLoRA / ARD-LoRA | Language backbone, the low-rank family's usual site | Estimated importance: rank raised where updates are large | [zhang2023adalora; shinwari2026ardlora] |
| VPT / SSF | Visual encoder: prompt vectors; feature scaling and shifting | Uniform: the same configuration in every module | [jia2022vpt; lian2022ssf] |
| Encoder-side bottlenecks | Encoder feed-forward path; feature side of either branch | Not determinable from the cited sources: no allocation rule | [chen2022adaptformer; jie2022convpass; gao2024clipadapter] |
| Projector redesign | Projector | Not a parameter division: the knob is the visual-token count | [cha2024honeybee; li2025tokenpacker] |
| Search-based | Selected by the search, so it spans sites | Search over the configuration | [zhou2024autopeft; liu2022ia3] |
"""

FIG_OLD = ("Figure 1 sketches the two decisions as a plane and places representative methods within it. The figure "
           "makes the independence visible: a single site --- the language backbone --- is occupied by methods that "
           "differ only in how they divide their budget, and a single allocation strategy appears at more than one "
           "site. The next section turns to what this structure implies for the evidence.")
FIG_NEW = ("The table makes the independence visible: a single site --- the language backbone --- is occupied by "
           "methods that differ only in how they divide their budget, and a single allocation strategy appears at "
           "more than one site. The next section turns to what this structure implies for the evidence.")

ANCHOR = "parameters within it. Four strategies recur."


def rx(s: str) -> re.Pattern:
    """Match a quoted passage regardless of how the Markdown wraps it."""
    return re.compile(r"\s+".join(re.escape(w) for w in s.split()))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(MD, encoding="utf-8").read()
    words0 = len(re.findall(r"[A-Za-z][A-Za-z-]*", t))

    for i, (old, new) in enumerate(CUTS, 1):
        pat = rx(old)
        m = pat.search(t)
        assert m, "cut C%d pattern not found" % i
        t = t[:m.start()] + new + t[m.end():]
    print("cuts applied:", len(CUTS))

    assert rx(FIG_OLD).search(t), "Figure-1 paragraph not found"
    t = rx(FIG_OLD).sub(lambda _m: FIG_NEW, t, count=1)

    assert ANCHOR in t, "table anchor not found"
    t = t.replace(ANCHOR, ANCHOR + "\n" + TABLE, 1)

    assert "**Table 2.** How the checklist items map" in t, "checklist-mapping caption not found"
    t = t.replace("**Table 2.** How the checklist items map", "**Table 4.** How the checklist items map", 1)

    words1 = len(re.findall(r"[A-Za-z][A-Za-z-]*", t))
    print("words %d -> %d (%+d)" % (words0, words1, words1 - words0))
    assert "Figure 1" not in t, "a Figure 1 reference survives"

    if a.apply:
        io.open(MD, "w", encoding="utf-8", newline="").write(t)

    b = io.open(BUILDER, encoding="utf-8").read()
    old_line = '    body = body.replace("Figure 1", BS + "ref{fig:decision}")\n'
    assert old_line in b, "builder Figure-1 replace line not found"
    b = b.replace(old_line, "", 1)
    assert "\n    FIGURE,\n" in b, "builder FIGURE insertion not found"
    b = b.replace("\n    FIGURE,\n", "\n", 1)
    if a.apply:
        io.open(BUILDER, "w", encoding="utf-8", newline="").write(b)
    print("builder: Figure 1 retired (constant left defined but unused)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())