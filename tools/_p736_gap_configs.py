# -*- coding: utf-8 -*-
r"""Find theory configurations that exist on disk but did not make it into the ODE ledger.

The ledger counts 96 runs from outputs/theory/**/dg_star_history.json. The 2026-10-05 audit saw
103. Before re-running anything, establish exactly which configurations are present on disk,
which the ledger includes, and which are missing - a missing fit is re-run only if its
trajectory file exists.

    python tools/_p736_gap_configs.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PUB = REPO / "publish_clean"
THEORY = PUB / "outputs" / "theory"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    led = json.loads((PUB / "outputs/analysis/ode_ledger.json").read_text(
        encoding="utf-8", errors="ignore"))
    runs = led.get("runs") or []

    print("=" * 108)
    print("1. what the ledger holds")
    print("=" * 108)
    print(f"  runs = {len(runs)}")
    confs = Counter(str(r.get("conf")) for r in runs)
    print(f"  distinct conf strings = {len(confs)}")
    for c, n in sorted(confs.items())[:40]:
        print(f"     {n:>3}  {c}")

    print()
    print("=" * 108)
    print("2. theory directories that contain a dg_star_history.json")
    print("=" * 108)
    dirs = sorted({p.parent for p in THEORY.rglob("dg_star_history.json") if p.is_file()})
    print(f"  {len(dirs)} directories")
    # map ledger conf -> set of dirs it could correspond to
    ledger_dirs = set()
    for r in runs:
        c = str(r.get("conf"))
        for d in dirs:
            rel = d.relative_to(THEORY).as_posix()
            if rel == c or rel.replace("/", "_") in c or c in rel:
                ledger_dirs.add(d)
    missing = [d for d in dirs if d not in ledger_dirs]
    print(f"  directories represented in the ledger: {len(ledger_dirs)}")
    print(f"  directories NOT matched to any ledger run: {len(missing)}")
    for d in missing:
        rel = d.relative_to(THEORY).as_posix()
        files = sorted(p.name for p in d.iterdir() if p.is_file())
        print(f"     {rel}")
        print(f"        files: {files}")

    print()
    print("=" * 108)
    print("3. ledger conf values that match no directory")
    print("=" * 108)
    dirnames = {d.relative_to(THEORY).as_posix() for d in dirs}
    unmatched = [c for c in confs if not any(c in dn or dn in c for dn in dirnames)]
    print(f"  {len(unmatched)} unmatched conf strings")
    for c in unmatched[:20]:
        print(f"     {c}")

    print()
    print("=" * 108)
    print("4. families on disk vs in the ledger")
    print("=" * 108)
    print(f"  ledger families: {dict(Counter(str(r.get('family')) for r in runs))}")
    fam_dirs = Counter(d.relative_to(THEORY).parts[0] for d in dirs)
    print(f"  disk top-level families: {dict(fam_dirs)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
