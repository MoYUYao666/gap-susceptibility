# -*- coding: utf-8 -*-
r"""Add a `--precision` switch so the sweep can run the model in bf16 instead of 4-bit.

Operator instruction 2026-10-15: "不要4bit量化，就原模型直接跑，多跑一点". The 4-bit path exists because the
local machine has 8.6 GB; the rented device has 32.8 GB, which holds the 7B weights in bf16 (about 15 GB)
with room for activations, so the 4-bit dequantisation and its rounding are not needed there.

What changes: the `BitsAndBytesConfig` is only built for `--precision 4bit`; bf16 loads the model with
`torch_dtype=torch.bfloat16` and no quantisation config. The pixel tensor follows the same switch (fp16 for
4-bit as before, bf16 for bf16). `prepare_model_for_kbit_training` is still applied, because it is what
enables gradient checkpointing and the input-embedding requirement; it is a no-op for the bit-width part
when the model is not quantised.

Default stays `4bit`, so nothing about the local baseline changes.

    python tools/_p977_bf16_option.py [--apply]
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

ARG_ANCHOR = '    ap.add_argument("--deterministic", action="store_true",\n'
ARG_NEW = ('    ap.add_argument("--precision", choices=["4bit", "bf16"], default="4bit",\n'
           '                    help="4bit matches the published configuration; bf16 needs about 16 GB")\n')

QUANT_RE = re.compile(r"    quant = BitsAndBytesConfig\(load_in_4bit=True, bnb_4bit_quant_type=\"nf4\",\n"
                      r"\s+bnb_4bit_compute_dtype=torch\.bfloat16,\n"
                      r"\s+bnb_4bit_use_double_quant=True\)\n")
QUANT_NEW = ('    # 4-bit is only needed where the device cannot hold the weights; bf16 keeps the model in\n'
             '    # its native precision, which removes the dequantisation rounding entirely.\n'
             '    quant = None\n'
             '    if a.precision == "4bit":\n'
             '        quant = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",\n'
             '                                   bnb_4bit_compute_dtype=torch.bfloat16,\n'
             '                                   bnb_4bit_use_double_quant=True)\n'
             '    pixel_dtype = torch.float16 if a.precision == "4bit" else torch.bfloat16\n'
             '    print(f"  precision: {a.precision}")\n')


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    t = SCRIPT.read_text(encoding="utf-8")
    if "--precision" in t:
        print("  already patched")
        return 0
    assert t.count(ARG_ANCHOR) == 1, "the deterministic argument was not found exactly once"
    assert len(QUANT_RE.findall(t)) == 1, f"the quantisation config matched {len(QUANT_RE.findall(t))} times"
    out = t.replace(ARG_ANCHOR, ARG_NEW + ARG_ANCHOR, 1)
    out = QUANT_RE.sub(QUANT_NEW, out, count=1)

    # the two from_pretrained calls: pass the config only when it exists
    n_cfg = out.count('quantization_config=quant')
    out = out.replace('quantization_config=quant', 'quantization_config=quant if quant else None')
    print(f"  quantization_config call sites updated: {n_cfg}")

    # the pixel dtype, applied in make_batch
    px_old = '        out["pixel_values"] = out["pixel_values"].to(torch.float16)\n'
    px_new = '        out["pixel_values"] = out["pixel_values"].to(pixel_dtype)\n'
    assert out.count(px_old) == 1, f"the pixel dtype line was found {out.count(px_old)} times"
    out = out.replace(px_old, px_new, 1)

    ast.parse(out)
    print("  added --precision {4bit,bf16}; bf16 skips quantisation and keeps pixels in bf16")
    if not a.apply:
        print("  (dry run)")
        return 0
    SCRIPT.write_text(out, encoding="utf-8", newline="")
    r = subprocess.run([PY, "-c", "import ast,io;ast.parse(io.open(r'" + str(SCRIPT)
                        + "',encoding='utf-8').read());print('ok')"], capture_output=True)
    assert r.returncode == 0, r.stderr.decode("utf-8", "replace")
    check = SCRIPT.read_text(encoding="utf-8")
    assert 'a.precision == "bf16"' in check or "pixel_dtype" in check
    print("  written; parses on the sweep's interpreter")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
