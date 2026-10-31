# -*- coding: utf-8 -*-
r"""Add `--eval-batch` so the held-out measurement does not have to run two pairs at a time.

The measurement path calls `_sides(mm, chunk)` in slices of `a.batch`, so with batch 2 a 500-pair
measurement is 250 forward passes and, at the sizes involved here, several minutes per run. That work is
`torch.no_grad()`, so it can use a much larger slice without affecting what is computed -- only how many
pairs travel together. The training batch is a genuine hyper-parameter and is not touched by this.

    python tools/_p993_eval_batch.py [--apply]
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

ARG_ANCHOR = '    ap.add_argument("--alloc-warmup-gb", type=float, default=0.0,\n'
ARG_NEW = ('    ap.add_argument("--eval-batch", type=int, default=0,\n'
           '                    help="pairs per forward in the held-out measurement (0 = same as --batch)")\n')

MEASURE_RE = re.compile(r"( *)for s in range\(0, len\(batch_ids\), max\(1, a\.batch\)\):\n"
                        r" *chunk = batch_ids\[s:s \+ max\(1, a\.batch\)\]\n")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    t = SCRIPT.read_text(encoding="utf-8")
    if "--eval-batch" in t:
        print("  already patched")
        return 0
    if ARG_ANCHOR in t:
        out = t.replace(ARG_ANCHOR, ARG_NEW + ARG_ANCHOR, 1)
    else:
        anchor = '    ap.add_argument("--precision", choices=["4bit", "bf16"], default="4bit",\n'
        assert t.count(anchor) == 1, "no argument anchor found"
        out = t.replace(anchor, ARG_NEW + anchor, 1)
    m = MEASURE_RE.search(out)
    assert m, "the measurement slicing was not found"
    out = (out[: m.start()]
           + f"{m.group(1)}eb = a.eval_batch or a.batch\n"
           + f"{m.group(1)}for s in range(0, len(batch_ids), eb):\n"
           + f"{m.group(1)}    chunk = batch_ids[s:s + eb]\n"
           + out[m.end():])
    ast.parse(out)
    print("  added --eval-batch; the measurement uses it, training still uses --batch")
    if not a.apply:
        print("  (dry run)")
        return 0
    SCRIPT.write_text(out, encoding="utf-8", newline="")
    r = subprocess.run([PY, "-c", "import ast,io;ast.parse(io.open(r'" + str(SCRIPT)
                        + "',encoding='utf-8').read());print('ok')"], capture_output=True)
    assert r.returncode == 0, r.stderr.decode("utf-8", "replace")
    print("  written; parses on the sweep's interpreter")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
