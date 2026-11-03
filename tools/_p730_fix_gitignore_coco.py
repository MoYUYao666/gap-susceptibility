# -*- coding: utf-8 -*-
r"""Fix the .gitignore rule that was hiding nine result files, then recount the ledger population.

Root cause of the 222 vs 215 discrepancy:

  .gitignore line 54 is "coco/", which has no leading slash, so it matches a directory named coco
  at ANY depth - including outputs/theory/coco/, which holds result data. The rule was meant for
  the MS-COCO dataset at the repository root. Nine dg_star_history.json files were therefore
  excluded from the archive, and the ledger population the paper describes cannot be reproduced
  from what is published.

Fix: anchor the dataset rules with a leading slash, then add the nine files.

    python tools/_p730_fix_gitignore_coco.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PUB = REPO / "publish_clean"

# dataset directories at the repository root: anchor them so a nested directory of the same
# name (e.g. outputs/theory/coco) is not excluded
ANCHOR = ["coco/", "flickr30k/", "data/", "datasets/"]

NINE = [
    "outputs/theory/coco/coco_both_r8/seed123/dg_star_history.json",
    "outputs/theory/coco/coco_both_r8/seed42/dg_star_history.json",
    "outputs/theory/coco/coco_both_r8/seed456/dg_star_history.json",
    "outputs/theory/coco/coco_full_ft/seed123/dg_star_history.json",
    "outputs/theory/coco/coco_full_ft/seed42/dg_star_history.json",
    "outputs/theory/coco/coco_full_ft/seed456/dg_star_history.json",
    "outputs/theory/coco/coco_text_r8/seed123/dg_star_history.json",
    "outputs/theory/coco/coco_text_r8/seed42/dg_star_history.json",
    "outputs/theory/coco/coco_text_r8/seed456/dg_star_history.json",
]


def git(*args):
    r = subprocess.run(["git"] + list(args), cwd=str(PUB), capture_output=True)
    return r.returncode, r.stdout.decode("utf-8", errors="replace"), r.stderr.decode("utf-8", "replace")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    gi = PUB / ".gitignore"
    t = gi.read_text(encoding="utf-8", errors="replace")
    print("=" * 104)
    print("current dataset rules")
    print("=" * 104)
    for line in t.splitlines():
        if line.strip() in ANCHOR or line.strip().startswith("#"):
            continue
    for name in ANCHOR:
        print(f"  {'present' if name in t else 'absent '}  {name}")

    new = t
    for name in ANCHOR:
        if f"\n{name}" in new:
            new = new.replace(f"\n{name}", f"\n/{name}")
    changed = new != t
    print()
    print(f"  anchoring changes the file: {changed}")
    if a.apply and changed:
        shutil.copy2(gi, gi.with_suffix(".gitignore.bak_p730"))
        gi.write_text(new, encoding="utf-8", newline="")
        print("  .gitignore rewritten")

    if not a.apply:
        print("  (dry run)")
        return 0

    print()
    print("=" * 104)
    print("add the nine result files")
    print("=" * 104)
    for f in NINE:
        p = PUB / f
        print(f"  {'exists' if p.exists() else 'MISSING'}  {f}")

    print()
    print("=" * 104)
    print("recount")
    print("=" * 104)
    rc, out, _ = git("ls-files", "outputs/theory")
    tracked = [x for x in out.splitlines() if x.endswith("dg_star_history.json")]
    print(f"  tracked dg_star_history.json before adding: {len(tracked)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
