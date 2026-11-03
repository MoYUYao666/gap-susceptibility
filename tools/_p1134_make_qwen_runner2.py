# -*- coding: utf-8 -*-
r"""Generate a Qwen2.5-VL runner from the current, fixed LLaVA sweep.

Yesterday's Qwen runner was built from an older frozen copy and inherited two problems: the measurement compared
projected vision features with token embeddings (and implicitly included image tokens in the text side), and the
checkpoint filter saved nothing. Both are fixed in `_p820_llava_sites.py` now -- the measurement hooks `lm_head`
for the final hidden state, excludes image tokens from the text side, computes the canonical DG*/CG, and saves the
trainable tensors -- so the Qwen runner is regenerated from it rather than patched separately.

Differences that must be replaced for Qwen, each asserted:

1. model class `LlavaForConditionalGeneration` -> `Qwen2_5_VLForConditionalGeneration` (2 load sites + import);
2. prompt: Qwen needs its own chat template, the LLaVA `USER: <image> ...` string is not accepted;
3. image token id: Qwen exposes `image_token_id` (151655), not `image_token_index` -- the old fallback of 32000
   exists nowhere in Qwen's vocabulary, so label masking and the pooled vision side would both be wrong;
4. tower classifier: Qwen names its towers `model.visual.blocks.*` (vision), `model.visual.merger.*` (projector)
   and `model.language_model.*` (text).

    python tools/_p1134_make_qwen_runner2.py [--apply]
"""
from __future__ import annotations

import argparse
import ast
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "tools" / "_p820_llava_sites.py"
DST = REPO / "tools" / "_p1135_qwen_sites.py"
PY = r"D:\Anaconda\envs\pytorch\python.exe"

MODEL_DEFAULT = "Qwen/Qwen2.5-VL-7B-Instruct"

REPL = [
    # 1. import
    ("from transformers import AutoProcessor, BitsAndBytesConfig, LlavaForConditionalGeneration",
     "from transformers import (AutoProcessor, BitsAndBytesConfig,\n"
     "                          Qwen2_5_VLForConditionalGeneration)"),
    # 2. the two load sites
    ("    model = LlavaForConditionalGeneration.from_pretrained(",
     "    model = Qwen2_5_VLForConditionalGeneration.from_pretrained("),
    ("        m = LlavaForConditionalGeneration.from_pretrained(",
     "        m = Qwen2_5_VLForConditionalGeneration.from_pretrained("),
    # 3. prompt -> chat template
    ('        pre = "USER: <image>\\nDescribe this image in detail.\\nASSISTANT: "\n'
     '        prompts = [pre + ((captions[k] if captions else by_img[i][0]) if with_labels else "")\n'
     '                   for k, i in enumerate(batch_ids)]\n',
     '        _instr = "Describe this image in detail."\n'
     '        _caps = [(captions[k] if captions else by_img[i][0]) if with_labels else ""\n'
     '                 for k, i in enumerate(batch_ids)]\n'
     '        prompts = []\n'
     '        for _cap in _caps:\n'
     '            _msgs = [{"role": "user", "content": [{"type": "image"},\n'
     '                                                 {"type": "text", "text": _instr}]}]\n'
     '            if with_labels:\n'
     '                _msgs.append({"role": "assistant", "content": [{"type": "text", "text": _cap}]})\n'
     '            prompts.append(proc.apply_chat_template(_msgs, tokenize=False,\n'
     '                                                    add_generation_prompt=not with_labels))\n'),
    # 4. image token id -- label masking inside make_batch
    ('            img_id = int(getattr(model.config, "image_token_index", 32000))',
     '            # Qwen exposes image_token_id (151655); image_token_index does not exist and 32000 is not in\n'
     '            # its vocabulary, so the default would silently mis-mask.\n'
     '            img_id = int(getattr(model.config, "image_token_id", None)\n'
     '                         or getattr(model.config, "image_token_index", 151655))'),
    # 5. image token id -- inside _sides
    ('        img_id = int(getattr(getattr(mm, "config", None), "image_token_index", 32000))',
     '        img_id = int(getattr(getattr(mm, "config", None), "image_token_id", None)\n'
     '                     or getattr(getattr(mm, "config", None), "image_token_index", 151655))'),
    # 6. tower classifier
    ('    if "vision_tower" in name or "vision_model" in name:\n'
     '        return "vision"\n'
     '    if "multi_modal_projector" in name:\n'
     '        return "projector"\n'
     '    if "language_model" in name:\n'
     '        return "text"\n'
     '    return "other"\n',
     '    if "vision_tower" in name or "vision_model" in name:\n'
     '        return "vision"\n'
     '    if "multi_modal_projector" in name:\n'
     '        return "projector"\n'
     '    if "language_model" in name:\n'
     '        return "text"\n'
     '    # Qwen2.5-VL: projector nested inside the vision prefix, so it is matched first\n'
     '    if "visual.merger" in name:\n'
     '        return "projector"\n'
     '    if "visual." in name:\n'
     '        return "vision"\n'
     '    return "other"\n'),
    # 7. defaults that must not point at LLaVA
    ('MODEL = "llava-hf/llava-1.5-7b-hf"', f'MODEL = "{MODEL_DEFAULT}"'),
    ('OUT_DIR = REPO / "outputs" / "llava_sites"', 'OUT_DIR = REPO / "outputs" / "qwen_sites"'),
    ('    print(f"  loading {MODEL} in 4-bit nf4 ...")', '    print(f"  loading {MODEL} ...")'),
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    src = SRC.read_text(encoding="utf-8")
    assert "output_hidden_states=True" in src or "register_forward_pre_hook" in src
    assert "Qwen" not in src.replace("Qwen2-VL", ""), "source should be the LLaVA sweep"

    t = src
    applied = []
    for old, new in REPL:
        n = t.count(old)
        assert n == 1, f"expected exactly one occurrence, found {n}:\n{old[:90]}"
        t = t.replace(old, new, 1)
        applied.append(old.strip().splitlines()[0][:70])

    ast.parse(t)
    print(f"  {len(applied)} replacements applied:")
    for x in applied:
        print(f"    {x}")
    print(f"  output: {DST.name} ({len(t.splitlines())} lines)")

    # the LLaVA sweep must remain untouched
    after = SRC.read_text(encoding="utf-8")
    assert after == src, "the LLaVA sweep was modified"
    print("  the LLaVA sweep is unchanged")

    if not a.apply:
        print("  (dry run)")
        return 0
    DST.write_text(t, encoding="utf-8", newline="")
    r = subprocess.run([PY, "-c", "import ast,io;ast.parse(io.open(r'" + str(DST)
                        + "',encoding='utf-8').read());print('local parse ok')"], capture_output=True)
    print("  " + r.stdout.decode("utf-8", "replace").strip())
    if r.returncode != 0:
        print(r.stderr.decode("utf-8", "replace"))
        return 1
    check = DST.read_text(encoding="utf-8")
    for needle in ("Qwen2_5_VLForConditionalGeneration", "apply_chat_template", "image_token_id",
                   "visual.merger", "register_forward_pre_hook", "_trainable_names", "dg_star = float("):
        print(f"    {needle:<36} {needle in check}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
