# -*- coding: utf-8 -*-
r"""Fix a false failure in the verification gate: the process check matched its own command line.

The gate reported "a sweep process is still running" although the sweep had exited with `EXIT=0` and the
device was idle:

    === finished? log says done: True, process alive: True
    NOT SOUND -- a sweep process is still running

The cause is the check itself:

    pgrep -af _p820_llava_sites | head -2

`pgrep -f` matches any process whose full command line contains the pattern, and the pattern is carried by
the shell that is running the check, so the check always finds at least itself. That is why the failure
appeared at the same moment the log said the sweep was done. The replacement filters the checker out
(`grep -v grep`-style) and prints the matching command lines, so a real leftover would be visible.

This is the same class of mistake as the earlier `log.count("undefined")` false failure: the checker
measuring something other than what it claims. The fix is asserted here, and the gate is re-run afterwards.

    python tools/_p1027_fix_process_check.py [--apply]
"""
from __future__ import annotations

import argparse
import ast
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
GATE = REPO / "tools" / "_p984_verify_cloud_results.py"
PY = r"D:\Anaconda\envs\pytorch\python.exe"

OLD = '    alive = sh("pgrep -af _p820_llava_sites | head -2")\n'
NEW = ('    # `pgrep -f <pattern>` also matches the shell that runs this check, because the pattern is part of\n'
       '    # its command line. Listing the processes and excluding the checker avoids that self-match; the\n'
       '    # measured state on 2026-10-16 was `NO SWEEP PROCESS` with the device idle at 1 MiB.\n'
       '    alive = sh("ps -eo pid,etimes,cmd | grep _p820_llava_sites | grep -v grep "\n'
       '               "| grep -v _p984_verify || echo NONE")\n')


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = GATE.read_text(encoding="utf-8")
    if "ps -eo pid,etimes,cmd" in t:
        print("  already fixed")
        return 0
    assert t.count(OLD) == 1, "the process check was not found exactly once"
    t = t.replace(OLD, NEW, 1)
    t = t.replace('    still_running = bool(alive.strip())\n',
                  '    still_running = "NONE" not in alive and bool(alive.strip())\n', 1)
    ast.parse(t)
    print("  process check no longer matches its own command line")
    if not a.apply:
        print("  (dry run)")
        return 0
    GATE.write_text(t, encoding="utf-8", newline="")
    r = subprocess.run([PY, "-c", "import ast,io;ast.parse(io.open(r'" + str(GATE)
                        + "',encoding='utf-8').read());print('local parse ok')"], capture_output=True)
    print("  " + r.stdout.decode("utf-8", "replace").strip())
    assert r.returncode == 0, r.stderr.decode("utf-8", "replace")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
