# -*- coding: utf-8 -*-
r"""Store the canonical metric in each run record, and print it.

`measure()` now returns a dict (`cg`, `legacy_dg`, `dg_star`, `dg_empirical`, `n`) instead of a 3-tuple, so the
three consumers have to change: the record fields, the console line, and the early "before" slice. Each record
keeps the legacy keys under their old names so it stays comparable with the archived twelve, and adds the
canonical ones under `dg_star_*` / `cg_*` / `dg_emp_*`.

    python tools/_p1119_record_canonical.py [--apply]
"""
from __future__ import annotations

import argparse
import ast
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "tools" / "_p820_llava_sites.py"
PY = r"D:\Anaconda\envs\pytorch\python.exe"

OLD_REC = '''                       "cg_before": before[0], "cg_after": after[0],
                       "dg_before": before[1], "dg_after": after[1],
                       "dg_rel_change": (None if not before[1] or before[1] == 0
                                         else (after[1] - before[1]) / before[1]),
                       "n_eval": after[2], "train_seconds": round(train_s, 1),
'''
NEW_REC = '''                       # legacy definition (the archived twelve used this), kept for comparison
                       "cg_before": before["cg"], "cg_after": after["cg"],
                       "dg_before": before["legacy_dg"], "dg_after": after["legacy_dg"],
                       "dg_rel_change": (None if not before["legacy_dg"] or before["legacy_dg"] == 0
                                         else (after["legacy_dg"] - before["legacy_dg"])
                                         / before["legacy_dg"]),
                       # canonical definition (src/dg_star_tracker.py) -- the quantity the paper and ODE use
                       "dg_star_before": before["dg_star"], "dg_star_after": after["dg_star"],
                       "dg_star_rel_change": (None if not before["dg_star"] or before["dg_star"] == 0
                                              else (after["dg_star"] - before["dg_star"])
                                              / before["dg_star"]),
                       "cg_canonical_before": before["cg"], "cg_canonical_after": after["cg"],
                       "dg_empirical_before": before["dg_empirical"],
                       "dg_empirical_after": after["dg_empirical"],
                       "n_eval": after["n"], "train_seconds": round(train_s, 1),
'''
OLD_PRINT = '''                print(f"  DG* {before[1]:.4f} -> {after[1]:.4f}  (rel {rec['dg_rel_change']:+.3%})  "
                      f"CG {before[0]:.4f} -> {after[0]:.4f}  ({train_s:.0f}s)")
'''
NEW_PRINT = '''                print(f"  canonical DG* {before['dg_star']:.4f} -> {after['dg_star']:.4f}  "
                      f"(rel {rec['dg_star_rel_change']:+.3%})  CG {after['cg']:.4f}  "
                      f"DG_emp {after['dg_empirical']:.4f}  ({train_s:.0f}s)")
                print(f"  legacy    DG* {before['legacy_dg']:.4f} -> {after['legacy_dg']:.4f}  "
                      f"(rel {rec['dg_rel_change']:+.3%})")
'''


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = SCRIPT.read_text(encoding="utf-8")
    if "dg_star_before" in t:
        print("  already recorded")
        return 0
    for old, new, label in ((OLD_REC, NEW_REC, "record fields"), (OLD_PRINT, NEW_PRINT, "console line")):
        n = t.count(old)
        assert n == 1, f"{label}: expected one occurrence, found {n}"
        t = t.replace(old, new, 1)
    ast.parse(t)
    print("  records and console now carry both definitions")
    if not a.apply:
        print("  (dry run)")
        return 0
    SCRIPT.write_text(t, encoding="utf-8", newline="")
    r = subprocess.run([PY, "-c", "import ast,io;ast.parse(io.open(r'" + str(SCRIPT)
                        + "',encoding='utf-8').read());print('local parse ok')"], capture_output=True)
    print("  " + r.stdout.decode("utf-8", "replace").strip())
    if r.returncode != 0:
        print(r.stderr.decode("utf-8", "replace"))
        return 1
    check = SCRIPT.read_text(encoding="utf-8")
    for needle in ("dg_star_before", "dg_star_rel_change", "dg_empirical_after"):
        print(f"    {needle:<22} {needle in check}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
