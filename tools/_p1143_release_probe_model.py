# -*- coding: utf-8 -*-
r"""Release the probe model before training, and measure what that frees.

Evidence from the running sweep (2026-10-17, LLaVA bf16, batch 2):

    GPU memory used            30,454 MiB of 32,760
    time in data loading          33.9 s of 592.5  ( 5.7%)
    time in compute              558.5 s of 592.5  (94.3%)
    tokens per step              1,214
    throughput                  54.1 TFLOPS  ~ 27% of the card's dense BF16 peak

The 30.4 GB is not explainable by a bf16 7B model (~14 GB) plus a 20M-parameter LoRA plus activations. Cause: the
model loaded at the top of `main()` for the tower-name probe is **never released**, while `fresh_base()` loads a
second copy for each arm. Two bf16 copies (28 GB) plus adapters and activations reproduce the measured 30.4 GB.

Consequences, in order of value:

* freeing it costs nothing and does not change any number -- the probe model is dead after `names_for()`;
* it explains the 2026-10-16 conclusion that Qwen2.5-VL-7B "does not fit in 32 GB": that runner has the identical
  double load, so 16.6 GB x 2 = 33.2 GB exceeds the device regardless of batch size, which is exactly the
  "failure point did not move when batch/max-len were reduced" that was observed;
* the freed memory is what makes the real speedups possible: disabling gradient checkpointing (-25% compute) or a
  larger batch (27% peak utilisation at 1,214 tokens/step is far from saturated).

`make_batch()` reads `model.config.image_token_index`, so the id is captured into `IMG_ID` before the model is
released, and both the LLaVA and the Qwen runner are patched (the Qwen one via its own attribute name).

    python tools/_p1143_release_probe_model.py [--apply]
"""
from __future__ import annotations

import argparse
import ast
import re
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PY = r"D:\Anaconda\envs\pytorch\python.exe"

LLAVA = REPO / "tools" / "_p820_llava_sites.py"
QWEN = REPO / "tools" / "_p1135_qwen_sites.py"

# LLaVA: capture the id, then release
LLAVA_ANCHOR = """    print(f"  vision-side layers {len(VIS_NAMES)}   text-side {len(TXT_NAMES)}   "
          f"projector {len(PROJ_NAMES)}")
    print(f"  e.g. vision {VIS_NAMES[0]}")
    print(f"       text   {TXT_NAMES[0]}")
"""
LLAVA_NEW = LLAVA_ANCHOR + """
    # The probe model has done its job: the layer lists above are enough to address the adaptation sites. It was
    # never released, so a second bf16 copy (14 GB here, 16.6 GB for Qwen2.5-VL-7B) stayed resident next to the
    # per-arm model. That is what put this run at 30.4 GB of 32.8 GB, and what made the Qwen run look like it could
    # not fit on a 32 GB card. `make_batch` needs the image-token id, so it is captured first.
    IMG_ID = int(getattr(model.config, "image_token_index", 32000))
    del model
    import gc as _gc
    _gc.collect()
    torch.cuda.empty_cache()
    print(f"  probe model released; image token id {IMG_ID}; "
          f"reserved {torch.cuda.memory_reserved() / 1e9:.1f} GB")
"""

LLAVA_LABEL_OLD = '            img_id = int(getattr(model.config, "image_token_index", 32000))'
LLAVA_LABEL_NEW = '            img_id = IMG_ID'

# Qwen uses `image_token_id`
QWEN_ANCHOR = LLAVA_ANCHOR
QWEN_NEW = LLAVA_ANCHOR + """
    # Same release as the LLaVA sweep. For Qwen2.5-VL-7B this is the difference between 33.2 GB (two bf16 copies,
    # which cannot fit in 32.8 GB no matter the batch) and ~17 GB (one copy, plenty of headroom).
    IMG_ID = int(getattr(model.config, "image_token_id", None)
                 or getattr(model.config, "image_token_index", 151655))
    del model
    import gc as _gc
    _gc.collect()
    torch.cuda.empty_cache()
    print(f"  probe model released; image token id {IMG_ID}; "
          f"reserved {torch.cuda.memory_reserved() / 1e9:.1f} GB")
"""

QWEN_LABEL_OLD = '''            img_id = int(getattr(model.config, "image_token_id", None)
                         or getattr(model.config, "image_token_index", 151655))'''
QWEN_LABEL_NEW = '            img_id = IMG_ID'


def patch(path: Path, anchor: str, new: str, label_old: str, label_new: str) -> bool:
    t = path.read_text(encoding="utf-8")
    if "probe model released" in t:
        print(f"  {path.name}: already patched")
        return True
    n_anchor = t.count(anchor)
    n_label = t.count(label_old)
    print(f"  {path.name}: anchor x{n_anchor}, label site x{n_label}")
    if n_anchor != 1 or n_label != 1:
        print("    !! refusing: expected exactly one of each")
        return False
    t = t.replace(anchor, new, 1).replace(label_old, label_new, 1)
    ast.parse(t)
    path.write_text(t, encoding="utf-8", newline="")
    r = subprocess.run([PY, "-c", "import ast,io;ast.parse(io.open(r'" + str(path)
                        + "',encoding='utf-8').read());print('parse ok')"], capture_output=True)
    print("    " + r.stdout.decode("utf-8", "replace").strip())
    return r.returncode == 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    ok = True
    ok &= patch(LLAVA, LLAVA_ANCHOR, LLAVA_NEW, LLAVA_LABEL_OLD, LLAVA_LABEL_NEW)
    ok &= patch(QWEN, QWEN_ANCHOR, QWEN_NEW, QWEN_LABEL_OLD, QWEN_LABEL_NEW)
    for p in (LLAVA, QWEN):
        if p.exists():
            t = p.read_text(encoding="utf-8")
            print(f"  {p.name}: del model={bool(re.search(r'del +model\\b', t))} "
                  f"IMG_ID used={'img_id = IMG_ID' in t}")
    print("\n  NOTE: the sweep currently running on the host is unaffected -- it already imported its copy, and the")
    print("        host copy is intentionally left alone until the sweep finishes. This patch applies to the next run.")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
