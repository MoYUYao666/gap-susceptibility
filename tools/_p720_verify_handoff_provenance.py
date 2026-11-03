# -*- coding: utf-8 -*-
r"""Verify the provenance the handoff just revealed for Paper A's five numbers.

HANDOFF says:
  - the appendix catalogue sums to 221 (117 mechanism + 104 strict-freezing) and
    "catalogue + ODE = 221 + 162 = 383"
  - the CR1 robust standard error with 6 clusters went from 0.0723 to 0.2911, p(t5) = 0.0155

If the appendix table really sums to those numbers, then the source is the table itself, which is
checkable. If the SE 0.2911 exists in the archive, the last gap closes too.

    python tools/_p720_verify_handoff_provenance.py [--apply]
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
PA = REPO / "paper合"
PUB = REPO / "publish_clean"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    print("=" * 112)
    print("1. the appendix catalogue: does it sum to 117 + 95 and to 221?")
    print("=" * 112)
    supp = PA / "sections" / "supplement.tex"
    if supp.exists():
        t = io.open(supp, encoding="utf-8", errors="replace").read()
        # find category rows with counts
        rows = re.findall(r"(X{0,3}(?:IX|IV|V?I{0,3})|[IVX]+)\s*[:.]?\s*([^&\n]{0,80}?)&?\s*"
                          r"(\d{1,3})\s*\\\\", t)
        print(f"  {supp.name}: {len(t):,} chars")
        # simpler: any line holding a category name and a number
        cats = []
        for line in t.splitlines():
            if re.search(r"(Mechanism|Strict|Control|ODE)", line, re.I) and re.search(r"\d{2,3}", line):
                cats.append(" ".join(line.split())[:140])
        for c in cats[:14]:
            print("     " + c)
        # totals stated in the file
        print()
        print("  stated totals in supplement.tex:")
        for m in re.finditer(r"\b(117|95|104|162|221|383|212)\b", t):
            ln = t[:m.start()].count("\n") + 1
            seg = " ".join(t[max(0, m.start() - 150):m.start() + 150].split())
            print(f"     L{ln}: ...{seg[:230]}...")
    else:
        print("  supplement.tex not found")

    print()
    print("=" * 112)
    print("2. the CR1 standard error 0.2911 in the archive")
    print("=" * 112)
    r = subprocess.run(["git", "ls-files", "outputs"], cwd=str(PUB), capture_output=True)
    files = [x for x in r.stdout.decode("utf-8", errors="replace").splitlines()
             if x.endswith(".json")]
    hits = []

    def walk(o, p="$"):
        if isinstance(o, dict):
            for k, v in o.items():
                yield from walk(v, f"{p}.{k}")
        elif isinstance(o, list):
            for i, v in enumerate(o):
                yield from walk(v, f"{p}[{i}]")
        else:
            yield p, o

    for rel in files:
        p = PUB / rel
        if not p.exists():
            continue
        try:
            d = json.loads(p.read_text(encoding="utf-8", errors="ignore"))
        except Exception:
            continue
        for path, v in walk(d):
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                if abs(float(v) - 0.2911) <= 0.001:
                    hits.append(f"{rel}::{path} = {v}")
    print(f"  matches for 0.2911 ± 0.001: {len(hits)}")
    for h in hits[:10]:
        print(f"     {h}")
    # also check the workspace copy of pr_stats_hardened for an se field
    print()
    for rel in ("outputs/analysis/pr_stats_hardened.json",):
        p = PUB / rel
        d = json.loads(p.read_text(encoding="utf-8", errors="ignore"))
        cro = d.get("mixed_effects", {}).get("cluster_robust_OLS", {})
        for grp, vals in cro.items():
            if isinstance(vals, dict):
                print(f"  {rel} mixed_effects.cluster_robust_OLS.{grp}: {list(vals.keys())}")
                for k, v in vals.items():
                    print(f"        {k} = {v}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
