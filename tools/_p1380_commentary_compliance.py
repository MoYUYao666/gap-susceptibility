# -*- coding: utf-8 -*-
r"""Commentary: add a short "what reporting would change" paragraph after the six-instance table, with compensating trims.

    python tools/_p1380_commentary_compliance.py [--apply]
"""
from __future__ import annotations

import argparse
import io

MD = "paper_review_prl/MANUSCRIPT.md"
PARA = """**What reporting the six items would change.** None of the six remedies requires a new experiment. Naming the POPE
subset makes its three numbers comparable across papers; stating the MMBench protocol makes two values placeable in one
table; giving the budget composition turns "parameter count" into a budget; defining failure semantics stops a non-finite
value from counting as evidence against a method; naming the variance convention makes intervals combinable; and describing
the freeze regime identifies the intervention that "frozen encoder" names. Each remedy is one sentence in a paper and
removes one class of incomparability.

"""
TRIMS = [
    ('The distinction changes\nthe direction of the conclusion: a configuration that fails for an implementation reason is not a\nmethod that fails. The literature does not systematically separate the two, so we record this as an\nopen question rather than a finding about any particular method.',
     'The distinction changes the direction of the conclusion: a configuration that fails for an implementation\nreason is not a method that fails. We record this as an open question rather than a finding.'),
    ('Adaptation of the visual encoder follows a different logic and appears when the visual distribution\nshifts.',
     'Adaptation of the visual encoder follows different logic and appears when the visual distribution shifts.'),
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(MD, encoding="utf-8").read()
    if "What reporting the six items would change" in t:
        print("  already present")
        return 0
    n = 0
    for old, new in TRIMS:
        if t.count(old) == 1:
            t = t.replace(old, new, 1)
            n += 1
    anchor = "### 3.7 What a practitioner can still conclude"
    assert t.count(anchor) == 1
    t = t.replace(anchor, PARA + anchor, 1)
    print(f"  paragraph inserted; compensating trims: {n}")
    if not a.apply:
        print("  (dry run)")
        return 0
    io.open(MD, "w", encoding="utf-8", newline="").write(t)
    print("  written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
