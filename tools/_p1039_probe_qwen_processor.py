# -*- coding: utf-8 -*-
r"""Inspect what the Qwen processor returns, to drive the measurement correctly.

The measurement path calls the vision tower by hand, which works for LLaVA but not for Qwen2.5-VL:

    TypeError: Qwen2_5_VisionTransformerPretrainedModel.forward() missing 1 required positional argument: 'grid_thw'

Qwen's tower needs the patch-grid shape that its dynamic resolution produces, so a different route is needed:
capture the projected vision features from a full forward pass with a hook on the projector/merger module.
That works for any architecture and needs no manual tower call. This prints the processor's output keys and
the merger's output shape so the replacement can be written to match reality.

    python tools/_p1039_probe_qwen_processor.py [--apply]
"""
from __future__ import annotations

import argparse
import os
import sys

import paramiko

HOST = os.environ.get("P3SSH_HOST", "")
PORT = int(os.environ.get("P3SSH_PORT", "22"))
PASS = os.environ.get("P3SSH_PASS", "")

PROBE = r"""
export HF_HOME=/root/autodl-tmp/hf HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
/root/miniconda3/bin/python - <<'PYEOF'
import torch, json
from pathlib import Path
from PIL import Image
from transformers import AutoProcessor, Qwen2_5_VLForConditionalGeneration

M = "Qwen/Qwen2.5-VL-7B-Instruct"
proc = AutoProcessor.from_pretrained(M)
root = Path("/root/p3/coco_full")
ann = json.loads((root / "annotations" / "captions_val2014.json").read_text(encoding="utf-8", errors="ignore"))
by = {}
for c in ann["annotations"]:
    by.setdefault(c["image_id"], []).append(c["caption"])
ids = [i for i in by if (root / "val2014" / ("COCO_val2014_%012d.jpg" % i)).exists()][:2]
ims = [Image.open(root / "val2014" / ("COCO_val2014_%012d.jpg" % i)).convert("RGB") for i in ids]
prompt = proc.apply_chat_template([{"role": "user", "content": [{"type": "image"},
                                                                {"type": "text", "text": "Describe this image in detail."}]}],
                                  tokenize=False, add_generation_prompt=True)
out = proc(images=ims, text=[prompt] * len(ims), return_tensors="pt", padding=True, truncation=True, max_length=2048)
print("  processor keys:", sorted(out.keys()))
for k, v in out.items():
    print("    %-22s %s" % (k, tuple(v.shape) if hasattr(v, "shape") else type(v).__name__))
print("  input_ids row0 image_token count:",
      int((out["input_ids"][0] == 151655).sum()))

m = Qwen2_5_VLForConditionalGeneration.from_pretrained(M, torch_dtype=torch.bfloat16,
                                                      device_map={"": 0}, low_cpu_mem_usage=True)
inner = m.model
print("  inner type:", type(inner).__name__)
print("  has visual:", hasattr(inner, "visual"), "| visual.merger:", hasattr(inner.visual, "merger"))
captured = {}
def hook(_mod, _inp, outp):
    captured["merger"] = outp
h = inner.visual.merger.register_forward_hook(hook)
inp = {k: (v.to(0) if hasattr(v, "to") else v) for k, v in out.items()}
with torch.no_grad():
    res = m(**inp, output_hidden_states=True)
h.remove()
print("  merger output type:", type(captured.get("merger")).__name__)
mo = captured.get("merger")
if isinstance(mo, tuple):
    print("  merger tuple len:", len(mo), "shapes:", [tuple(x.shape) for x in mo if hasattr(x, "shape")])
else:
    print("  merger shape:", tuple(mo.shape))
hs = res.hidden_states
print("  hidden_states layers:", len(hs), "layer0:", tuple(hs[0].shape), "last:", tuple(hs[-1].shape))
print("  pixel_values dtype after model:", inp["pixel_values"].dtype)
PYEOF
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not a.apply:
        print("  (dry run)")
        return 0
    if not (HOST and PASS):
        print("  P3SSH_HOST / P3SSH_PASS are not set")
        return 2
    cli = paramiko.SSHClient()
    cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    cli.connect(HOST, port=PORT, username="root", password=PASS, timeout=30,
                allow_agent=False, look_for_keys=False)
    _i, o, e = cli.exec_command(PROBE, timeout=900)
    print((o.read().decode("utf-8", "replace") + e.read().decode("utf-8", "replace")).strip())
    cli.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
