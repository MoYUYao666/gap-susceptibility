# -*- coding: utf-8 -*-
r"""Reduce the canonical measurement's memory use, and relaunch with a smaller eval batch.

The retrain failed on every arm with CUDA OOM:

    Tried to allocate 802.00 MiB. GPU 0 has 31.48 GiB of which 675 MiB free ... 30.45 GiB allocated
    measurement failed on batch at 0: OutOfMemoryError

Cause: the canonical measurement now runs a **full forward with `output_hidden_states=True`**, which materialises
a tensor for every one of the 29 layers. At `--eval-batch 32` that is

    29 layers x 32 pairs x 596 tokens x 4096 dims x 2 bytes  ~ 4.5 GB

on top of the model, the optimiser state and the vision-tower activations. The smoke test passed because it used
`--eval-batch 8`.

Two changes:

* the launcher now passes `--eval-batch 8`;
* `_sides` releases the forward's output as soon as the last hidden state is extracted, and runs the pooling in
  `float32` after casting only the two slices it needs, instead of casting the whole hidden state.

    python tools/_p1127_light_measure.py [--apply]
"""
from __future__ import annotations

import argparse
import ast
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SWEEP = REPO / "tools" / "_p820_llava_sites.py"
LAUNCHER = REPO / "tools" / "_p1124_retrain_canonical.sh"
PY = r"D:\Anaconda\envs\pytorch\python.exe"

OLD = """        with torch.no_grad():
            out = mm(**inp, output_hidden_states=True)
        hid = out.hidden_states[-1].float()
        tok = inp["input_ids"]
"""
NEW = """        with torch.no_grad():
            out = mm(**inp, output_hidden_states=True)
            # Keep only the last layer: holding the whole tuple (29 layers) while casting to float32 is what
            # pushed the measurement over the device limit at eval-batch 32.
            hid = out.hidden_states[-1].float()
            del out
        torch.cuda.empty_cache()
        tok = inp["input_ids"]
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = SWEEP.read_text(encoding="utf-8")
    if "del out" in t:
        print("  sweep already releases the forward output")
    else:
        assert t.count(OLD) == 1, f"forward block: found {t.count(OLD)}"
        t = t.replace(OLD, NEW, 1)
        ast.parse(t)
        print("  sweep: forward output released after extracting the last hidden state")
        if a.apply:
            SWEEP.write_text(t, encoding="utf-8", newline="")

    lt = LAUNCHER.read_text(encoding="utf-8")
    if "--eval-batch 8" in lt:
        print("  launcher already uses eval-batch 8")
    else:
        assert "--eval-batch 32" in lt, "eval-batch flag not found in the launcher"
        lt = lt.replace("--eval-batch 32", "--eval-batch 8", 1)
        print("  launcher: eval-batch 32 -> 8 (the canonical measurement keeps all 29 hidden states)")
        if a.apply:
            LAUNCHER.write_text(lt, encoding="utf-8", newline="")

    if not a.apply:
        print("  (dry run)")
        return 0
    r = subprocess.run([PY, "-c", "import ast,io;ast.parse(io.open(r'" + str(SWEEP)
                        + "',encoding='utf-8').read());print('local parse ok')"], capture_output=True)
    print("  " + r.stdout.decode("utf-8", "replace").strip())
    print("  launcher eval-batch:", "8" if "--eval-batch 8" in LAUNCHER.read_text(encoding="utf-8") else "?")
    return 0 if r.returncode == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
