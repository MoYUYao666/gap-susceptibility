# -*- coding: utf-8 -*-
r"""Confirm that everything fitted is now published, and that nothing is left only on disk.

Two questions to answer with evidence:
  1. Does the published repository contain every theory directory that holds a trajectory?
     (Before the ignore-rule fix, nine coco directories were excluded.)
  2. Are there runs elsewhere in outputs/ that the paper's statistics might legitimately include
     and that are still unpublished?

    python tools/_p738_confirm_published.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PUB = REPO / "publish_clean"


def git(*args):
    r = subprocess.run(["git"] + list(args), cwd=str(PUB), capture_output=True)
    return r.stdout.decode("utf-8", errors="replace")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    print("=" * 106)
    print("1. theory trajectory directories: tracked vs on disk")
    print("=" * 106)
    tracked = {l for l in git("ls-files", "outputs/theory").splitlines()
               if l.endswith("dg_star_history.json")}
    disk = {p.relative_to(PUB).as_posix()
            for p in (PUB / "outputs/theory").rglob("dg_star_history.json") if p.is_file()}
    print(f"  tracked : {len(tracked)}")
    print(f"  on disk : {len(disk)}")
    only_disk = disk - tracked
    only_git = tracked - disk
    print(f"  only on disk (unpublished): {len(only_disk)}")
    for f in sorted(only_disk)[:10]:
        print(f"     {f}")
    print(f"  only in git (file deleted locally): {len(only_git)}")
    for f in sorted(only_git)[:10]:
        print(f"     {f}")

    print()
    print("=" * 106)
    print("2. trajectory directories by family, published")
    print("=" * 106)
    fams = Counter(Path(f).relative_to("outputs/theory").parts[0] for f in tracked)
    for k, v in sorted(fams.items()):
        print(f"  {k:<20} {v:>4}")
    print(f"  {'TOTAL':<20} {sum(fams.values()):>4}")

    print()
    print("=" * 106)
    print("3. other dg_star_history.json outside outputs/theory (not in the ledger's rule)")
    print("=" * 106)
    allt = [l for l in git("ls-files", "outputs").splitlines()
            if l.endswith("dg_star_history.json")]
    outside = [f for f in allt if not f.startswith("outputs/theory/")]
    print(f"  {len(outside)} file(s):")
    for f in outside:
        print(f"     {f}")
    print()
    print("  these are NOT in the ledger, whose rule is outputs/theory/** only:")
    print("  the paper's fit total is therefore the 96 in outputs/theory, plus the")
    print("  auxiliary fits in ode_loco/ode_loco2/adapter_all/bitfit archives.")

    print()
    print("=" * 106)
    print("4. final check: is any published result file still tracked-but-missing or untracked?")
    print("=" * 106)
    untracked = [l[3:].strip() for l in git("status", "--porcelain",
                                            "--untracked-files=all").splitlines()
                 if l.startswith("?? ")]
    print(f"  untracked files under outputs/: "
          f"{len([f for f in untracked if f.startswith('outputs/')])}")
    print(f"  total untracked: {len(untracked)}")
    if untracked:
        for f in untracked[:10]:
            print(f"     {f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
