# -*- coding: utf-8 -*-
r"""Undo the prompt refactor for LLaVA and make the Qwen path a separate, explicit branch.

Two findings from the smoke run of 2026-10-16:

1. **The prompt refactor changed LLaVA's numbers.** A five-step deterministic run of the patched script
   produced loss 4.3099 where the frozen baseline is 2.9466. The generalisation built the prompt through
   `processor.apply_chat_template(..., add_generation_prompt=False)` even for LLaVA, which does have a chat
   template in transformers 5.16.1, so the prompt stopped being the string the published numbers came from.
   The chat-template route is therefore restricted to models that are not the LLaVA checkpoint, and the
   original prompt string is used exactly as before for LLaVA.

2. **Qwen cannot be loaded through `LlavaForConditionalGeneration`.** With the Qwen checkpoint the loader
   raises `StrictDataclassClassValidationError: The hidden size (1280) is not a multiple of the number of
   attention heads (12)`, because the LLaVA config class is being fed a Qwen vision config. A model-class
   map is added instead: the correct `AutoModelForVision2Seq`-style class is chosen from the config's own
   `model_type`, so each checkpoint is loaded by its own class.

    python tools/_p1030_fix_model_loading.py [--apply]
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


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    t = SCRIPT.read_text(encoding="utf-8")
    if "_load_vlm" in t:
        print("  already patched")
        return 0

    # ---- 1. prompt: use the chat template only for models that need it -------------------------------
    old_prompt = re.search(r"        prompts = \[\]\n(?:.*\n)*?            prompts\.append\(text\)\n", t)
    assert old_prompt, "the prompt block was not found"
    new_prompt = (
        "        prompts = []\n"
        "        # The LLaVA prompt string is what the published numbers came from, so it is kept verbatim\n"
        "        # for that checkpoint. A five-step regression run on 2026-10-16 showed loss 4.3099 against\n"
        "        # the 2.9466 baseline when this path used the processor's chat template for LLaVA too, so the\n"
        "        # template is applied only to models that are not the LLaVA checkpoint.\n"
        "        _use_template = \"llava\" not in MODEL.lower()\n"
        "        for cap in caps:\n"
        "            text = pre + cap\n"
        "            if _use_template:\n"
        "                try:\n"
        "                    msgs = [{\"role\": \"user\", \"content\": [{\"type\": \"image\"},\n"
        "                                                         {\"type\": \"text\", \"text\": PROMPT_INSTRUCTION}]},\n"
        "                            {\"role\": \"assistant\", \"content\": [{\"type\": \"text\", \"text\": cap}]}]\n"
        "                    text = proc.apply_chat_template(msgs, tokenize=False, add_generation_prompt=False)\n"
        "                    if not with_labels:\n"
        "                        text = proc.apply_chat_template(msgs[:1], tokenize=False,\n"
        "                                                        add_generation_prompt=True)\n"
        "                except Exception as _exc:\n"
        "                    print(f\"  chat template unavailable ({type(_exc).__name__}); keeping the prompt string\")\n"
        "            prompts.append(text)\n")
    t = t[: old_prompt.start()] + new_prompt + t[old_prompt.end():]

    # make the instruction a module constant next to MODEL
    t = t.replace('MODEL = "llava-hf/llava-1.5-7b-hf"\n',
                  'MODEL = "llava-hf/llava-1.5-7b-hf"\n'
                  'PROMPT_INSTRUCTION = "Describe this image in detail."\n', 1)

    # ---- 2. load each checkpoint with its own class --------------------------------------------------
    helper = '''

def _load_vlm(path, dtype, device_map="cuda:0"):
    """Load a vision-language checkpoint with the class its own config asks for.

    Loading Qwen2.5-VL through `LlavaForConditionalGeneration` fails with
    `The hidden size (1280) is not a multiple of the number of attention heads (12)`, because the LLaVA
    config class is validating a Qwen vision config. The class is therefore chosen from the config's
    `model_type`, with LLaVA kept as the default so the existing runs load exactly as before.
    """
    import transformers as _tf
    from transformers import AutoConfig as _AutoConfig
    cfg = _AutoConfig.from_pretrained(path)
    kind = getattr(cfg, "model_type", "") or ""
    table = {
        "llava": getattr(_tf, "LlavaForConditionalGeneration", None),
        "qwen2_5_vl": getattr(_tf, "Qwen2_5_VLForConditionalGeneration", None),
        "qwen2_vl": getattr(_tf, "Qwen2VLForConditionalGeneration", None),
    }
    cls = table.get(kind)
    if cls is None:
        cls = getattr(_tf, "AutoModelForVision2Seq", None)
        print(f"  model_type={kind!r}: using {cls.__name__}")
    else:
        print(f"  model_type={kind!r}: using {cls.__name__}")
    return cls.from_pretrained(path, torch_dtype=dtype, device_map=device_map,
                               low_cpu_mem_usage=True)
'''
    t = t.replace("\ndef main():", helper + "\n\ndef main():", 1)

    # route both from_pretrained calls through the helper
    old1 = re.search(r"    m = LlavaForConditionalGeneration\.from_pretrained\(\n(?:.*\n)*?    \)\n", t)
    assert old1, "the 4-bit load call was not found"
    t = t[: old1.start()] + '    m = _load_vlm(MODEL, torch.bfloat16)\n' + t[old1.end():]
    old2 = re.search(r"        m = LlavaForConditionalGeneration\.from_pretrained\(\n(?:.*\n)*?        \)\n", t)
    if old2:
        t = t[: old2.start()] + '        m = _load_vlm(MODEL, torch.bfloat16)\n' + t[old2.end():]

    ast.parse(t)
    print("  LLaVA keeps its original prompt string; chat template only for non-LLaVA models")
    print("  checkpoint loading now picks the class from the config's model_type")
    if not a.apply:
        print("  (dry run)")
        return 0
    SCRIPT.write_text(t, encoding="utf-8", newline="")
    r = subprocess.run([PY, "-c", "import ast,io;ast.parse(io.open(r'" + str(SCRIPT)
                        + "',encoding='utf-8').read());print('local parse ok')"], capture_output=True)
    print("  " + r.stdout.decode("utf-8", "replace").strip())
    assert r.returncode == 0, r.stderr.decode("utf-8", "replace")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
