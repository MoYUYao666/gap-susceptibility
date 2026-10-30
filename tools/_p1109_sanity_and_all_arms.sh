#!/usr/bin/env bash
# Sanity-check the two extraction choices before trusting the numbers, and run all four arms.
#
# The frozen arm gives DG* = 0.000428 while the Qwen batch (which used the same canonical formula) sits at
# 0.2-2.2, three orders of magnitude larger. Two candidate explanations, both testable:
#   1. the vision side is pooling the wrong positions -- LLaVA 1.5 uses image token id 32000, but transforms 5.x
#      may place a different id in the sequence;
#   2. LLaVA's projected visual features really are nearly identical to the language model's token embeddings at
#      those positions, which would make DG* small for a trivial reason (both sides read the same tensor).
# This prints the token composition of one batch and the two sides' magnitudes, then runs all four arms.
set -uo pipefail
cd /root/p3
export PYTHONIOENCODING=utf-8
export HF_HOME=/root/autodl-tmp/hf
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
PY=/root/miniconda3/bin/python
MODEL=/root/autodl-tmp/hf/hub/models--llava-hf--llava-1.5-7b-hf/snapshots/main

echo "=== where was the device left? ==="
nvidia-smi --query-gpu=memory.used --format=csv,noheader

echo "=== token composition and side magnitudes for one batch ==="
$PY - <<'PYEOF'
import json
from collections import Counter
from pathlib import Path
import torch, torch.nn.functional as F
from PIL import Image
from transformers import AutoProcessor, LlavaForConditionalGeneration

ROOT = Path("/root/p3/coco_eval")
MODEL = "/root/autodl-tmp/hf/hub/models--llava-hf--llava-1.5-7b-hf/snapshots/main"
ann = json.loads((ROOT / "annotations" / "captions_val2014.json").read_text(encoding="utf-8"))
by = {}
for c in ann["annotations"]:
    by.setdefault(c["image_id"], []).append(c["caption"])
ids = [i for i in by if (ROOT / "val2014" / ("COCO_val2014_%012d.jpg" % i)).exists()][:4]

proc = AutoProcessor.from_pretrained(MODEL)
proc.tokenizer.padding_side = "right"
model = LlavaForConditionalGeneration.from_pretrained(MODEL, torch_dtype=torch.bfloat16,
                                                     device_map={"": 0}, low_cpu_mem_usage=True).eval()
print("  config.image_token_index:", getattr(model.config, "image_token_index", None))

ims = [Image.open(ROOT / "val2014" / ("COCO_val2014_%012d.jpg" % i)).convert("RGB") for i in ids]
pre = "USER: <image>\nDescribe this image in detail.\nASSISTANT: "
inp = proc(images=ims, text=[pre] * len(ims), return_tensors="pt", padding=True, truncation=True, max_length=2048)
if inp["pixel_values"].dtype == torch.uint8:
    inp["pixel_values"] = inp["pixel_values"].to(torch.float32) / 255.0
inp["pixel_values"] = inp["pixel_values"].to(torch.bfloat16)
inp = {k: (v.to(0) if hasattr(v, "to") else v) for k, v in inp.items()}

row = inp["input_ids"][0].tolist()
cnt = Counter(row)
print("  sequence length:", len(row))
print("  most frequent tokens:", cnt.most_common(4))
print("  count of image_token_index:", row.count(getattr(model.config, "image_token_index", 32000)))
print("  vocab size:", getattr(model.config, "vocab_size", None))

with torch.no_grad():
    out = model(**inp, output_hidden_states=True)
hid = out.hidden_states[-1]
print("  hidden shape:", tuple(hid.shape), "dtype", hid.dtype)

IMG = getattr(model.config, "image_token_index", 32000)
vm = (inp["input_ids"] == IMG).unsqueeze(-1).to(hid.dtype)
n = vm.sum(1)
I = (hid * vm).sum(1) / n.clamp(min=1)
mask = inp["attention_mask"].unsqueeze(-1).to(hid.dtype)
T = (hid * mask).sum(1) / mask.sum(1).clamp(min=1)
print("  image-token count per row:", n.tolist())
print("  ||I|| raw:", [round(float(x), 3) for x in I.norm(dim=-1)])
print("  ||T|| raw:", [round(float(x), 3) for x in T.norm(dim=-1)])
print("  cos(I,T) per pair:", [round(float(x), 5) for x in F.cosine_similarity(I.float(), T.float(), dim=-1)])
print("  ||I-T||^2 per pair:", [round(float(x), 8) for x in ((F.normalize(I.float(), dim=-1) - F.normalize(T.float(), dim=-1)) ** 2).sum(-1)])

# which positions does the text side actually average over? compare with excluding image tokens
mask_txt = inp["attention_mask"].bool() & (inp["input_ids"] != IMG)
T2 = (hid * mask_txt.unsqueeze(-1).to(hid.dtype)).sum(1) / mask_txt.sum(1, keepdim=True).clamp(min=1).to(hid.dtype)
print("  ||T_excluding_image - T_all||:", [round(float(x), 5) for x in (T2.float() - T.float()).norm(dim=-1)])
del model
PYEOF

echo
echo "=== all four arms ==="
for arm in frozen text_only vision_only both; do
  echo "--- $arm ---"
  ARMS=$arm EVAL_PAIRS=500 bash _p1107_canonical.sh 2>&1 | grep -aE "canonical DG|batch spread|held-out|loaded|Traceback|Error" | head -5
done
echo ALL_ARMS_DONE
