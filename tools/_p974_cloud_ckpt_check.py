# -*- coding: utf-8 -*-
r"""Check gradient checkpointing the way the sweep actually builds the model.

The first probe called `from_pretrained` directly, without the LoRA wrapping or
`prepare_model_for_kbit_training`, so its `is_gradient_checkpointing: False` described a different model
than the one trained. This probe follows the sweep's own path: load with the 4-bit config, then
`prepare_model_for_kbit_training(use_gradient_checkpointing=True)` plus `get_peft_model`, which is what
`build(arm)` does. If checkpointing is on there, the cloud is configured like the local run and the 48x
speed difference is hardware only.

    python tools/_p974_cloud_ckpt_check.py
"""
from __future__ import annotations

import os
import sys

import paramiko

HOST = os.environ.get("P3SSH_HOST", "")
PORT = int(os.environ.get("P3SSH_PORT", "22"))
PASS = os.environ.get("P3SSH_PASS", "")

PROBE = r""" /root/miniconda3/bin/python - <<'PYEOF'
import os
os.environ["HF_HOME"] = "/root/autodl-tmp/hf"
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
import torch
from transformers import AutoProcessor, BitsAndBytesConfig, LlavaForConditionalGeneration
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training

MODEL = "llava-hf/llava-1.5-7b-hf"
quant = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                           bnb_4bit_compute_dtype=torch.bfloat16, bnb_4bit_use_double_quant=True)
m = LlavaForConditionalGeneration.from_pretrained(
    MODEL, quantization_config=quant, torch_dtype=torch.bfloat16, device_map={"": 0},
    low_cpu_mem_usage=True)
print("plain from_pretrained is_gradient_checkpointing:", getattr(m, "is_gradient_checkpointing", None))

# this is what the sweep's build(arm) does for a non-frozen arm
m = prepare_model_for_kbit_training(m, use_gradient_checkpointing=True)
print("after prepare_model_for_kbit_training        :", getattr(m, "is_gradient_checkpointing", None))
inner = getattr(m, "model", m)
lm = getattr(inner, "language_model", None)
print("language_model is_gradient_checkpointing     :", getattr(lm, "is_gradient_checkpointing", None))
print("gpu memory allocated GB                      : %.1f" % (torch.cuda.memory_allocated() / 1e9))
cfg = LoraConfig(r=8, lora_alpha=16.0, lora_dropout=0.0, bias="none", task_type="CAUSAL_LM",
                 target_modules=["q_proj", "v_proj"])
m = get_peft_model(m, cfg)
print("after get_peft_model is_gradient_checkpointing:", getattr(m, "is_gradient_checkpointing", None))
print("trainable params                             :", sum(p.numel() for p in m.parameters() if p.requires_grad))
PYEOF"""


def main() -> int:
    if not (HOST and PASS):
        print("  P3SSH_HOST / P3SSH_PASS are not set")
        return 2
    cli = paramiko.SSHClient()
    cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    cli.connect(HOST, port=PORT, username="root", password=PASS, timeout=30,
                allow_agent=False, look_for_keys=False)
    _i, o, e = cli.exec_command(PROBE, timeout=900)
    text = (o.read().decode("utf-8", "replace") + e.read().decode("utf-8", "replace")).strip()
    for line in text.splitlines():
        if any(k in line for k in ("gradient_checkpointing", "memory allocated", "trainable",
                                   "Error", "Traceback", "RuntimeError")):
            print("   ", line[:150])
    cli.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
