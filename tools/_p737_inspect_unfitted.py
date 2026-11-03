# -*- coding: utf-8 -*-
r"""Inspect the theory families the ledger does not fit, especially beta_pilot (nine directories).

The ledger covers 96 of the 96 directories that hold a dg_star_history.json, so nothing with a
trajectory is being skipped. But disk also holds beta_pilot/ with nine directories and verify_accum/
with two. Seven missing runs would explain the 103 the audit saw.

This lists what each of those directories contains, and whether a trajectory could be fitted.

    python tools/_p737_inspect_unfitted.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PUB = REPO / "publish_clean"
THEORY = PUB / "outputs" / "theory"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    for fam in ("beta_pilot", "verify_accum", "coco", "v1_trajectory"):
        d = THEORY / fam
        if not d.exists():
            print(f"  {fam}: not present")
            continue
        dirs = sorted({p.parent for p in d.rglob("*") if p.is_file()})
        print("=" * 104)
        print(f"{fam}: {len(dirs)} directories with files")
        print("=" * 104)
        for dd in dirs:
            files = sorted(p.name for p in dd.iterdir() if p.is_file())
            rel = dd.relative_to(THEORY).as_posix()
            has_traj = "dg_star_history.json" in files
            print(f"  {rel:<44} traj={'yes' if has_traj else 'NO '}  {files}")
        print()

    print("=" * 104)
    print("summary: directories with a trajectory, by family")
    print("=" * 104)
    tot = 0
    for fam in sorted({p.relative_to(THEORY).parts[0] for p in THEORY.rglob("dg_star_history.json")}):
        n = len({p.parent for p in (THEORY / fam).rglob("dg_star_history.json")})
        tot += n
        print(f"  {fam:<20} {n:>4}")
    print(f"  {'TOTAL':<20} {tot:>4}")
    print()
    print(f"  the ledger fits {tot} of them; the 2026-10-05 audit recorded 103")
    print(f"  difference: {103 - tot}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
