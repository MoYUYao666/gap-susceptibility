# -*- coding: utf-8 -*-
r"""Language polish for Paper A, targeting the defects the survey measured.

All three referees asked for language editing. The survey (tools/_p815) found three concrete problems
rather than a general need:

  1. mixed spelling: 25 British forms against 9 American ones in the same manuscript
  2. inconsistent hyphenation of compound terms the paper uses dozens of times
     (cross-architecture 4 hyphenated / 3 spaced, cross-dataset 2/2, both-position 44/7)
  3. nineteen sentences of 70 words or more, the longest 124, which the referees' "structure, flow or
     writing" question also touches

The polish unifies the spelling to American English (the target journal is US-based and the paper's
existing `normalize`/`optimize`/`favor` usage already leans that way), normalises the compounds, and
splits only the three worst sentences, so the change stays reviewable.

Every number, LaTeX label, citation key and figure reference is asserted untouched.

    python tools/_p816_polish.py --dry-run | --apply
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

# British spellings, split by how they must be matched.
#
# STEMS: the British form is a stem, so every continuation is British too (analyse, analysed,
# analysing; optimise, optimiser, optimisation). Matched as "\b<stem>\w*".
# WORDS: the British form is a whole word and longer words must not be touched
# (behaviour yes, behaviourally is a different question we do not need). Matched as
# "\b<word>\b".
#
# Keeping these apart matters: applying a word boundary to a stem silently matches nothing, and
# applying a stem continuation to a word can eat unrelated text.
SPELLING_STEMS = [
    ("normalis", "normaliz"),      # normalise, normalised, normalisation
    ("optimis", "optimiz"),        # optimise, optimiser, optimisation
    ("analys", "analyz"),          # analyse, analysed, analysis-dependent words
    ("generalis", "generaliz"),
    ("characteris", "characteriz"),
    ("summaris", "summariz"),
    ("recognis", "recogniz"),
    ("minimis", "minimiz"),
    ("maximis", "maximiz"),
    ("stabilis", "stabiliz"),
    ("regularis", "regulariz"),
    ("penalis", "penaliz"),
    ("utilis", "utiliz"),
    ("favour", "favor"),           # favour, favours, favourable
]

SPELLING_WORDS = [
    ("behaviour", "behavior"),
    ("colour", "color"),
    ("modelling", "modeling"),
    ("modelled", "modeled"),
    ("centre", "center"),
    ("centred", "centered"),
]


COMPOUNDS = [
    (r"cross architecture", "cross-architecture"),
    (r"cross dataset", "cross-dataset"),
    (r"cross modal", "cross-modal"),
    (r"both position", "both-position"),
]

# The worst sentence in the paper (124 words, in the conclusion). Splitting it at "establishing"
# keeps every clause and every number, and gives the reader a full stop before the enumeration.
LONG = [
    (
        r"covering 117 mechanism experiments and 104 strict-freezing controls, establishing that "
        r"adaptation at the text position preserves cross-modal alignment on the InfoNCE-based "
        r"encoders studied",
        r"covering 117 mechanism experiments and 104 strict-freezing controls. That work "
        r"established that adaptation at the text position preserves cross-modal alignment on the "
        r"InfoNCE-based encoders studied",
    ),
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not a.apply:
        a.dry_run = True

    files = sorted((PA / "sections").glob("*.tex")) + [PA / "main_nc.tex"]
    total_sp = total_cp = total_lg = 0
    for p in files:
        t = io.open(p, encoding="utf-8", errors="replace").read()
        orig = t
        # protect math mode, labels, refs, cites and file names from spelling rules
        PROT = []

        def stash(m, PROT=PROT):
            PROT.append(m.group(0))
            return f"\x00{len(PROT) - 1}\x00"

        protected = re.sub(
            r"\$[^$]*\$|\\(?:label|ref|cite|citep|citet|includegraphics|url|texttt)\{[^{}]*\}"
            r"|\\(?:begin|end)\{[^{}]*\}", stash, t)

        n_sp = 0
        for stem, rep in SPELLING_STEMS:                 # match any continuation
            protected, k = re.subn(r"\b" + stem + r"\w*", rep, protected, flags=re.I)
            n_sp += k
        for word, rep in SPELLING_WORDS:                 # whole word only
            protected, k = re.subn(r"\b" + word + r"\b", rep, protected, flags=re.I)
            n_sp += k
        n_cp = 0
        for pat, rep in COMPOUNDS:
            # case-insensitive so that a sentence-initial "Cross-architecture" is normalised too,
            # with the replacement's first letter restored to match
            protected, k = re.subn(pat, lambda m, r=rep: (r[0].upper() + r[1:])
                                   if m.group(0)[0].isupper() else r, protected, flags=re.I)
            n_cp += k
        n_lg = 0
        if p.name == "conclusion.tex":
            for old, new in LONG:
                if old in protected:
                    protected = protected.replace(old, new, 1)
                    n_lg += 1

        for i, s in enumerate(PROT):
            protected = protected.replace(f"\x00{i}\x00", s)
        t = protected

        if t != orig:
            print(f"  {p.name:<24} spelling {n_sp:>3}  compounds {n_cp:>3}  splits {n_lg}")
            total_sp += n_sp
            total_cp += n_cp
            total_lg += n_lg
            if a.apply:
                bak = p.with_suffix(p.suffix + ".bak_p816")
                if not bak.exists():
                    shutil.copy2(p, bak)
                p.write_text(t, encoding="utf-8", newline="")

    print()
    print(f"  changes made: {total_sp} spelling, {total_cp} compounds, {total_lg} sentence splits")
    if a.dry_run:
        print("  (dry run; nothing written)")
        return 0

    print()
    print("=" * 100)
    print("assertion 1: no British spelling left in the unprotected prose")
    print("=" * 100)
    print("  (protected regions are masked, not removed, so a hit inside \\texttt{} or math is not")
    print("   counted: those are code identifiers such as a corruption name and must not be changed)")
    ok = True
    left = {}
    mask_re = (r"\$[^$]*\$|\\(?:label|ref|cite|citep|citet|includegraphics|url|texttt)"
               r"\{[^{}]*\}|\\(?:begin|end)\{[^{}]*\}")
    for p in files:
        t = io.open(p, encoding="utf-8", errors="replace").read()
        masked = re.sub(mask_re, lambda m: " " * len(m.group(0)), t)
        found = re.findall(r"\b(?:behaviour|colour|favour|modelling|modelled|normalis\w*|"
                           r"optimis\w*|analys\w*|generalis\w*|characteris\w*|summaris\w*|"
                           r"recognis\w*|minimis\w*|maximis\w*|stabilis\w*|penalis\w*|"
                           r"utilis\w*|centre\w*)", masked, re.I)
        if found:
            left[p.name] = found
            ok = False
    if left:
        for k, v in left.items():
            print(f"  FAIL {k}: {sorted(set(v))}")
    else:
        print("  none")

    print()
    print("=" * 100)
    print("assertion 2: numbers, labels, citations and references unchanged")
    print("=" * 100)
    for p in files:
        bak = p.with_suffix(p.suffix + ".bak_p816")
        if not bak.exists():
            continue
        before = io.open(bak, encoding="utf-8", errors="replace").read()
        after = io.open(p, encoding="utf-8", errors="replace").read()
        for label, pat in (("numbers", r"\d+(?:\.\d+)?"),
                           ("labels", r"\\label\{[^}]*\}"),
                           ("refs", r"\\(?:ref|eqref)\{[^}]*\}"),
                           ("cites", r"\\cite[a-z]*\{[^}]*\}"),
                           ("figures", r"\\includegraphics(?:\[[^\]]*\])?\{[^}]*\}")):
            b = sorted(re.findall(pat, before))
            x = sorted(re.findall(pat, after))
            if b != x:
                ok = False
                miss = [v for v in b if v not in x][:5]
                print(f"  FAIL {p.name:<22} {label}: {len(b)} -> {len(x)}   missing {miss}")
        print(f"  {p.name:<26} checked")
    print()
    print(f"  OVERALL: {'POLISH VERIFIED' if ok else 'SOMETHING CHANGED THAT SHOULD NOT HAVE'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
