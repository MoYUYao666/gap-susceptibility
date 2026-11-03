# -*- coding: utf-8 -*-
r"""Check Paper A against every objection in the Pattern Recognition rejection letter.

The letter (C:\Users\hongr\Desktop\PR_reject.txt, manuscript PR-D-26-10149) has an Area Editor
summary plus three referee reports. Its headline: "severe numerical inconsistencies, flawed
statistics, unsubstantiated causal claims and unreliable generalization ... These fundamental
flaws invalidate core findings".

Each objection is turned into a concrete test against the current paper合 sources. This prints
what the paper says now, so the ones still outstanding can be identified rather than assumed.

    python tools/_p741_check_pr_objections.py [--apply]
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
PUB = REPO / "publish_clean"
LETTER = Path(r"C:\Users\hongr\Desktop\PR_reject.txt")
OUT = REPO / "outputs" / "analysis" / "pr_objections_check.json"


def paper_text():
    parts = [io.open(PA / "main_nc.tex", encoding="utf-8", errors="replace").read()]
    for p in sorted((PA / "sections").glob("*.tex")):
        parts.append(io.open(p, encoding="utf-8", errors="replace").read())
    return "\n".join(parts)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = paper_text()
    flat = re.sub(r"\s+", " ", t)
    report = {}

    def probe(name, pattern, expect_absent=True, note=""):
        hits = list(re.finditer(pattern, t, re.I))
        present = bool(hits)
        good = (not present) if expect_absent else present
        report[name] = {"pattern": pattern, "hits": len(hits), "ok": good, "note": note}
        mark = "OK  " if good else "TODO"
        print(f"  [{mark}] {name}  ({len(hits)} hit(s))")
        for m in hits[:4]:
            ln = t[:m.start()].count("\n") + 1
            seg = " ".join(t[max(0, m.start() - 130):m.start() + 200].split())
            print(f"           L{ln}: ...{seg[:250]}...")
        if note:
            print(f"           note: {note}")

    print("=" * 110)
    print("R1-W1 / R3-1: numerical inconsistency and configuration transparency")
    print("=" * 110)
    probe("withdrawn +0.079 no longer presented as the recommended setting",
          r"\+0\.079", expect_absent=False,
          note="check whether it is described as a different configuration")
    probe("a configuration comparison table exists",
          r"config\w* (?:comparison|table)|tab:config", expect_absent=False)
    probe("Route D explained", r"Route~?D|route_d", expect_absent=False)

    print()
    print("=" * 110)
    print("R1-W2 / R2-5 / R3-2: pseudo-replication and grouped statistics")
    print("=" * 110)
    probe("cluster-robust inference reported", r"cluster(?:ed)?[- ]robust|CR1", expect_absent=False)
    probe("within-group correlations reported", r"within[- ](?:group|model|dataset|family)",
          expect_absent=False)
    probe("mixed-effects model reported", r"mixed[- ]effects", expect_absent=False)
    probe("held-out / out-of-sample validation", r"held[- ]out|out[- ]of[- ]sample",
          expect_absent=False)

    print()
    print("=" * 110)
    print("R1-W3 / R2-4 / R3-3: causal overclaiming")
    print("=" * 110)
    probe("'direct causal evidence' removed", r"direct causal", expect_absent=True)
    probe("'Visual Fragility' still claimed as a mechanism",
          r"Visual Fragility", expect_absent=False)
    probe("relative perturbation budget used",
          r"\\Delta W\\|_F|relative (?:weight )?perturbation", expect_absent=False)
    probe("'2.6 times' ratio removed", r"2\.6\s*(?:times|x)|2\.6\\times", expect_absent=True)

    print()
    print("=" * 110)
    print("R1-W4 / R3-4: cross-architecture and cross-dataset generalization")
    print("=" * 110)
    probe("COCO near-random explained", r"near[- ]random|below \$0\.001\$", expect_absent=False)
    probe("'across architectures' universal claim removed",
          r"across architectures|any contrastive", expect_absent=True)
    probe("SigLIP small-gap limitation stated", r"SigLIP", expect_absent=False)

    print()
    print("=" * 110)
    print("R1-W5 / R2-5: DG monitoring practical contribution")
    print("=" * 110)
    probe("'zero-overhead' removed", r"zero[- ]overhead", expect_absent=True)
    probe("early stopping positioned as preliminary",
          r"early stopping", expect_absent=False)

    print()
    print("=" * 110)
    print("R1-W6: experimental fairness (learning-rate sweep)")
    print("=" * 110)
    probe("per-method learning-rate tuning reported",
          r"learning[- ]rate (?:sweep|tuning)|tuned (?:each|per)", expect_absent=False)
    probe("60.69 / 60.87 matched-accuracy result present",
          r"60\.69|60\.87", expect_absent=False)

    print()
    print("=" * 110)
    print("AE / R2-1: scope of the claims")
    print("=" * 110)
    m = re.search(r"\\title\{(.*?)\}", io.open(PA / "main_nc.tex", encoding="utf-8",
                                               errors="replace").read(), re.S)
    print(f"  title now: {' '.join(m.group(1).split()) if m else '?'}")
    probe("'Protect, Don't Perturb' title retired (only in the cover letter's disclosure)",
          r"Protect, Don't Perturb", expect_absent=False)

    print()
    print("=" * 110)
    print("R3-1 (last point): cover-letter manuscript number")
    print("=" * 110)
    cl = io.open(PA / "cover_letter_nc.tex", encoding="utf-8", errors="replace").read()
    for mm in re.finditer(r"PR-D-26-10149|manuscript number|Manuscript Number", cl, re.I):
        ln = cl[:mm.start()].count("\n") + 1
        seg = " ".join(cl[max(0, mm.start() - 90):mm.start() + 150].split())
        print(f"  cover_letter_nc.tex L{ln}: ...{seg[:240]}...")
    report["cover_letter_number"] = "PR-D-26-10149" in cl

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps(report, ensure_ascii=False, indent=1))
        print()
        print(f"  wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
