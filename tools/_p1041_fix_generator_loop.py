# -*- coding: utf-8 -*-
r"""Drop the two now-obsolete substitution pairs from the Qwen runner generator.

The measurement rewrite replaced the old three-pair block with a single pair (the whole `_sides` body is
substituted at once), so the loop in `main()` still references `TEXT_OLD` and `IMG2_OLD`, which no longer
exist. This removes those entries, leaving only the model-class, prompt, image-token, tower and `_sides`
replacements.

    python tools/_p1041_fix_generator_loop.py [--apply]
"""
from __future__ import annotations

import argparse
import ast
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
GEN = REPO / "tools" / "_p1034_make_qwen_runner.py"
PY = r"D:\Anaconda\envs\pytorch\python.exe"

OLD = ("""    for old, new, label in ((SIDES_OLD, SIDES_NEW, "measurement submodules"),
                            (TEXT_OLD, TEXT_NEW, "vision/projector call"),
                            (IMG2_OLD, IMG2_NEW, "measurement image token")):
        n = t.count(old)
        assert n == 1, f"{label}: expected one site, found {n}"
        t = t.replace(old, new, 1)
        applied.append(f"{label} x1")
""")
NEW = ("""    # One pair now: the whole `_sides` body is replaced at once, because the Qwen measurement takes both
    # sides from a single forward pass instead of calling the vision tower by hand.
    n = t.count(SIDES_OLD)
    assert n == 1, f"measurement substitution: expected one site, found {n}"
    t = t.replace(SIDES_OLD, SIDES_NEW, 1)
    applied.append("measurement body x1")
""")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = GEN.read_text(encoding="utf-8")
    if "measurement body x1" in t:
        print("  already fixed")
        return 0
    assert OLD in t, "the substitution loop was not found verbatim"
    t = t.replace(OLD, NEW, 1)
    ast.parse(t)
    print("  the loop now substitutes only the measurement body")
    if not a.apply:
        print("  (dry run)")
        return 0
    GEN.write_text(t, encoding="utf-8", newline="")
    r = subprocess.run([PY, "-c", "import ast,io;ast.parse(io.open(r'" + str(GEN)
                        + "',encoding='utf-8').read());print('generator parses ok')"], capture_output=True)
    print("  " + r.stdout.decode("utf-8", "replace").strip())
    return 0 if r.returncode == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
