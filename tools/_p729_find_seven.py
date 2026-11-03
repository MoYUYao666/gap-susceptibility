# -*- coding: utf-8 -*-
r"""Find the seven dg_star_history.json files that could take the ledger from 96 back to 103.

The generator globs outputs/theory/**/dg_star_history.json. Tracked files matching that pattern
number 96 now, while the alpha audit recorded 103. So seven such files existed when the audit ran
and are gone (or untracked) now.

This lists what exists on disk versus in git, and looks for candidates outside outputs/theory/.

    python tools/_p729_find_seven.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PUB = REPO / "publish_clean"
WS = REPO


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    print("=" * 108)
    print("1. dg_star_history.json under outputs/theory/: tracked vs on disk")
    print("=" * 108)
    r = subprocess.run(["git", "ls-files", "outputs/theory"], cwd=str(PUB), capture_output=True)
    tracked = [x for x in r.stdout.decode("utf-8", errors="replace").splitlines()
               if x.endswith("dg_star_history.json")]
    disk = [p for p in (PUB / "outputs/theory").rglob("dg_star_history.json") if p.is_file()]
    print(f"  tracked in git : {len(tracked)}")
    print(f"  present on disk: {len(disk)}")
    # also the workspace copy
    ws_disk = [p for p in (WS / "outputs/theory").rglob("dg_star_history.json") if p.is_file()]
    print(f"  workspace copy : {len(ws_disk)}")

    print()
    print("=" * 108)
    print("2. any dg_star_history.json elsewhere in the repo")
    print("=" * 108)
    for base in (PUB / "outputs", WS / "outputs"):
        found = [p for p in base.rglob("dg_star_history.json")
                 if p.is_file() and "theory" not in p.parts]
        if found:
            print(f"  {base}:")
            for p in found[:20]:
                print(f"     {p.relative_to(base)}")
    print()

    print("=" * 108)
    print("3. the per-family breakdown of what the ledger counts now")
    print("=" * 108)
    led = json.loads((PUB / "outputs/analysis/ode_ledger.json").read_text(
        encoding="utf-8", errors="ignore"))
    from collections import Counter
    fams = Counter(r.get("family") for r in led["runs"])
    confs = Counter(r.get("conf") for r in led["runs"])
    print(f"  families: {dict(fams)}")
    print(f"  distinct configs: {len(confs)}")
    # configs present as directories but not in the ledger
    dirs = sorted({str(p.parent.relative_to(PUB / 'outputs/theory'))
                   for p in (PUB / "outputs/theory").rglob("dg_star_history.json")})
    inled = set()
    for r_ in led["runs"]:
        inled.add(str(r_.get("conf")))
    missing = [d for d in dirs if not any(d.endswith(str(c)) or str(c).endswith(d) for c in inled)]
    print(f"  theory dirs with a history file: {len(dirs)}")
    print(f"  of those, not obviously represented in the ledger: {len(missing)}")
    for d in missing[:12]:
        print(f"     {d}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
