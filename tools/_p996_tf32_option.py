# -*- coding: utf-8 -*-
r"""Add `--tf32` cleanly, with a syntax check on the remote copy before anything is run there.

First attempt failed: the insertion disturbed the existing `if a.deterministic:` block, and a syntax check
that only ran locally reported "ok" while the file that had already been uploaded was broken (the remote
error was `IndentationError` at the `allow_tf32` line). The lesson is written into the script: after
uploading, the remote interpreter parses the file, and if it does not, the run does not start.

The switch itself: the sweep leaves `torch.backends.cuda.matmul.allow_tf32` False, so fp32 matmuls in a bf16
loop run in full fp32. TF32 is the normal path for those on the RTX 40 series. It is a switch, not a silent
default, and its speed is measured before use.

    python tools/_p996_tf32_option.py [--apply]
"""
from __future__ import annotations

import argparse
import ast
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "tools" / "_p820_llava_sites.py"
PY = r"D:\Anaconda\envs\pytorch\python.exe"

ARG_ANCHOR = '    ap.add_argument("--eval-batch", type=int, default=0,\n'
ARG_NEW = ('    ap.add_argument("--tf32", action="store_true",\n'
           '                    help="allow TF32 for fp32 matmuls (default off, as the script has always run)")\n')

# exactly the lines around the determinism block, so the insertion cannot land inside it
DET_BLOCK = ("            if a.deterministic:\n"
             "                torch.backends.cudnn.deterministic = True\n"
             "                torch.backends.cudnn.benchmark = False\n"
             "                torch.backends.cuda.matmul.allow_tf32 = False\n")
TF32_BLOCK = ("            if getattr(a, \"tf32\", False):\n"
              "                torch.backends.cuda.matmul.allow_tf32 = True\n"
              "                torch.backends.cudnn.allow_tf32 = True\n"
              "                print(\"  TF32 enabled for fp32 matmuls\")\n")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    t = SCRIPT.read_text(encoding="utf-8")
    if "--tf32" in t and TF32_BLOCK in t:
        print("  already patched correctly")
        return 0
    if "--tf32" in t and TF32_BLOCK not in t:
        # remove a previous, broken insertion before redoing it
        import re
        t = re.sub(r' *ap\.add_argument\("--tf32".*?\n(?: .*\n)*?.*\)\n', "", t, count=1)
        print("  removed the previous --tf32 argument block")
    assert t.count(ARG_ANCHOR) == 1, "the eval-batch argument was not found exactly once"
    assert t.count(DET_BLOCK) == 1, "the determinism block was not found exactly once"
    out = t.replace(ARG_ANCHOR, ARG_NEW + ARG_ANCHOR, 1)
    out = out.replace(DET_BLOCK, DET_BLOCK + TF32_BLOCK, 1)
    ast.parse(out)
    print("  added --tf32 and the switch beside the determinism block")
    if not a.apply:
        print("  (dry run)")
        return 0
    SCRIPT.write_text(out, encoding="utf-8", newline="")
    r = subprocess.run([PY, "-c", "import ast,io;ast.parse(io.open(r'" + str(SCRIPT)
                        + "',encoding='utf-8').read());print('local parse ok')"], capture_output=True)
    print("  " + r.stdout.decode("utf-8", "replace").strip())
    assert r.returncode == 0, r.stderr.decode("utf-8", "replace")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
