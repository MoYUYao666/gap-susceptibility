# -*- coding: utf-8 -*-
r"""Decide whether Paper A's strict-freezing control count should be 95 or 104.

The author does not remember. The evidence available:

- sections/supplement.tex has a category table (tab:full_experiments) whose XIV row says 104 and
  whose Total says 221; its prose in the same file says 95.
- sections/empirical.tex says "117 under the earlier convention and 95 under strict freezing".
- sections/conclusion.tex says 95.
- HANDOFF L10175/L10193 records a correction 95 -> 104 after adding BioCLIP, measured 104.

So the number has to be decided from the archive: count the strict-freezing runs that the paper's
own protocol definition covers, per backbone and per rank, and see which of 95 / 104 the data
supports.

    python tools/_p722_decide_95_or_104.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PUB = REPO / "publish_clean"
PA = REPO / "paper合"
OUT = REPO / "outputs" / "analysis" / "decide_95_104.json"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    print("=" * 112)
    print("1. the paper's own category table, in full")
    print("=" * 112)
    supp = (PA / "sections" / "supplement.tex").read_text(encoding="utf-8", errors="replace")
    m = re.search(r"\\begin\{longtable\}.*?\\end\{longtable\}", supp, re.S)
    if m:
        rows = re.findall(r"^(.{0,90}?)\s*&\s*(\d+)\s*\\\\", m.group(0), re.M)
        tot = 0
        for label, n in rows:
            label = " ".join(label.split())
            if "Total" in label or "midrule" in label:
                continue
            tot += int(n)
            print(f"     {int(n):>4}   {label}")
        print(f"     ----   sum of category rows = {tot}")
    print()
    print("  prose in the same file:")
    for mm in re.finditer(r"[^.]*strict-freezing[^.]*\.", supp):
        print("     " + " ".join(mm.group(0).split())[:220])

    print()
    print("=" * 112)
    print("2. strict-freezing runs actually in the archive, by directory")
    print("=" * 112)
    r = subprocess.run(["git", "ls-files", "outputs"], cwd=str(PUB), capture_output=True)
    files = [x for x in r.stdout.decode("utf-8", errors="replace").splitlines() if x.strip()]
    sf = [f for f in files if "strict_freeze" in f or "strictfreeze" in f
          or "vlm_strict" in f or "siglip_strict" in f]
    print(f"  {len(sf)} tracked files match a strict-freeze path")
    # per config directory, count result files
    per_dir = defaultdict(int)
    for f in sf:
        if f.endswith("results.json"):
            parts = f.split("/")
            key = "/".join(parts[:2]) if len(parts) > 2 else parts[0]
            per_dir[key] += 1
    total = 0
    for k, v in sorted(per_dir.items()):
        print(f"     {v:>4}   {k}")
        total += v
    print(f"     ----   results.json total = {total}")
    # also by (dir, arm) to see the structure
    print()
    print("  by directory and arm:")
    per_arm = defaultdict(int)
    for f in sf:
        if f.endswith("results.json"):
            parts = f.split("/")
            if len(parts) >= 4:
                per_arm[(parts[1], parts[2])] += 1
            else:
                per_arm[(parts[1], "-")] += 1
    for k, v in sorted(per_arm.items()):
        print(f"     {v:>4}   {k[0]:<28} {k[1]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
