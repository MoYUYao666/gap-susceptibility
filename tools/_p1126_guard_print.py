# -*- coding: utf-8 -*-
r"""Make the per-run print tolerate a missing measurement.

The frozen arm crashed while formatting the canonical numbers:

    TypeError: unsupported format string passed to NoneType.__format__
      print(f"  canonical DG* {before['dg_star']:.4f} -> {after['dg_star']:.4f} ...")

That happened because the evaluation set was empty (a fixture problem, fixed separately), so `measure()` returned
None. A missing measurement should be reported, not turned into an exception that burns an arm -- the arm guard
caught it, but the sweep then produced no record at all.

    python tools/_p1126_guard_print.py [--apply]
"""
from __future__ import annotations

import argparse
import ast
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "tools" / "_p820_llava_sites.py"
PY = r"D:\Anaconda\envs\pytorch\python.exe"

OLD = '''                print(f"  canonical DG* {before['dg_star']:.4f} -> {after['dg_star']:.4f}  "
                      f"(rel {rec['dg_star_rel_change']:+.3%})  CG {after['cg']:.4f}  "
                      f"DG_emp {after['dg_empirical']:.4f}  ({train_s:.0f}s)")
                print(f"  legacy    DG* {before['legacy_dg']:.4f} -> {after['legacy_dg']:.4f}  "
                      f"(rel {rec['dg_rel_change']:+.3%})")
'''
NEW = '''                def _fmt(v, spec=".4f"):
                    return "n/a" if v is None else format(v, spec)
                print(f"  canonical DG* {_fmt(before['dg_star'])} -> {_fmt(after['dg_star'])}  "
                      f"(rel {_fmt(rec['dg_star_rel_change'], '+.3%')})  CG {_fmt(after['cg'])}  "
                      f"DG_emp {_fmt(after['dg_empirical'])}  ({train_s:.0f}s)")
                print(f"  legacy    DG* {_fmt(before['legacy_dg'])} -> {_fmt(after['legacy_dg'])}  "
                      f"(rel {_fmt(rec['dg_rel_change'], '+.3%')})")
                if after["n"] == 0:
                    print("  !! no evaluation pairs were measured; check the fixture")
'''


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = SCRIPT.read_text(encoding="utf-8")
    if "_fmt(before['dg_star'])" in t:
        print("  already guarded")
        return 0
    assert t.count(OLD) == 1, f"print block: found {t.count(OLD)}"
    t = t.replace(OLD, NEW, 1)
    ast.parse(t)
    print("  the print tolerates None and warns when no pairs were measured")
    if not a.apply:
        print("  (dry run)")
        return 0
    SCRIPT.write_text(t, encoding="utf-8", newline="")
    r = subprocess.run([PY, "-c", "import ast,io;ast.parse(io.open(r'" + str(SCRIPT)
                        + "',encoding='utf-8').read());print('local parse ok')"], capture_output=True)
    print("  " + r.stdout.decode("utf-8", "replace").strip())
    return 0 if r.returncode == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
