# -*- coding: utf-8 -*-
r"""Check that Paper A's headline numbers come from files that are current, not superseded.

The previous pass showed every value present somewhere under outputs/, but one hit was a file
named _p255_run1_5seed_superseded.json - "superseded". A number sourced from a retired file, or
absent from the current figures, is exactly the kind of provenance gap the claim ledger exists
to catch, and Paper A is about to be submitted.

For each value this lists the tracked files containing it, flagging any whose name suggests it
has been withdrawn, and reports whether a current (non-underscore-prefixed) file also holds it.

    python tools/_p697_value_provenance.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PUB = REPO / "publish_clean"
PA = REPO / "paper合"
OUT = REPO / "outputs" / "analysis" / "paperhe_value_provenance.json"

# values Paper A states, with the claim they support
VALUES = {
    "0.949": "mean R2 of the ODE fit over LoRA",
    "0.814": "lower end of the R2 range",
    "0.977": "upper end of the R2 range",
    "0.943": "OpenCLIP BitFit R2",
    "0.922": "CLIP full-fine-tuning pilot R2",
    "0.946": "linear baseline R2",
    "204": "archived runs in the empirical part",
    "383": "experiments in the validation part",
    "221": "runs in the experiment catalogue",
    "60.69": "LoRA zero-shot accuracy after per-method tuning",
    "60.87": "full fine-tuning accuracy after per-method tuning",
    "0.91": "relative budget ratio at a 5% drop",
    "0.0867": "some reported quantity",
}

SUSPECT = re.compile(r"superseded|_archive|broken|_old|obsolete|_tmp|_scratch", re.I)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    r = subprocess.run(["git", "ls-files", "outputs"], cwd=str(PUB), capture_output=True)
    tracked = [x for x in r.stdout.decode("utf-8", errors="replace").splitlines() if x.strip()]
    jsons = [f for f in tracked if f.endswith((".json", ".txt", ".md"))]
    print(f"  scanning {len(jsons)} tracked text files under outputs/")
    print()

    report = {}
    for val, claim in VALUES.items():
        current, suspect = [], []
        for f in jsons:
            p = PUB / f
            if not p.exists():
                continue
            try:
                t = p.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            if val not in t:
                continue
            (suspect if SUSPECT.search(f) else current).append(f)
        status = "OK " if current else ("SUSPECT-ONLY" if suspect else "NOT FOUND")
        print(f"  {status:<13} {val:<8} {claim}")
        print(f"        current files: {len(current)}   suspect files: {len(suspect)}")
        for f in current[:2]:
            print(f"          {f}")
        for f in suspect[:2]:
            print(f"          [suspect] {f}")
        report[val] = {"claim": claim, "current": current[:5], "suspect": suspect[:5],
                       "status": status}

    print()
    print("=" * 104)
    print("summary")
    print("=" * 104)
    bad = [v for v, d in report.items() if d["status"] != "OK "]
    print(f"  values with a current source: {len(report) - len(bad)}/{len(report)}")
    if bad:
        print(f"  needing attention: {bad}")
        print()
        print("  For each, either the value lives only in a retired file (so the figure it")
        print("  supports needs re-sourcing), or it is in no tracked file at all (so the claim")
        print("  has no archive behind it).")
    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps(report, ensure_ascii=False, indent=1))
        print()
        print(f"  wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
