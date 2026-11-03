# -*- coding: utf-8 -*-
r"""Language-polish survey of Paper A: find the mechanical and stylistic problems first.

Reviewers 1, 2 and 3 all asked for language editing. Before rewriting any prose, this measures what
is actually wrong, so the polish targets real defects rather than taste:

  - repeated words inside a sentence
  - doubled words ("the the")
  - sentences that are far longer than the rest of the paper
  - inconsistent British/American spelling
  - inconsistent hyphenation of compound terms the paper uses often
  - spacing and punctuation faults around math, citations and abbreviations
  - paragraph openers that repeat across sections

    python tools/_p815_polish_survey.py --apply
"""
from __future__ import annotations

import argparse
import io
import json
import re
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PA = REPO / "paper合"
OUT = REPO / "outputs" / "analysis" / "polish_survey.json"

BRITISH = ["behaviour", "colour", "favour", "modelling", "modelled", "normalise", "normalised",
           "optimise", "optimised", "analyse", "analysed", "centre", "generalise", "generalised",
           "characterise", "characterised", "summarise", "summarised", "utilisation"]
AMERICAN = ["behavior", "color", "favor", "modeling", "modeled", "normalize", "normalized",
            "optimize", "optimized", "analyze", "analyzed", "center", "generalize", "generalized",
            "characterize", "characterized", "summarize", "summarized", "utilization"]

COMPOUNDS = [
    (r"cross[- ]?modal", "cross-modal"),
    (r"cross[- ]?architecture", "cross-architecture"),
    (r"cross[- ]?dataset", "cross-dataset"),
    (r"text[- ]?only", "text-only"),
    (r"vision[- ]?only", "vision-only"),
    (r"both[- ]?position", "both-position"),
    (r"low[- ]?rank", "low-rank"),
    (r"fine[- ]?tuning", "fine-tuning"),
    (r"zero[- ]?shot", "zero-shot"),
    (r"parameter[- ]?efficient", "parameter-efficient"),
    (r"multi[- ]?modal", "multimodal"),
    (r"pre[- ]?train", "pretrain"),
]


def detex(s: str) -> str:
    s = re.sub(r"\\[a-zA-Z]+\*?(\[[^\]]*\])?(\{[^{}]*\})?", " ", s)
    s = re.sub(r"\$[^$]*\$", " MATH ", s)
    s = re.sub(r"\\[a-zA-Z]+", " ", s)
    return re.sub(r"\s+", " ", s)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    files = sorted((PA / "sections").glob("*.tex")) + [PA / "main_nc.tex"]
    full = "\n".join(io.open(f, encoding="utf-8", errors="replace").read() for f in files)
    prose = detex(full)
    report = {}

    print("=" * 104)
    print("1. doubled words")
    print("=" * 104)
    dbl = re.findall(r"\b(\w+)\s+\1\b", prose, re.I)
    dbl = [d for d in dbl if d.lower() not in ("that", "had")]
    print(f"  {len(dbl)}: {Counter(d.lower() for d in dbl).most_common(12)}")
    report["doubled"] = Counter(d.lower() for d in dbl).most_common(20)

    print()
    print("=" * 104)
    print("2. sentence length distribution")
    print("=" * 104)
    sents = [s.strip() for s in re.split(r"(?<=[.!?])\s+", prose) if len(s.strip()) > 15]
    lens = sorted(len(s.split()) for s in sents)
    if lens:
        n = len(lens)
        print(f"  {n} sentences; median {lens[n // 2]} words; p90 {lens[int(n * 0.9)]}; "
              f"max {lens[-1]}")
        long_ones = [s for s in sents if len(s.split()) >= 70]
        print(f"  sentences of 70+ words: {len(long_ones)}")
        for s in long_ones[:6]:
            print(f"     ({len(s.split())} w) {s[:150]}...")
        report["sentences"] = {"n": n, "median": lens[n // 2], "p90": lens[int(n * 0.9)],
                               "max": lens[-1], "over_70": len(long_ones)}

    print()
    print("=" * 104)
    print("3. British vs American spelling")
    print("=" * 104)
    bl = Counter(w for w in BRITISH for _ in re.finditer(r"\b" + w + r"\w*", prose, re.I))
    am = Counter(w for w in AMERICAN for _ in re.finditer(r"\b" + w + r"\w*", prose, re.I))
    print(f"  British forms:  {sum(bl.values())}  {dict(bl)}")
    print(f"  American forms: {sum(am.values())}  {dict(am)}")
    report["british"] = dict(bl)
    report["american"] = dict(am)

    print()
    print("=" * 104)
    print("4. compound-term consistency")
    print("=" * 104)
    comp = {}
    for pat, canon in COMPOUNDS:
        hy = len(re.findall(pat.replace("[- ]?", "-"), prose, re.I))
        sp = len(re.findall(pat.replace("[- ]?", " "), prose, re.I))
        comp[canon] = {"hyphen": hy, "space": sp}
        flag = "" if sp == 0 else "  <-- inconsistent"
        print(f"  {canon:<24} hyphen {hy:>4}   space {sp:>4}{flag}")
    report["compounds"] = comp

    print()
    print("=" * 104)
    print("5. spacing and punctuation around math and citations")
    print("=" * 104)
    checks = {
        "missing space before \\cite": len(re.findall(r"[a-z]\\cite", full)),
        "double space": len(re.findall(r"[a-z]  +[a-z]", prose)),
        "space before comma/period": len(re.findall(r"\s+[,.;](?=\s|$)", prose)),
        "no space after period": len(re.findall(r"\.[A-Z][a-z]", prose)),
        "sentence starting lowercase after period": len(re.findall(r"\.\s+[a-z]{3,}", prose)),
    }
    for k, v in checks.items():
        print(f"  {k:<44} {v}")
    report["mechanics"] = checks

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
        print()
        print(f"  wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
