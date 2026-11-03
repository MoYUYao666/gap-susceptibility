# -*- coding: utf-8 -*-
r"""Stop calling `prepare_model_for_kbit_training` when the model is not quantised.

Measured on the cloud, 2026-10-15 23:0x: the bf16 smoke run died with

    torch.OutOfMemoryError: Tried to allocate 172.00 MiB. GPU 0 has 31.48 GiB, 27.69 MiB free
    ... in peft/utils/other.py:202  param.data = param.data.to(torch.float32)

`prepare_model_for_kbit_training` upcasts every parameter to fp32 -- correct and necessary for a 4-bit
model, whose weights are stored quantised, but fatal for a bf16 7B model, which is already 15 GB and
becomes 30 GB before any activation is allocated.

For the bf16 path the three things that function actually does are applied directly instead:

* gradient checkpointing on (`enable_gradient_checkpointing`),
* `use_cache = False` (incompatible with checkpointing),
* input embeddings requiring grad, so LoRA on the embedding path trains (mirrors the k-bit helper).

Layer-norm upcasting is deliberately **not** copied: it is a stability trick for quantised weights and it
would reintroduce the fp32 copy.

    python tools/_p979_bf16_no_kbit_prepare.py [--apply]
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

OLD_RE = re.compile(
    r"        return prepare_model_for_kbit_training\(m, use_gradient_checkpointing=True\)\n")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    t = SCRIPT.read_text(encoding="utf-8")
    if "bf16 branch below" in t or "not a.precision" in t:
        print("  already fixed")
        return 0
    m = OLD_RE.search(t)
    assert m, "the prepare_model_for_kbit_training line was not found"
    indent = "        "
    new = (
        f"{indent}# For 4-bit the k-bit helper is required: it upcasts parameters to fp32, which a\n"
        f"{indent}# quantised model needs. For bf16 the same call is fatal -- measured 2026-10-15, it took\n"
        f"{indent}# the 15 GB model to 30 GB and the run died with CUDA out of memory before any activation.\n"
        f"{indent}# The bf16 branch below does the parts that matter for training and skips the upcast.\n"
        f"{indent}if a.precision == \"4bit\":\n"
        f"{indent}    return prepare_model_for_kbit_training(m, use_gradient_checkpointing=True)\n"
        f"{indent}m.gradient_checkpointing_enable()\n"
        f"{indent}try:\n"
        f"{indent}    m.config.use_cache = False\n"
        f"{indent}except Exception:\n"
        f"{indent}    pass\n"
        f"{indent}inner = getattr(m, \"model\", m)\n"
        f"{indent}for _name, _mod in ((\"language_model\", getattr(inner, \"language_model\", None)),\n"
        f"{indent}                    (\"vision_tower\", getattr(inner, \"vision_tower\", None))):\n"
        f"{indent}    if _mod is not None:\n"
        f"{indent}        try:\n"
        f"{indent}            _mod.enable_input_require_grads()\n"
        f"{indent}        except Exception:\n"
        f"{indent}            pass\n"
        f"{indent}return m\n")
    out = t[: m.start()] + new + t[m.end():]
    ast.parse(out)
    print("  bf16 path no longer upcasts to fp32; the 4-bit path is untouched")
    if not a.apply:
        print("  (dry run)")
        return 0
    SCRIPT.write_text(out, encoding="utf-8", newline="")
    r = subprocess.run([PY, "-c", "import ast,io;ast.parse(io.open(r'" + str(SCRIPT)
                        + "',encoding='utf-8').read());print('ok')"], capture_output=True)
    assert r.returncode == 0, r.stderr.decode("utf-8", "replace")
    check = SCRIPT.read_text(encoding="utf-8")
    assert 'if a.precision == "4bit":' in check and "enable_input_require_grads" in check
    print("  written; parses on the sweep's interpreter")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
