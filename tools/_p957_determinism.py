# -*- coding: utf-8 -*-
r"""Make repeated runs of the sweep agree with each other, and therefore comparable with the cloud.

Found on 2026-10-15 21:13: two local runs of the **same** parity configuration gave loss 2.9466 and 2.9449
at step 5 -- a difference of 1.7e-3. The script seeds `random`, `numpy` and `torch`, but sets no
determinism switch at all, so cuDNN is free to pick a different convolution algorithm for the vision tower
on every run and bitsandbytes' 4-bit kernels add their own variation. The consequence matters for the plan:
"the cloud must match the local baseline to 1e-3" was too tight to be meaningful.

Two switches are added, both low-risk:

* `torch.backends.cudnn.deterministic = True` and `benchmark = False` -- algorithm selection becomes
  deterministic; this does not disable any kernel the way `use_deterministic_algorithms(True)` can, so the
  4-bit path keeps working.
* `torch.backends.cuda.matmul.allow_tf32 = False` -- keeps matrix multiplications in full precision rather
  than allowing TF32 rounding, which varies with the device.

Seed initialisation stays exactly where it was.

    python tools/_p957_determinism.py [--apply]
"""
from __future__ import annotations

import argparse
import ast
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "tools" / "_p820_llava_sites.py"
PY = r"D:\Anaconda\envs\pytorch\python.exe"

ANCHOR = "            torch.manual_seed(seed)\n"
ADD = ("            # Determinism switches. Without them two runs of the same configuration differ by\n"
       "            # about 1.7e-3 in the first steps (measured 2026-10-15), because cuDNN picks its\n"
       "            # convolution algorithm afresh and 4-bit kernels vary; that is larger than the\n"
       "            # tolerance a cloud comparison against the local baseline needs.\n"
       "            torch.backends.cudnn.deterministic = True\n"
       "            torch.backends.cudnn.benchmark = False\n"
       "            torch.backends.cuda.matmul.allow_tf32 = False\n")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    t = SCRIPT.read_text(encoding="utf-8")
    if "cudnn.deterministic = True" in t:
        print("  already set")
        return 0
    assert t.count(ANCHOR) == 1, f"the seeding line was found {t.count(ANCHOR)} times"
    out = t.replace(ANCHOR, ANCHOR + ADD, 1)
    ast.parse(out)
    print("  added cudnn.deterministic / benchmark=False / allow_tf32=False after torch.manual_seed")
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
