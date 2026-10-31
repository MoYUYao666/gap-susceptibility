# -*- coding: utf-8 -*-
r"""Cap the allocator warm-up, which is what makes bf16 fail to load on a 24 GB device.

The second host (RTX 4090 D, 23.52 GiB usable) died while loading bf16:

    Tried to allocate 13.15 GiB. GPU 0 has a total capacity of 23.52 GiB of which 10.01 GiB is free.

The 13.15 GiB is `caching_allocator_warmup` in transformers 5.16.1, which reserves a buffer of the model's
own size before loading so that the loading itself cannot fragment. Neither PyTorch nor transformers offers
a switch for it in this version (it is called unconditionally at modeling_utils.py:4473, and its only
escape clauses are for mps and neuron devices), so the function is wrapped at run time and its reservation
is capped by a flag:

    --alloc-warmup-gb 2.0    reserve at most 2 GB (default keeps the behaviour above that)

The wrapper calls the original function for every device except cuda, and for cuda it temporarily reports a
smaller device so the original arithmetic does the capping -- that way the logic stays inside transformers
and only the number changes.

    python tools/_p988_alloc_warmup_cap.py [--apply]
"""
from __future__ import annotations

import argparse
import ast
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "tools" / "_p820_llava_sites.py"
PY = r"D:\Anaconda\envs\pytorch\python.exe"

ARG_ANCHOR = '    ap.add_argument("--precision", choices=["4bit", "bf16"], default="4bit",\n'
ARG_NEW = ('    ap.add_argument("--alloc-warmup-gb", type=float, default=0.0,\n'
           '                    help="cap the model-loading allocator reservation in GB (0 = transformers default)")\n')

# inserted just before the model is built, so it applies to both from_pretrained calls
HOOK_ANCHOR = "    print(f\"  loading {MODEL} in 4-bit nf4 ...\")\n"
HOOK_NEW = '''    if a.alloc_warmup_gb:
        # transformers reserves a buffer the size of the model before loading it (caching_allocator_warmup).
        # On a device where the weights nearly fill the memory that reservation cannot be satisfied, and the
        # load fails with CUDA out of memory even though the model itself would fit. Wrapping the function
        # and shrinking the reported device size keeps transformers' own capping arithmetic in charge.
        import transformers.modeling_utils as _mu
        _orig_warmup = _mu.caching_allocator_warmup

        def _capped_warmup(model, expanded_device_map, hf_quantizer):
            class _Small:
                type = "cuda"
                index = 0

                def __init__(self, size):
                    self._size = size

                @property
                def total_memory(self):
                    return self._size

            import torch as _t
            real = _t.cuda.get_device_properties(0).total_memory
            small = int(a.alloc_warmup_gb * 1024 ** 3)
            props = _Small(small)

            class _Props:
                @staticmethod
                def get_device_properties(_i):
                    return props
            real_get = _t.cuda.get_device_properties
            _t.cuda.get_device_properties = _Props.get_device_properties
            try:
                print(f"  allocator warmup capped: reporting {small / 1e9:.1f} GB instead of "
                      f"{real / 1e9:.1f} GB")
                return _orig_warmup(model, expanded_device_map, hf_quantizer)
            finally:
                _t.cuda.get_device_properties = real_get

        _mu.caching_allocator_warmup = _capped_warmup
'''


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    t = SCRIPT.read_text(encoding="utf-8")
    if "--alloc-warmup-gb" in t:
        print("  already patched")
        return 0
    assert t.count(ARG_ANCHOR) == 1, "the precision argument was not found exactly once"
    assert t.count(HOOK_ANCHOR) == 1, "the loading banner was not found exactly once"
    out = t.replace(ARG_ANCHOR, ARG_NEW + ARG_ANCHOR, 1).replace(HOOK_ANCHOR, HOOK_NEW + HOOK_ANCHOR, 1)
    ast.parse(out)
    print("  added --alloc-warmup-gb and the bounded warm-up wrapper")
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
