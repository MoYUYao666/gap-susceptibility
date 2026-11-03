# -*- coding: utf-8 -*-
r"""Inventory every per-epoch DG* trajectory in the repository, to see whether the claimed 162 ODE fits are reproducible.

The ODE ledger (`tools/_p1_ledger.py`) fits DG*(t) = DG*_0 + (A/B)(1 - exp(-B t)) to files named
`outputs/theory/**/dg_star_history.json` with at least five epochs, and currently finds 96. The manuscript claims 162
fits (383 = 221 catalogued runs + 162 ODE fits). Before re-running anything, count what trajectories actually exist,
where they live, and how they are keyed -- a re-run is only meaningful if the inputs can be found.

    python tools/_p1175_ode_trajectory_inventory.py
"""
from __future__ import annotations

import glob
import io
import json
import os
import re
from collections import Counter, defaultdict

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def looks_like_trajectory(obj) -> tuple[bool, int]:
    """A trajectory candidate: a dict carrying an epoch list and a DG* series of the same length."""
    if not isinstance(obj, dict):
        return False, 0
    keys = {k.lower() for k in obj}
    epoch_key = next((k for k in obj if k.lower() in ("epochs", "epoch", "steps")), None)
    series_key = next((k for k in obj if "dg_star" in k.lower() or "dgst" in k.lower()), None)
    if not (epoch_key and series_key):
        return False, 0
    e, s = obj[epoch_key], obj[series_key]
    if not (isinstance(e, list) and isinstance(s, list)) or len(e) != len(s):
        return False, 0
    return True, len(e)


def main() -> None:
    canonical, other = [], []
    for f in glob.glob(os.path.join(REPO, "outputs", "**", "*.json"), recursive=True):
        rel = os.path.relpath(f, REPO)
        try:
            obj = json.load(io.open(f, encoding="utf-8", errors="ignore"))
        except Exception:
            continue
        ok, n = looks_like_trajectory(obj)
        if not ok:
            # also inspect one level of nesting, e.g. {"history": {...}} or {"monitor": {...}}
            if isinstance(obj, dict):
                for v in obj.values():
                    ok2, n2 = looks_like_trajectory(v)
                    if ok2:
                        ok, n = True, n2
                        break
        if ok:
            (canonical if rel.endswith("dg_star_history.json") else other).append((rel, n))

    print("=== canonical inputs used by tools/_p1_ledger.py (outputs/theory/**/dg_star_history.json) ===")
    print(f"  files: {len(canonical)}")
    lens = Counter(n for _, n in canonical)
    print(f"  series lengths (epochs): {dict(sorted(lens.items()))}")
    fits = sum(1 for _, n in canonical if n >= 5)
    print(f"  would be fitted (>=5 epochs): {fits}")

    print("\n=== other per-epoch DG* trajectories elsewhere in outputs/ ===")
    print(f"  files: {len(other)}")
    for rel, n in sorted(other)[:20]:
        print(f"    {n:>3} epochs  {rel}")
    if len(other) > 20:
        print(f"    ... and {len(other)-20} more")

    print("\n=== total distinct trajectory files ===")
    print(f"  {len(canonical) + len(other)}")

    # what the ledger currently reports
    led = os.path.join(REPO, "outputs", "analysis", "ode_ledger.json")
    if os.path.exists(led):
        d = json.load(io.open(led, encoding="utf-8"))
        print(f"\n=== current ledger ===")
        print(f"  n_runs_total: {d.get('n_runs_total')}")
        print(f"  n_configs: {d.get('n_configs')}  n_configs_lora: {d.get('n_configs_lora')}")
        fam = Counter(r.get("family") for r in d.get("runs", []))
        print(f"  by family: {dict(fam)}")

    print("\n=== gap ===")
    claimed = 162
    print(f"  manuscript claims {claimed} ODE fits; ledger has {fits} canonical trajectories")
    print(f"  gap: {claimed - fits}")


if __name__ == "__main__":
    main()
