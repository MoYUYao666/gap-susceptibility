# -*- coding: utf-8 -*-
r"""Count the data-availability text options exactly, for a 200-character form field.

The operator's form rejects anything over 200 characters and my hand count was wrong (I
counted a wrapped version as if it had no line breaks). This measures each candidate.

    python tools/_p668_data_availability_text.py
"""
from __future__ import annotations

import io
import sys

CANDIDATES = {
    "A: DOI only, essential facts": (
        "Data and code are deposited in the public Zenodo repository, DOI "
        "10.5281/zenodo.23341223 - openly available, not on request. See the "
        "manuscript's Data statement."
    ),
    "B: DOI with resolvable link": (
        "Data and code are publicly available in Zenodo, DOI 10.5281/zenodo.23341223 "
        "(https://doi.org/10.5281/zenodo.23341223). Not on request. See the "
        "manuscript's Data statement."
    ),
    "C: DOI link + GitHub name only": (
        "Data and code: Zenodo DOI 10.5281/zenodo.23341223 "
        "(https://doi.org/10.5281/zenodo.23341223) and GitHub "
        "MoYUYao666/gap-susceptibility. Openly available, not on request."
    ),
    "D: shortest that still links": (
        "Data and code are openly available in the public Zenodo archive, DOI "
        "10.5281/zenodo.23341223 (https://doi.org/10.5281/zenodo.23341223), not on request."
    ),
    "E: A + GitHub owner/repo": (
        "Data and code: public Zenodo repo, DOI 10.5281/zenodo.23341223, and GitHub "
        "MoYUYao666/gap-susceptibility. Openly available, not on request."
    ),
}


def main() -> int:
    print(f"  {'option':<34} {'chars':>6}  fits 200")
    print("  " + "-" * 60)
    for name, text in CANDIDATES.items():
        n = len(text)
        print(f"  {name:<34} {n:>6}  {'YES' if n <= 200 else 'no'}")
        if n <= 200:
            print()
            print(text)
            print()
    print()
    print("  For reference, the text the operator pasted was:")
    pasted = (
        "The data and code are deposited in the public Zenodo repository, DOI "
        "10.5281/zenodo.23341223 (https://doi.org/10.5281/zenodo.23341223), openly "
        "available - not on request. Artifacts are described in the manuscript's Data "
        "statement."
    )
    print(f"    {len(pasted)} characters")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
