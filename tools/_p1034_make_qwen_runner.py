# -*- coding: utf-8 -*-
r"""Build a Qwen2.5-VL runner from the frozen LLaVA sweep, by mechanical replacement with assertions.

The LLaVA script must stay exactly as it was for the published numbers (`_p820_llava_sites.py` is restored
from the frozen copy and verified byte-identical to the one that produced the twelve records). Qwen needs
three things that differ, and only those are changed here, each with an assertion that the replacement landed:

1. **model class** -- `LlavaForConditionalGeneration` rejects a Qwen config with
   `The hidden size (1280) is not a multiple of the number of attention heads (12)`, so
   `Qwen2_5_VLForConditionalGeneration` is used;
2. **prompt** -- Qwen2.5-VL requires its own chat template; the LLaVA `USER: <image> ... ASSISTANT:` string is
   not accepted by its processor;
3. **image-token location** -- the LLaVA code reads `config.image_token_index`, which Qwen's config does not
   have, so it silently fell back to id 32000 and the label masking would cut nothing. Qwen's config exposes
   `image_token_id`.

The output is a separate file, so the LLaVA path cannot be affected by it.

    python tools/_p1034_make_qwen_runner.py [--apply]
"""
from __future__ import annotations

import argparse
import ast
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "tools" / "_p820_llava_sites.py"
DST = REPO / "tools" / "_p1035_qwen_sites.py"
PY = r"D:\Anaconda\envs\pytorch\python.exe"

# 1. model class, at both load sites, plus the import (the real import line is
#    `from transformers import AutoProcessor, BitsAndBytesConfig, LlavaForConditionalGeneration`)
LOADS = [
    ("    model = LlavaForConditionalGeneration.from_pretrained(\n",
     "    model = Qwen2_5_VLForConditionalGeneration.from_pretrained(\n"),
    ("        m = LlavaForConditionalGeneration.from_pretrained(\n",
     "        m = Qwen2_5_VLForConditionalGeneration.from_pretrained(\n"),
    ("from transformers import AutoProcessor, BitsAndBytesConfig, LlavaForConditionalGeneration",
     "from transformers import (AutoProcessor, BitsAndBytesConfig,\n"
     "                          Qwen2_5_VLForConditionalGeneration)"),
]
# 2. prompt: one site per batch builder
PROMPT_OLD = '        pre = "USER: <image>\\nDescribe this image in detail.\\nASSISTANT: "\n'
PROMPT_NEW = ('        _instr = "Describe this image in detail."\n'
              '        pre = proc.apply_chat_template(\n'
              '            [{"role": "user", "content": [{"type": "image"},\n'
              '                                          {"type": "text", "text": _instr}]}],\n'
              '            tokenize=False, add_generation_prompt=True)\n')
# 3. image token id
IMG_OLD = '            img_id = int(getattr(model.config, "image_token_index", 32000))\n'
IMG_NEW = ('            # Qwen2.5-VL exposes `image_token_id`; there is no `image_token_index`, and the old\n'
           '            # default of 32000 exists nowhere in Qwen vocabulary, which would make the mask a no-op.\n'
           '            img_id = int(getattr(model.config, "image_token_id", None)\n'
           '                         or getattr(model.config, "image_token_index", 151655))\n')

# 4. tower classification. Measured on the host with tools/_p1038: Qwen2.5-VL names its towers
#    `model.visual.blocks.*` (vision), `model.visual.merger.*` (the projector) and
#    `model.language_model.layers.*` (text). The LLaVA names are kept so the classifier stays correct for
#    both, and all three lists (`VIS_NAMES`, `TXT_NAMES`, `PROJ_NAMES`) derive from this function.
TOWER_OLD = ('    if "vision_tower" in name or "vision_model" in name:\n'
             '        return "vision"\n'
             '    if "multi_modal_projector" in name:\n'
             '        return "projector"\n'
             '    if "language_model" in name:\n'
             '        return "text"\n'
             '    return "other"\n')
TOWER_NEW = ('    if "vision_tower" in name or "vision_model" in name:\n'
             '        return "vision"\n'
             '    if "multi_modal_projector" in name:\n'
             '        return "projector"\n'
             '    if "language_model" in name:\n'
             '        return "text"\n'
             '    # Qwen2.5-VL: the projector is nested inside the vision prefix, so it is tested first.\n'
             '    if "visual.merger" in name or "multi_modal_projector" in name:\n'
             '        return "projector"\n'
             '    if "visual." in name:\n'
             '        return "vision"\n'
             '    return "other"\n')


SIDES_OLD = ('        inner = getattr(base, "model", base)\n'
             '        vision = getattr(inner, "vision_tower", None)\n'
             '        projector = getattr(inner, "multi_modal_projector", None)\n'
             '        lm = getattr(inner, "language_model", None)\n'
             '        if vision is None or projector is None or lm is None:\n'
             '            raise RuntimeError(f"could not locate the submodules on {type(inner).__name__}")\n')
SIDES_NEW = ('        # Qwen2.5-VL cannot be measured the LLaVA way: its tower needs the patch grid of its\n'
             '        # dynamic resolution, and calling it with pixel_values alone raises\n'
             '        #   Qwen2_5_VisionTransformerPretrainedModel.forward() missing 1 required positional\n'
             '        #   argument: \'grid_thw\'\n'
             '        # The processor does return that grid (`image_grid_thw`, recorded by tools/_p1039), and a\n'
             '        # hook on `visual.merger` captures the projected vision features: a plain tensor, measured\n'
             '        # (587, 3584) for two COCO images. Both sides therefore come from one full forward pass.\n'
             '        inner = getattr(base, "model", base)\n'
             '        merger = getattr(getattr(inner, "visual", None), "merger", None)\n'
             '        lm = getattr(inner, "language_model", None)\n'
             '        if merger is None or lm is None:\n'
             '            raise RuntimeError(f"could not locate the submodules on {type(inner).__name__}")\n'
             '        # Both sides are captured with hooks so that no per-layer activations are kept: the first\n'
             '        # attempt used output_hidden_states=True, which holds a tensor for all 29 layers and ran\n'
             '        # the device out of memory (31.46 GiB in use, 5.69 MiB free). The text side is the token\n'
             '        # embedding, which a hook on the embedding module gives for the price of one tensor.\n'
             '        _cap = {}\n'
             '\n'
             '        def _hook_merger(_mod, _inp, outp):\n'
             '            _cap["v"] = outp\n'
             '\n'
             '        def _hook_embed(_mod, _inp, outp):\n'
             '            _cap["t"] = outp\n'
             '\n'
             '        _hm = merger.register_forward_hook(_hook_merger)\n'
             '        _he = lm.get_input_embeddings().register_forward_hook(_hook_embed)\n'
             '        try:\n'
             '            with torch.no_grad():\n'
             '                mm(**inp)\n'
             '        finally:\n'
             '            _hm.remove()\n'
             '            _he.remove()\n'
             '        V = _cap["v"]\n'
             '        if isinstance(V, tuple):\n'
             '            V = V[0]\n'
             '        ids = inp["input_ids"]\n'
             '        img_id = int(getattr(base.config, "image_token_id", None)\n'
             '                     or getattr(base.config, "image_token_index", 151655))\n'
             '        mask = inp["attention_mask"].bool() & (ids != img_id)\n'
             '        T = _cap["t"][mask]\n'
             '        return V.reshape(-1, V.shape[-1]), T\n')

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = SRC.read_text(encoding="utf-8")
    assert "apply_chat_template" not in t, "the source is not the frozen LLaVA sweep"

    applied = []
    for old, new in LOADS:
        if old in t:
            n = t.count(old)
            t = t.replace(old, new)
            applied.append(f"model class x{n}")
    assert applied, "no model-class load site was found"
    n_prompt = t.count(PROMPT_OLD)
    assert n_prompt >= 1, "the prompt line was not found"
    t = t.replace(PROMPT_OLD, PROMPT_NEW)
    applied.append(f"prompt x{n_prompt}")
    n_img = t.count(IMG_OLD)
    assert n_img >= 1, "the image-token line was not found"
    t = t.replace(IMG_OLD, IMG_NEW)
    applied.append(f"image token x{n_img}")
    n_tower = t.count(TOWER_OLD)
    assert n_tower == 1, "the tower classifier was not found exactly once"
    t = t.replace(TOWER_OLD, TOWER_NEW, 1)
    applied.append("tower classifier x1")
    # One pair now: the whole `_sides` body is replaced at once, because the Qwen measurement takes both
    # sides from a single forward pass instead of calling the vision tower by hand.
    n = t.count(SIDES_OLD)
    assert n == 1, f"measurement substitution: expected one site, found {n}"
    t = t.replace(SIDES_OLD, SIDES_NEW, 1)
    applied.append("measurement body x1")

    # the runner writes elsewhere so it can never overwrite the LLaVA records
    t = t.replace('OUT_DIR = REPO / "outputs" / "llava_sites"',
                  'OUT_DIR = REPO / "outputs" / "qwen_sites"', 1)
    t = t.replace('print(f"  loading {MODEL} in 4-bit nf4 ...")',
                  'print(f"  loading {MODEL} ...")', 1)
    t = t.replace('MODEL = "llava-hf/llava-1.5-7b-hf"',
                  'MODEL = "Qwen/Qwen2.5-VL-7B-Instruct"', 1)
    t = t.replace('"""', '"""Qwen2.5-VL runner.', 1)

    ast.parse(t)
    print("  replacements:")
    for x in applied:
        print(f"    {x}")
    print(f"  output: {DST.name} ({len(t.splitlines())} lines)")
    if not a.apply:
        print("  (dry run)")
        return 0
    DST.write_text(t, encoding="utf-8", newline="")
    r = subprocess.run([PY, "-c", "import ast,io;ast.parse(io.open(r'" + str(DST)
                        + "',encoding='utf-8').read());print('local parse ok')"], capture_output=True)
    print("  " + r.stdout.decode("utf-8", "replace").strip())
    assert r.returncode == 0, r.stderr.decode("utf-8", "replace")
    src = SRC.read_text(encoding="utf-8")
    assert "apply_chat_template" not in src, "the LLaVA source gained the chat-template path"
    assert "Qwen2_5_VLForConditionalGeneration" not in src, "the LLaVA source gained the Qwen class"
    print("  the LLaVA sweep is unchanged (its one mention of Qwen is the original docstring)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
