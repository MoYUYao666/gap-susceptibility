# -*- coding: utf-8 -*-
r"""Insert the Zenodo DOI and switch the statements from "private" to "public".

Operator supplied the DOI on 2026-10-14: 10.5281/zenodo.23341083
The GitHub repository is now PUBLIC (verified: isPrivate=false), so the data statement no
longer needs to say the repository is private and pending deposition.

Four places are updated:
1. paper3/paper_ieee/main.tex                                - Data statement
2. SUBMISSION/P3_PRL_revision/manuscript/latex_source/main.tex - the same statement, in the source package
3. paper3/paper_ieee/cover_letter_prl.tex                    - the [REPOSITORY DOI, to be inserted] placeholder
4. publish_clean/README.md and README.md                     - Data availability + a DOI badge

    python tools/_p620_insert_doi.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DOI = "10.5281/zenodo.23341083"
URL = f"https://doi.org/{DOI}"

OLD_MAIN = """statistic, and the training configurations---are archived in the project repository. That
repository is private while the manuscript is under review; a public archive with a
persistent identifier, linked from the published article, will be deposited on acceptance,
and the material is available to the editor and reviewers on request. We note that the
analysis does not require any non-public data: every number in the paper can be recomputed
from the public datasets and models above."""

NEW_MAIN = f"""statistic, and the training configurations---are archived in a public repository at
\\url{{https://github.com/MoYUYao666/gap-susceptibility}} and in a versioned snapshot
archived on Zenodo under DOI \\texttt{{{DOI}}} (\\url{{{URL}}}). Every number in the
paper can be recomputed from the public datasets and models above, using the per-run
records and analysis scripts in that archive."""

OLD_CL = r"\texttt{[REPOSITORY DOI, to be inserted]}"
NEW_CL = f"\\texttt{{{DOI}}} (\\url{{{URL}}})"

OLD_README = """A versioned snapshot of this repository is archived on Zenodo; the DOI is minted from the
`v1.0-prl-revision` release."""

NEW_README = f"""A versioned snapshot of this repository is archived on Zenodo:

[![DOI](https://zenodo.org/badge/DOI/{DOI}.svg)]({URL})

**DOI: [{DOI}]({URL})** — this is the persistent identifier to cite for the code and
results. It resolves to the `v1.0-prl-revision` release."""


def patch(path: Path, old: str, new: str, label: str) -> bool:
    if not path.exists():
        print(f"  MISSING  {path.relative_to(REPO)}")
        return False
    t = io.open(path, encoding="utf-8", errors="replace").read()
    n = t.count(old)
    print(f"  {label:<12} {path.relative_to(REPO)}  matches={n}")
    return n == 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    print(f"  DOI = {DOI}")
    print()
    jobs = [
        (REPO / "paper3" / "paper_ieee" / "main.tex", OLD_MAIN, NEW_MAIN, "main.tex"),
        (REPO / "SUBMISSION" / "P3_PRL_revision" / "manuscript" / "latex_source" / "main.tex",
         OLD_MAIN, NEW_MAIN, "src copy"),
        (REPO / "paper3" / "paper_ieee" / "cover_letter_prl.tex", OLD_CL, NEW_CL, "cover letter"),
        (REPO / "publish_clean" / "README.md", OLD_README, NEW_README, "README"),
        (REPO / "README.md", OLD_README, NEW_README, "README(root)"),
    ]
    ok = True
    for p, old, new, label in jobs:
        got = patch(p, old, new, label)
        ok = ok and got
    print()
    if not ok:
        print("  Some anchors did not match exactly once - nothing written.")
        return 1
    if not a.apply:
        print("  (dry run)")
        return 0
    for p, old, new, label in jobs:
        bak = p.with_suffix(p.suffix + ".bak_p620")
        if not bak.exists():
            shutil.copy2(p, bak)
        t = io.open(p, encoding="utf-8", errors="replace").read()
        io.open(p, "w", encoding="utf-8", newline="").write(t.replace(old, new))
    print("  All files written.")
    print()
    print("  Re-check:")
    for p, _, _, label in jobs:
        t = io.open(p, encoding="utf-8", errors="replace").read()
        print(f"    {label:<12} contains DOI: {DOI in t}  |  stale 'is private': "
              f"{'repository is private' in t}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
