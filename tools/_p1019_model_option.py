# -*- coding: utf-8 -*-
r"""Let the sweep target any vision-language model, so Qwen can be run with the same method.

The script hard-codes `MODEL = "llava-hf/llava-1.5-7b-hf"` and one prompt. The operator now wants a Qwen
model tried as well ("跑完之后qwen新模型也试试看"), and the scientific value is in running **the same
experiment** on a second architecture, so the pieces that differ are taken from the model's own processor
rather than hard-coded:

* `--model` selects the checkpoint;
* the ready-made chat prompt is built with the processor's own `apply_chat_template` when it has one,
  because Qwen2-VL style models do not accept the LLaVA `USER: <image> ... ASSISTANT:` string;
* the code that masks the prompt from the loss locates the image tokens by trying, in order: the configured
  `image_token_id`, then `image_token_index`, then the token that appears 576 times in a row (the ViT patch
  count). LLaVA's magic id 32000 is kept as the last fallback so the existing behaviour is unchanged.

    python tools/_p1019_model_option.py [--apply]
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

# 1. the argument
ARG_ANCHOR = '    ap.add_argument("--tf32", action="store_true",\n'
ARG_NEW = ('    ap.add_argument("--model", type=str, default="",\n'
           '                    help="checkpoint to run; default is the LLaVA used for the published numbers")\n')
# 2. let the constant be overridden right after parsing
PARSE_ANCHOR = "    a = ap.parse_args()\n"
PARSE_NEW = ('    global MODEL\n'
             '    if a.model:\n'
             '        MODEL = a.model\n')

# 3. build the prompt from the processor when it can
PROMPT_OLD = ('        pre = "USER: <image>\\nDescribe this image in detail.\\nASSISTANT: "\n'
              '        prompts = [pre + ((captions[k] if captions else by_img[i][0]) if with_labels else "")\n'
              '                   for k, i in enumerate(batch_ids)]\n')

PROMPT_NEW = '''        pre = "USER: <image>\\nDescribe this image in detail.\\nASSISTANT: "
        caps = [(captions[k] if captions else by_img[i][0]) if with_labels else "" for k, i in enumerate(batch_ids)]
        prompts = []
        for cap in caps:
            text = pre + cap
            # Qwen2-VL style models reject the LLaVA prompt string, so the model's own chat template is
            # used when it has one; the caption is still the assistant turn, so the supervision span works
            # out the same way.
            try:
                msgs = [{"role": "user", "content": [{"type": "image"},
                                                     {"type": "text", "text": PROMPT_INSTRUCTION}]},
                        {"role": "assistant", "content": [{"type": "text", "text": cap}]}]
                text = proc.apply_chat_template(msgs, tokenize=False, add_generation_prompt=False)
                if not with_labels:
                    msgs = msgs[:1]
                    text = proc.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
            except Exception:
                pass  # LLaVA's processor has no chat template: keep the prompt string
            prompts.append(text)
'''
PROMPT_INSTRUCTION = "Describe this image in detail."

# 4. locate the image tokens generically
IMGOLD_1 = ("            img_id = int(getattr(model.config, \"image_token_index\", 32000))\n"
            "            for b in range(labels.shape[0]):\n"
            "                row = out[\"input_ids\"][b]\n"
            "                img_pos = (row == img_id).nonzero(as_tuple=True)[0]\n")
IMGOLD_2 = ("            img_id = int(getattr(base.config, \"image_token_index\", 32000))\n")

IMG_NEW = '''            # Locate the image tokens without assuming LLaVA's magic id: try the configured
            # image_token_id, then image_token_index, then the token repeated 576 times (the ViT patch
            # count), and fall back to 32000 as before.
            img_id = None
            for attr in ("image_token_id", "image_token_index"):
                val = getattr(model.config, "image_token_id", None) if attr == "image_token_id" \\
                    else getattr(model.config, "image_token_index", None)
                if isinstance(val, int) and val >= 0:
                    img_id = val
                    break
            if img_id is None:
                import collections as _c
                row0 = out["input_ids"][0].tolist()
                common = _c.Counter(row0).most_common(3)
                for tok, cnt in common:
                    if cnt >= 500:
                        img_id = tok
                        break
            if img_id is None:
                img_id = 32000
'''

IMG_NEW_2 = '''            img_id = None
            for val in (getattr(base.config, "image_token_id", None),
                        getattr(base.config, "image_token_index", None)):
                if isinstance(val, int) and val >= 0:
                    img_id = val
                    break
            if img_id is None:
                img_id = 32000
'''


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    t = SCRIPT.read_text(encoding="utf-8")
    if "--model" in t and "apply_chat_template" in t:
        print("  already patched")
        return 0

    if ARG_ANCHOR in t and '"--model"' not in t:
        t = t.replace(ARG_ANCHOR, ARG_NEW + ARG_ANCHOR, 1)
        print("  added --model")
    if PARSE_ANCHOR in t and "global MODEL" not in t:
        t = t.replace(PARSE_ANCHOR, PARSE_ANCHOR + PARSE_NEW, 1)
        print("  --model overrides MODEL after parsing")
    if PROMPT_OLD in t:
        t = t.replace(PROMPT_OLD, PROMPT_NEW.replace("PROMPT_INSTRUCTION", repr(PROMPT_INSTRUCTION)), 1)
        print("  prompts now come from the processor's chat template when available")
    else:
        print("  WARN: the prompt block was not found verbatim")
    n = 0
    if IMGOLD_1 in t:
        t = t.replace(IMGOLD_1, IMG_NEW + "            for b in range(labels.shape[0]):\n"
                                       "                row = out[\"input_ids\"][b]\n"
                                       "                img_pos = (row == img_id).nonzero(as_tuple=True)[0]\n", 1)
        n += 1
    if IMGOLD_2 in t:
        t = t.replace(IMGOLD_2, IMG_NEW_2, 1)
        n += 1
    print(f"  image-token detection made generic at {n} site(s)")

    ast.parse(t)
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
