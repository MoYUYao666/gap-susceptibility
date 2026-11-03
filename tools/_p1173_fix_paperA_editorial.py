# -*- coding: utf-8 -*-
"""Fix the editorial defects in Paper A found by the independent read-only verification.

Fixes (all idempotent, asserted before and after):
  1. sections/discussion.tex - the duplicated "One consequence ... as an ordering." sentence
     (it appears twice back to back in the Twelfth limitation);
  2. sections/discussion.tex - limitations order: the paragraph block starting
     "Several limitations warrant discussion. First," must precede Tenth/Eleventh/Twelfth;
     the Tenth fragment ("... made at one shared learning rate") and its continuation
     (" rather than at each method's optimum, ...") are currently split by the Eleventh
     paragraph and are re-joined;
  3. sections/discussion.tex - "and and a collapse region" -> "and a collapse region";
  4. sections/discussion.tex - "rather than heuristic heuristics" -> "rather than heuristics";
  5. sections/empirical.tex - "ordering generaliz, because" -> "ordering generalizes, because";
  6. sections/supplement.tex - the both/vision mean separation is 2.01 pooled standard
     deviations (recomputed from outputs/canonical_caption_metric.json), not "one pooled
     standard deviation"; the wording is corrected accordingly.

    python tools/_p1173_fix_paperA_editorial.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DISC = REPO / "paper合" / "sections" / "discussion.tex"
EMPIR = REPO / "paper合" / "sections" / "empirical.tex"
SUPP = REPO / "paper合" / "sections" / "supplement.tex"

DUP_SENTENCE = (
    "One consequence is that the ordering of the two retrieval-strong arms in that table should "
    "not be pressed: the gap between CLIP B/32 both-position ($0.693$) and vision-only ($0.680$) "
    "is $0.013$, which is $1.7$--$2.4$ sampling standard deviations for a single evaluation, and "
    "about $1.5$ against the seed-to-seed spread of the same arms. We report the pair as "
    "unresolved rather than as an ordering."
)

SUBSECTION = "\\subsection{Limitations and Future Work}"
TENTH_HEAD = "Tenth, our cross-method comparison is made at one shared learning rate"
ELEVENTH_START = "Eleventh, the bottleneck Adapter"
TWELFTH_START = "Twelfth, the retrieval gallery"
FIRST_START = "Several limitations warrant discussion. First,"
NINTH_END = "should be read on that basis."
TENTH_TAIL_MARK = " rather than at each method's optimum, "

FAILS: list[str] = []


def need(cond: bool, msg: str) -> None:
    if not cond:
        FAILS.append(msg)
        print("FAIL  " + msg)


def find_line(lines: list[str], needle: str, startswith: bool = False) -> int:
    for i, ln in enumerate(lines):
        if (ln.startswith(needle) if startswith else ln.strip() == needle):
            return i
    return -1


def fix_discussion(text: str) -> str:
    n = text.count(DUP_SENTENCE)
    if n == 2:
        text = text.replace(DUP_SENTENCE + " " + DUP_SENTENCE, DUP_SENTENCE)
        print("  discussion: duplicate sentence removed")
    elif n == 1:
        print("  discussion: duplicate sentence already removed")
    else:
        need(False, f"discussion: expected 1 or 2 copies of the duplicated sentence, found {n}")

    lines = text.split("\n")
    i_sub = find_line(lines, SUBSECTION)
    i_twelfth = find_line(lines, TWELFTH_START, startswith=True)
    i_tenth = find_line(lines, TENTH_HEAD)
    i_eleventh = find_line(lines, ELEVENTH_START, startswith=True)
    i_first = find_line(lines, FIRST_START, startswith=True)
    i_ninth = find_line(lines, NINTH_END, startswith=False)
    # NINTH_END is the tail of the Ninth paragraph, not a whole line: find the line containing it.
    if i_ninth < 0:
        for i, ln in enumerate(lines):
            if ln.rstrip().endswith(NINTH_END):
                i_ninth = i
                break
    locs = {"subsection": i_sub, "Twelfth": i_twelfth, "Tenth": i_tenth, "Eleventh": i_eleventh,
            "First": i_first, "NinthEnd": i_ninth}
    need(all(v >= 0 for v in locs.values()), f"discussion: cannot locate all limitation markers: {locs}")
    if FAILS:
        return text

    ordered = i_first < i_tenth < i_eleventh < i_twelfth
    if ordered:
        print("  discussion: limitations already in First...Ninth, Tenth, Eleventh, Twelfth order")
        return "\n".join(lines)

    need(i_twelfth < i_tenth < i_eleventh < i_first <= i_ninth,
         "discussion: unexpected current limitation order: %s" % locs)

    ele = lines[i_eleventh]
    need(ele.count(TENTH_TAIL_MARK) == 1,
         "discussion: expected exactly one Tenth-continuation marker in the Eleventh paragraph")
    k = ele.index(TENTH_TAIL_MARK)
    eleventh = ele[:k].rstrip()
    tenth = lines[i_tenth].rstrip() + ele[k:]

    head = lines[: i_sub + 1]
    first_ninth = lines[i_first : i_ninth + 1]
    tail = lines[i_ninth + 1 :]
    while tail and tail[0].strip() == "":
        tail.pop(0)
    twelfth = lines[i_twelfth].strip()

    new = head + [""] + first_ninth + [""] + [tenth] + [""] + [eleventh] + [""] + [twelfth] + [""] + tail
    print("  discussion: limitations reordered to First...Ninth, Tenth, Eleventh, Twelfth")
    return "\n".join(new)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    disc = io.open(DISC, encoding="utf-8").read()
    disc2 = fix_discussion(disc)

    before = disc2
    disc2 = disc2.replace("and and a collapse region", "and a collapse region")
    if before != disc2:
        print("  discussion: 'and and' fixed")
    before = disc2
    disc2 = disc2.replace("rather than heuristic heuristics", "rather than heuristics")
    if before != disc2:
        print("  discussion: 'heuristic heuristics' fixed")

    empir = io.open(EMPIR, encoding="utf-8").read()
    empir2 = empir.replace("ordering generaliz, because", "ordering generalizes, because")
    if empir2 != empir:
        print("  empirical: 'generaliz' fixed")

    supp = io.open(SUPP, encoding="utf-8").read()
    old_pool = "in mean by a margin comparable to one pooled standard deviation"
    new_pool = "in mean by a margin of about two pooled standard deviations"
    supp2 = supp.replace(old_pool, new_pool)
    if supp2 != supp:
        print("  supplement: pooled-sd wording fixed (measured ratio 2.01)")

    # ---- assertions on the results -------------------------------------
    need(disc2.count(DUP_SENTENCE) == 1, "discussion: duplicated sentence count != 1 after fix")
    pos = [disc2.find(x) for x in (FIRST_START, TENTH_HEAD, ELEVENTH_START, TWELFTH_START)]
    need(all(p >= 0 for p in pos) and pos == sorted(pos),
         "discussion: First/Tenth/Eleventh/Twelfth order wrong after fix: %s" % pos)
    need("and and " not in disc2, "discussion: 'and and' still present")
    need("heuristic heuristics" not in disc2, "discussion: 'heuristic heuristics' still present")
    need("generaliz," not in empir2, "empirical: 'generaliz,' still present")
    need(old_pool not in supp2 and new_pool in supp2, "supplement: pooled-sd wording not fixed")
    need(supp2.count("about two pooled standard deviations") == 1,
         "supplement: unexpected count of the new pooled-sd phrase")

    if FAILS:
        print(f"\nRESULT: {len(FAILS)} failure(s); nothing written")
        return 1

    if a.apply:
        io.open(DISC, "w", encoding="utf-8", newline="").write(disc2)
        io.open(EMPIR, "w", encoding="utf-8", newline="").write(empir2)
        io.open(SUPP, "w", encoding="utf-8", newline="").write(supp2)
        print("\napplied: discussion.tex, empirical.tex, supplement.tex")
    else:
        print("\n(dry run; pass --apply to write)")

    # short before/after excerpt of the limitations opening
    i = disc2.find(SUBSECTION)
    print("\nlimitations opening after fix:\n" + disc2[i : i + 600].replace("\n", " | ")[:600])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
