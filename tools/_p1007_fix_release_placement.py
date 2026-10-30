# -*- coding: utf-8 -*-
r"""Move the release step to where it belongs: before `build(arm)`, outside the frozen branch.

The first placement was wrong twice over, and both were visible in the run:

* it sat **after** `mm = build(arm)`, so it deleted the model that had just been built (the next line then
  failed with `UnboundLocalError: cannot access local variable 'mm'`);
* it sat **inside** `if arm != "frozen":`, so a `frozen` arm never reached it.

Correct position: immediately before `mm = build(arm)`, at the same indentation, so every arm releases the
previous one first.

    python tools/_p1007_fix_release_placement.py [--apply]
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

BUILD = "            mm = build(arm)\n"

RELEASE = (
    "            # Release the previous arm before building this one. Measured 2026-10-16: without this,\n"
    "            # the second arm's load failed with 4.17 GiB free and 26.74 GiB still allocated, because\n"
    "            # every build() loads a new 14 GB model and the old one stayed resident. The allocator\n"
    "            # warm-up cap does not cover that case -- the failing allocation is inside the warm-up.\n"
    "            try:\n"
    "                del mm\n"
    "            except NameError:\n"
    "                pass  # first run: nothing to release\n"
    "            try:\n"
    "                del opt\n"
    "            except NameError:\n"
    "                pass\n"
    "            import gc as _gc\n"
    "            _gc.collect()\n"
    "            torch.cuda.empty_cache()\n"
    "            torch.cuda.reset_peak_memory_stats()\n"
    "            _free, _total = torch.cuda.mem_get_info()\n"
    "            print(f\"  device free before this arm: {_free / 1e9:.1f} GB of {_total / 1e9:.1f} GB\",\n"
    "                  flush=True)  # release_between_runs\n"
    "            if _free < 16e9:\n"
    "                raise SystemExit(\"  not enough device memory to load the next arm; stopping rather \"\n"
    "                                 \"than failing mid-run\")\n")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    t = SCRIPT.read_text(encoding="utf-8")
    # remove the misplaced block (the twelve-space-indented one inside the frozen branch)
    bad = re.search(r"                # Release the previous arm before building this one\..*?"
                    r"than failing mid-run\"\)\n\n", t, re.S)
    assert bad, "the misplaced release block was not found"
    t = t[: bad.start()] + t[bad.end():]
    # drop the now-dangling blank line left inside the branch
    t = t.replace("                mm.train()\n                t0 = time.time()\n\n", 
                  "                mm.train()\n                t0 = time.time()\n")
    if "release_between_runs" in t:
        t = t.replace("  # release_between_runs\n", "")   # any leftover marker
    assert BUILD in t, "the build call was not found"
    out = t.replace(BUILD, RELEASE + BUILD, 1)
    ast.parse(out)
    print("  release step moved before build(arm) and out of the frozen branch")
    if not a.apply:
        print("  (dry run)")
        return 0
    SCRIPT.write_text(out, encoding="utf-8", newline="")
    r = subprocess.run([PY, "-c", "import ast,io;ast.parse(io.open(r'" + str(SCRIPT)
                        + "',encoding='utf-8').read());print('local parse ok')"], capture_output=True)
    print("  " + r.stdout.decode("utf-8", "replace").strip())
    assert r.returncode == 0, r.stderr.decode("utf-8", "replace")
    check = SCRIPT.read_text(encoding="utf-8")
    i_rel = check.find("device free before this arm")
    i_build = check.find(BUILD)
    assert 0 < i_rel < i_build, "the release block is still not before the build"
    print("  verified: the release happens before the build")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
