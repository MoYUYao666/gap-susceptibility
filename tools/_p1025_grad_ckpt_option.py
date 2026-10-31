# -*- coding: utf-8 -*-
r"""Add a switch for gradient checkpointing so its cost can be measured instead of assumed.

The operator asked whether the device's memory is what caps the speed ("是显存限制了速度上限吗"). The evidence
so far says no: raising the batch did not help (batch 4 is 6% faster per step, batch 8 is slower), which is
not the signature of a memory-capacity limit. Two candidates remain:

* the cost of reading the weights, which every step pays regardless of batch;
* gradient checkpointing, which `--precision bf16` turns on by default and which recomputes every layer's
  forward pass during the backward pass -- roughly doubling the work per step. The `--precision 4bit` path
  enables it through `prepare_model_for_kbit_training`, and the bf16 path enables it directly.

This adds `--no-grad-ckpt` so the two can be compared on the same 25 steps. Memory may make the comparison
impossible for the larger arms, in which case the run says so rather than guessing.

    python tools/_p1025_grad_ckpt_option.py [--apply]
"""
from __future__ import annotations

import argparse
import ast
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "tools" / "_p820_llava_sites.py"
PY = r"D:\Anaconda\envs\pytorch\python.exe"

ARG_ANCHOR = '    ap.add_argument("--tf32", action="store_true",\n'
ARG_NEW = ('    ap.add_argument("--no-grad-ckpt", action="store_true",\n'
           '                    help="disable gradient checkpointing (default on: it saves memory, costs time)")\n')

OLD = "        m.gradient_checkpointing_enable()\n"
NEW = ("        if not getattr(a, \"no_grad_ckpt\", False):\n"
       "            m.gradient_checkpointing_enable()\n"
       "        else:\n"
       "            print(\"  gradient checkpointing DISABLED for this run\")\n"
       "            m.gradient_checkpointing_disable()\n")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    t = SCRIPT.read_text(encoding="utf-8")
    if "--no-grad-ckpt" in t:
        print("  already patched")
        return 0
    assert t.count(ARG_ANCHOR) == 1, "no argument anchor"
    assert t.count(OLD) == 1, "the checkpointing call was not found exactly once"
    t = t.replace(ARG_ANCHOR, ARG_NEW + ARG_ANCHOR, 1).replace(OLD, NEW, 1)
    ast.parse(t)
    print("  added --no-grad-ckpt")
    if not a.apply:
        print("  (dry run)")
        return 0
    SCRIPT.write_text(t, encoding="utf-8", newline="")
    r = subprocess.run([PY, "-c", "import ast,io;ast.parse(io.open(r'" + str(SCRIPT)
                        + "',encoding='utf-8').read());print('local parse ok')"], capture_output=True)
    print("  " + r.stdout.decode("utf-8", "replace").strip())
    assert r.returncode == 0, r.stderr.decode("utf-8", "replace")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
