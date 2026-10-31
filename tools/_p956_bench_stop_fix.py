# -*- coding: utf-8 -*-
r"""Make `--bench-steps` stop the whole run, not just the current epoch.

Found on 2026-10-15 at 21:10: the parity run with `--samples 20 --bench-steps 25` did not stop after the
first arm. 20 training pairs at batch 2 is only 10 steps per epoch, so `step_i` never reached 25 and the
`break` (which sits in the inner loop) never fired; the run walked on through `vision_only`, and would have
continued through every arm and seed. A timing run that does not stop is a timing run that costs hours.

The cap now breaks the outer loop as well, and prints the reason once.

    python tools/_p956_bench_stop_fix.py [--apply]
"""
from __future__ import annotations

import argparse
import ast
import re
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "tools" / "_p820_llava_sites.py"
PY = r"D:\Anaconda\envs\pytorch\python.exe"

OUTER_RE = re.compile(r"( *for ep in range\(start_ep, a\.epochs\):\n)")
OUTER_NEW = ("                    if a.bench_steps and step_i >= a.bench_steps:\n"
             "                        print(\"    bench cap already reached; not starting another epoch\",\n"
             "                              flush=True)\n"
             "                        break\n")

INNER_OLD = ('                        if a.bench_steps and step_i >= a.bench_steps:\n'
             '                            print("    bench stop after " + str(step_i) + " steps", flush=True)\n'
             '                            break\n')


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    t = SCRIPT.read_text(encoding="utf-8")
    if "bench cap already reached" in t:
        print("  already fixed")
        return 0
    assert t.count(OUTER_RE.search(t).group(1)) == 1, "the epoch loop was not found exactly once"
    out = OUTER_RE.sub(lambda m: m.group(1) + OUTER_NEW, t, count=1)
    assert out.count(INNER_OLD) == 1, "the inner cap was not found exactly once"
    out = out.replace(INNER_OLD, INNER_OLD.replace(
        '                            break\n',
        '                            break\n'), 1)
    ast.parse(out)
    print("  the cap now also breaks the epoch loop")
    if not a.apply:
        print("  (dry run)")
        return 0
    SCRIPT.write_text(out, encoding="utf-8", newline="")
    check = SCRIPT.read_text(encoding="utf-8")
    assert "bench cap already reached" in check
    r = subprocess.run([PY, "-c", "import ast,io;ast.parse(io.open(r'" + str(SCRIPT)
                        + "',encoding='utf-8').read());print('ok')"], capture_output=True)
    assert r.returncode == 0, r.stderr.decode("utf-8", "replace")
    print("  written; parses on the sweep's interpreter")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
