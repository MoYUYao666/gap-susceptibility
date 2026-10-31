# -*- coding: utf-8 -*-
r"""Update Paper A's data availability statement, and check it against the P3 reviewers' objections.

Part 1: replace the two contradictory data availability statements with one that matches
reality. The repository is public and has a Zenodo DOI (10.5281/zenodo.23341223); the current
text still says the repository "is currently private and will be made public upon publication"
and that "no new data were generated that requires deposit in an external repository". A second,
one-line statement in sections/conclusion.tex says the opposite ("Data will be made available on
request"), so the manuscript contradicts itself.

Part 2: run the P3 reviewers' objections against Paper A, because the same claims appear in both
papers and the wording was fixed only in P3.

    python tools/_p688_paperhe_da_and_p3check.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PA = REPO / "paper合"
OUT = REPO / "outputs" / "analysis" / "paperhe_da_p3check.json"
DOI = "10.5281/zenodo.23341223"
GH = "https://github.com/MoYUYao666/gap-susceptibility"

OLD_MAIN = """All datasets and model releases used in this study are public. Every result JSON cited in this
manuscript --- including the per-epoch monitoring trajectories, the strict-freezing controls and the
cross-architecture sweeps --- together with the analysis scripts that compute the reported statistics and
the training configurations, is archived in the project repository, which is currently private and will
be made public upon publication (available to the reviewers on request). No new data were generated that
requires deposit in an external repository, and no datum used here is restricted."""

NEW_MAIN = f"""All datasets and model releases used in this study are public. The derived data this paper
relies on --- every result JSON cited here, including the per-epoch monitoring trajectories, the
strict-freezing controls and the cross-architecture sweeps, together with the analysis scripts that
compute the reported statistics and the training configurations --- are openly available in a public
repository at \\url{{{GH}}} and in a versioned snapshot archived on Zenodo under DOI
\\texttt{{{DOI}}} (\\url{{https://doi.org/{DOI}}}). No datum used here is restricted, and every
number in the paper can be recomputed from the public resources above."""

OLD_CONCLUSION = r"\section*{Data availability} Data will be made available on request."

# P3 reviewer objections, expressed as things to look for in Paper A
CHECKS = [
    ("architecture-dependent reading (P3 withdrew it)",
     [r"architecture[- ]dependent", r"architectural(?:ly)? (?:dependent|specific)"]),
    ("alignment energy used as a proxy for downstream accuracy (P3: not a proxy)",
     [r"proxy for", r"predicts? (?:task|downstream) (?:accuracy|performance)"]),
    ("allocation rule claimed to beat the uniform baseline (P3: withdrawn)",
     [r"beats? the uniform", r"outperform(?:s|ed)? (?:the )?uniform", r"better than uniform"]),
    ("sharp phase transition (P3: bracketed instead)",
     [r"sharp phase transition", r"phase transition at", r"critical rank"]),
    ("uniqueness without the additivity axiom (P3: needs R3')",
     [r"unique admissible", r"the unique", r"uniqueness"]),
    ("block decomposability implying additivity (P3: counterexample)",
     [r"decomposab", r"additiv"]),
    ("a large variance ratio presented as a finding (P3: withdrawn)",
     [r"\b30\s*[x×]", r"variance ratio", r"reduces uncertainty by"]),
    ("sample size / power caveat (P3: 11-28 seeds needed)",
     [r"seeds? (?:are|is) (?:not )?enough", r"underpowered", r"power"]),
    ("downstream check reported at all",
     [r"downstream", r"retrieval", r"task accuracy"]),
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    report = {}

    print("=" * 104)
    print("PART 1. data availability statement")
    print("=" * 104)
    main = PA / "main_nc.tex"
    t = io.open(main, encoding="utf-8", errors="replace").read()
    print(f"  main_nc.tex: old wording present: {OLD_MAIN in t}")
    if OLD_MAIN not in t:
        # try a whitespace-tolerant match to report honestly
        flat_t = re.sub(r"\s+", " ", t)
        flat_o = re.sub(r"\s+", " ", OLD_MAIN)
        print(f"  main_nc.tex: whitespace-normalised match: {flat_o in flat_t}")
    concl = PA / "sections" / "conclusion.tex"
    c = io.open(concl, encoding="utf-8", errors="replace").read()
    flat_c = re.sub(r"\s+", " ", c)
    print(f"  conclusion.tex: one-liner present: "
          f"{'Data will be made available on request' in flat_c}")

    if a.apply:
        t2, n1 = re.subn(re.escape(re.sub(r"\s+", " ", OLD_MAIN)).replace(r"\ ", r"\s+"),
                         lambda m: NEW_MAIN, re.sub(r"\s+", " ", t), count=1)
        if n1 and "10.5281/zenodo" not in t2:
            io.open(main, "w", encoding="utf-8", newline="").write(t2)
            print(f"  main_nc.tex: statement replaced")
        c2, n2 = re.subn(
            r"\\section\*\{Data availability\}\s*Data will be made available on request\.",
            "", c)
        if n2:
            io.open(concl, "w", encoding="utf-8", newline="").write(c2)
            print(f"  conclusion.tex: contradictory one-liner removed")
        report["replaced_main"] = bool(n1)
        report["removed_conclusion"] = bool(n2)
    else:
        print("  (dry run)")

    print()
    print("=" * 104)
    print("PART 2. the P3 reviewers' objections, checked against Paper A")
    print("=" * 104)
    # corpus: the sources that make up the compiled manuscript
    files = [main] + sorted((PA / "sections").glob("*.tex"))
    corpus = {p.name: io.open(p, encoding="utf-8", errors="replace").read() for p in files}
    joined = "\n".join(corpus.values())
    flat = re.sub(r"\s+", " ", joined)
    for label, pats in CHECKS:
        hits = []
        for pat in pats:
            for m in re.finditer(pat, flat, re.I):
                ln = flat[:m.start()].count("\n")
                seg = flat[max(0, m.start() - 120):m.start() + 140]
                hits.append(seg.strip())
        print(f"  {'FOUND' if hits else 'none '} {label}")
        for h in hits[:2]:
            print(f"        ...{h[:240]}...")
        report.setdefault("checks", {})[label] = len(hits)

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps(report, ensure_ascii=False, indent=1))
        print()
        print(f"  wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
