# -*- coding: utf-8 -*-
r"""Free the previous model before building the next one.

The real cause of the two OOMs, confirmed by reading the traceback rather than guessing: every arm calls
`build(arm)`, which loads a fresh 14 GB model, and **the old model is never released**. The measured state
at the failure was

    GPU 0 has a total capacity of 31.48 GiB of which 4.17 GiB is free
    this process has 27.29 GiB memory in use ... 26.74 GiB is allocated by PyTorch

That 26.74 GiB is the previous arm's model plus its optimizer and activations, still resident. The next
load then needs 13 GiB it cannot get. The allocator warm-up cap added earlier does not help, because the
failing allocation happens *inside* the transformers warm-up itself.

The fix is to release between runs: drop the model reference, empty the CUDA cache, and collect. This is
placed at the top of the per-run loop, just before `build(arm)`, and it is a no-op on the first run.

    python tools/_p1006_release_between_runs.py [--apply]
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

ANCHOR = re.compile(r"( *)# ---- step timing, added 2026-10-15 -+ *\n")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    t = SCRIPT.read_text(encoding="utf-8")
    if "release_between_runs" in t:
        print("  already patched")
        return 0
    m = ANCHOR.search(t)
    assert m, "the step-timing comment was not found"
    indent = m.group(1)
    block = (
        f"{indent}# Release the previous arm before building this one. Measured 2026-10-16: without this,\n"
        f"{indent}# the second arm's load failed with 4.17 GiB free and 26.74 GiB still allocated, because\n"
        f"{indent}# every build() loads a new 14 GB model and the old one stayed resident. The allocator\n"
        f"{indent}# warm-up cap does not cover this case -- the failing allocation is inside the warm-up.\n"
        f"{indent}try:\n"
        f"{indent}    del mm\n"
        f"{indent}except NameError:\n"
        f"{indent}    pass  # first run: nothing to release\n"
        f"{indent}try:\n"
        f"{indent}    del opt\n"
        f"{indent}except NameError:\n"
        f"{indent}    pass\n"
        f"{indent}import gc as _gc\n"
        f"{indent}_gc.collect()\n"
        f"{indent}torch.cuda.empty_cache()\n"
        f"{indent}torch.cuda.reset_peak_memory_stats()\n"
        f"{indent}_free, _total = torch.cuda.mem_get_info()\n"
        f"{indent}print(f\"  released the previous arm; device now has {{_free / 1e9:.1f}} GB free of \"\n"
        f"{indent}      f\"{{_total / 1e9:.1f}} GB\", flush=True)  # release_between_runs\n"
        f"{indent}if _free < 16e9:\n"
        f"{indent}    raise SystemExit(\"  not enough device memory to load the next arm; stopping rather \"\n"
        f"{indent}                     \"than failing mid-run\")\n\n")
    out = t[: m.start()] + block + t[m.start():]
    ast.parse(out)
    print("  added a release step (del model/optimiser, gc, empty_cache) before each build")
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
