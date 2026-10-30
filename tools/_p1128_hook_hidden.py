# -*- coding: utf-8 -*-
r"""Capture the final hidden state with a hook instead of `output_hidden_states=True`.

Why: the canonical measurement needs only the last layer, but asking the model for `output_hidden_states=True`
made transformers materialise the whole per-layer stack and blew the device:

    tried to allocate 102 MiB ... 31.42 GiB in use, 29.81 GiB allocated by PyTorch
    Arm failed: frozen_s42: OutOfMemoryError

even at `--eval-batch 8` (29 layers x 8 pairs x 596 tokens x 4096 dims is only ~1.1 GB, so the flag costs far more
than the tensor it promises). The input to `lm_head` *is* the final hidden state, so a `forward_pre_hook` there
captures it for the price of one tensor and leaves the model's normal memory profile untouched.

    python tools/_p1128_hook_hidden.py [--apply]
"""
from __future__ import annotations

import argparse
import ast
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SWEEP = REPO / "tools" / "_p820_llava_sites.py"
PY = r"D:\Anaconda\envs\pytorch\python.exe"

OLD = """        with torch.no_grad():
            out = mm(**inp, output_hidden_states=True)
            # Keep only the last layer: holding the whole tuple (29 layers) while casting to float32 is what
            # pushed the measurement over the device limit at eval-batch 32.
            hid = out.hidden_states[-1].float()
            del out
        torch.cuda.empty_cache()
        tok = inp["input_ids"]
"""

NEW = """        # The last hidden state is the input to `lm_head`. A pre-hook there captures exactly that tensor and
        # costs nothing else, whereas `output_hidden_states=True` made transformers materialise the whole
        # 29-layer stack and overflowed the device even at eval-batch 8 (29.81 GiB allocated).
        base = mm
        while hasattr(base, "get_base_model"):
            nxt = base.get_base_model()
            if nxt is base:
                break
            base = nxt
        lm_head = getattr(base, "lm_head", None)
        if lm_head is None:
            raise RuntimeError(f"no lm_head on {type(base).__name__}")
        cap = {}

        def _grab(_mod, inputs):
            cap["hid"] = inputs[0]

        h = lm_head.register_forward_pre_hook(_grab)
        try:
            with torch.no_grad():
                mm(**inp)
        finally:
            h.remove()
        if "hid" not in cap:
            raise RuntimeError("the lm_head hook did not fire")
        hid = cap["hid"].float()
        del cap
        tok = inp["input_ids"]
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = SWEEP.read_text(encoding="utf-8")
    if "register_forward_pre_hook" in t:
        print("  already using the hook")
        return 0
    assert t.count(OLD) == 1, f"forward block: found {t.count(OLD)}"
    t = t.replace(OLD, NEW, 1)
    ast.parse(t)
    print("  measurement now hooks lm_head; output_hidden_states is gone")
    if not a.apply:
        print("  (dry run)")
        return 0
    SWEEP.write_text(t, encoding="utf-8", newline="")
    r = subprocess.run([PY, "-c", "import ast,io;ast.parse(io.open(r'" + str(SWEEP)
                        + "',encoding='utf-8').read());print('local parse ok')"], capture_output=True)
    print("  " + r.stdout.decode("utf-8", "replace").strip())
    check = SWEEP.read_text(encoding="utf-8")
    print("  output_hidden_states removed:", "output_hidden_states=True" not in check)
    return 0 if r.returncode == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
