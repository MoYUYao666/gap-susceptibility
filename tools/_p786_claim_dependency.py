# -*- coding: utf-8 -*-
r"""Determine which claims actually depend on the runs being LoRA rather than tower fine-tuning.

The defect means every run labelled "LoRA rank r" trained the whole adapted tower with a small
adapter attached. Two very different kinds of consequence follow, and they must not be confused:

  (a) naming/labelling: a number is attributed to the wrong method, which is a reporting error
  (b) substantive: a claim only holds because a rank or an alpha was actually doing work, so the
      claim breaks when the rank is the only thing that changes

This searches both manuscripts for claims of kind (b): statements that compare ranks, alphas or
target modules, or that attribute an effect to low-rank adaptation specifically.

    python tools/_p786_claim_dependency.py --apply
"""
from __future__ import annotations

import argparse
import io
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "outputs" / "analysis" / "lora_claim_dependency.json"

PAPERS = {
    "Paper A": REPO / "paper合" / "sections",
    "P3": REPO / "paper3" / "paper_ieee" / "sections",
}

# patterns that indicate a claim resting on the adaptation mechanism itself
KIND_B = {
    "rank sweep / rank dependence": r"[^.]*\brank\b[^.]*\b(?:sweep|scaling|effect|monotonic|"
                                    r"decreas|increas|saturat|sweet spot)[^.]*\.",
    "alpha / scaling-factor dependence": r"[^.]*\balpha\b[^.]*\b(?:scaling factor|interact|"
                                         r"non-monotonic|sweet spot|optimal)[^.]*\.",
    "target-module choice": r"[^.]*target modules?[^.]*\.",
    "low-rank specifically": r"[^.]*\b(?:low-rank|low rank|rank-\d|rank \$r\$|\br=\d)[^.]*\b"
                             r"(?:suffice|enough|adequate|preserve|better|worse)[^.]*\.",
    "parameter-efficiency claim": r"[^.]*\b(?:parameter[- ]efficien|0\.1\%|trainable parameters)"
                                  r"[^.]*\.",
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    report = {}
    for paper, d in PAPERS.items():
        if not d.exists():
            print(f"  {paper}: {d} absent")
            continue
        print("=" * 104)
        print(f"{paper}   ({d.relative_to(REPO)})")
        print("=" * 104)
        found = {}
        for pat_name, pat in KIND_B.items():
            hits = []
            for f in sorted(d.glob("*.tex")):
                t = io.open(f, encoding="utf-8", errors="replace").read()
                for m in re.finditer(pat, t, re.S):
                    seg = " ".join(m.group(0).split())
                    if 40 <= len(seg) <= 400 and re.search(r"LoRA|rank|alpha", seg, re.I):
                        hits.append({"file": f.name, "text": seg})
            found[pat_name] = hits
            print(f"  {pat_name}: {len(hits)} sentence(s)")
            for h in hits[:2]:
                print(f"     [{h['file']}] {h['text'][:180]}")
        print()
        report[paper] = {k: v[:6] for k, v in found.items()}

    print("=" * 104)
    print("reading of the two consequences")
    print("=" * 104)
    print("  (a) labelling: every 'LoRA' in either paper currently names a method that was not run.")
    print("  (b) substantive: a claim is broken only if it compares rank/alpha/target modules, or")
    print("      attributes an effect to low-rank adaptation itself, because in the executed runs")
    print("      those knobs controlled 0.13% of the trainable parameters.")
    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
        print()
        print(f"  wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
