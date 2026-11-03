# -*- coding: utf-8 -*-
r"""Store only the trainable weights in the resume checkpoint, not the whole model.

Measured 2026-10-16 12:16: `text_only_s456_ckpt.pt` was **14,367,576,761 bytes** -- the entire 7 B model,
written once per epoch, on a 30 GB root filesystem. The root filesystem hit 100% on the previous attempt
and the checkpoint write died with ENOSPC, which is what ended that sweep with nothing in the log.

The intent of the checkpoint is only to let an interrupted run continue. `arm` decides which tensors are
trainable (about 20 M for a text arm, 3.6 M for a vision arm), so saving just those cuts the file by about
two orders of magnitude and makes the write harmless. Loading uses `strict=False`, so a partial state dict
is accepted and the frozen weights come from the freshly loaded base model as before.

    python tools/_p1016_small_checkpoint.py [--apply]
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

SAVE_RE = re.compile(r"( *)torch\.save\(\{\"model\": \{k: v for k, v in mm\.state_dict\(\)\.items\(\)\},\n")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    t = SCRIPT.read_text(encoding="utf-8")
    if "trainable state only" in t:
        print("  already patched")
        return 0
    m = SAVE_RE.search(t)
    assert m, "the checkpoint save call was not found"
    indent = m.group(1)
    new = (
        f"{indent}# Trainable tensors only. Saving `mm.state_dict()` wrote the whole 7 B model -- measured\n"
        f"{indent}# at 14.4 GB per epoch on a 30 GB filesystem, which filled the disk and killed a run. The\n"
        f"{indent}# checkpoint exists to resume an interrupted arm, and only the trainable tensors change.\n"
        f"{indent}_trainable = {{k: v for k, v in mm.state_dict().items()\n"
        f"{indent}              if any(t is v for t in (p for p in mm.parameters() if p.requires_grad))}}\n"
        f"{indent}torch.save({{\"model\": _trainable,  # trainable state only\n")
    out = t[: m.start()] + new + t[m.end():]
    ast.parse(out)
    print("  checkpoint now stores trainable tensors only")
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
