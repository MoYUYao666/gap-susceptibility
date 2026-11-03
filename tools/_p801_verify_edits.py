# -*- coding: utf-8 -*-
r"""Verify the two Paper A edits read correctly and contain the right numbers.

    python tools/_p801_verify_edits.py --apply
"""
from __future__ import annotations

import argparse
import io
import json
import re
import statistics as st
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PA = REPO / "paper合"
OUT = REPO / "outputs" / "analysis" / "paperA_edit_verification.json"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(PA / "sections" / "empirical.tex", encoding="utf-8", errors="replace").read()

    d = json.loads((REPO / "outputs" / "analysis" / "coco_scaleup.json").read_text(
        encoding="utf-8", errors="ignore"))

    def stat(arm, k):
        v = [r[k] for r in d["runs"] if r["arm"] == arm and r.get(k) is not None]
        return st.mean(v), (st.stdev(v) if len(v) > 1 else 0.0)

    fz = stat("frozen", "R@1")[0]
    to, to_sd = stat("text_only", "R@1")
    bo, bo_sd = stat("both", "R@1")
    print("=" * 104)
    print("archive values the edits must match")
    print("=" * 104)
    print(f"  frozen {fz:.3f} | text_only {to:.3f} +- {to_sd:.3f} | both {bo:.3f} +- {bo_sd:.3f}")

    print()
    print("=" * 104)
    print("edit 1: repaired COCO retrieval evidence")
    print("=" * 104)
    m = re.search(r"That deficiency is repairable.*?of the two\.", t, re.S)
    ok = True
    if not m:
        print("  !! paragraph not found")
        ok = False
    else:
        seg = " ".join(m.group(0).split())
        print(f"  {seg}")
        print()
        for label, needle, expect in (
            ("frozen value", f"{fz:.3f}", True),
            ("text-only mean", f"{to:.3f}", True),
            ("text-only sd", f"{to_sd:.3f}", True),
            ("both mean", f"{bo:.3f}", True),
            ("both sd", f"{bo_sd:.3f}", True),
            ("10,000 training images", "10{,}000", True),
            ("3,000 evaluation images", "3{,}000", True),
            ("three seeds", "three seeds", True),
        ):
            present = needle in seg
            good = present == expect
            ok = ok and good
            print(f"  [{'ok  ' if good else 'FAIL'}] {label:<26} '{needle}'")
        # the honest reading must be stated
        honest = "does not reproduce the text-only advantage" in seg
        ok = ok and honest
        print(f"  [{'ok  ' if honest else 'FAIL'}] states it does not reproduce the text-only advantage")

    print()
    print("=" * 104)
    print("edit 2: method disclosure")
    print("=" * 104)
    m2 = re.search(r"A fourth caution concerns the method.*?same retrieval ordering\.", t, re.S)
    if not m2:
        print("  !! disclosure not found")
        ok = False
    else:
        seg2 = " ".join(m2.group(0).split())
        print(f"  {seg2[:600]}...")
        print()
        for label, needle in (
            ("adapter-only count 196,608", "196{,}608"),
            ("full-tower count 145,170,177", "145{,}170{,}177"),
            ("share 0.14%", "0.14"),
            ("says not low-rank adaptation", "not low-rank adaptation"),
            ("says rank ablation cannot be read as rank", "cannot be read as an effect of rank"),
            ("strict-freezing columns unaffected", "are unaffected"),
            ("both-position adapter count 491,520", "491{,}520"),
        ):
            present = needle in seg2
            ok = ok and present
            print(f"  [{'ok  ' if present else 'FAIL'}] {label}")

    print()
    print(f"  OVERALL: {'EDITS VERIFIED' if ok else 'SOMETHING NEEDS ATTENTION'}")
    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps({"frozen": fz, "text_only": [to, to_sd],
                                   "both": [bo, bo_sd], "verified": ok},
                                  ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"  wrote {OUT.relative_to(REPO)}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
