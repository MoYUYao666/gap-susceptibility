# -*- coding: utf-8 -*-
r"""List the Qwen2.5-VL parameter names, grouped by first components, so the tower split can be fixed.

The smoke run loaded Qwen successfully (8,292,166,656 parameters) but the tower check failed:

    backbone parameter tensors by tower: {'other': 391, 'text': 338}
    !! the tower split did not find both towers

`tower_of()` in the sweep classifies names by LLaVA's conventions (`vision_tower`, `language_model`, ...), so
with Qwen's naming every vision tensor lands in "other". Training the wrong tensors for `vision_only` and
`both` would silently invalidate those arms, so the real names are printed before anything is run.

    python tools/_p1038_qwen_param_names.py [--apply]
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
import collections, torch
from transformers import AutoConfig, Qwen2_5_VLForConditionalGeneration
cfg = AutoConfig.from_pretrained("Qwen/Qwen2.5-VL-7B-Instruct")
m = Qwen2_5_VLForConditionalGeneration.from_pretrained("Qwen/Qwen2.5-VL-7B-Instruct",
                                                      torch_dtype=torch.bfloat16,
                                                      device_map={"": 0}, low_cpu_mem_usage=True)
prefix2 = collections.Counter()
prefix3 = collections.Counter()
for n, _ in m.named_parameters():
    parts = n.split(".")
    prefix2[".".join(parts[:2])] += 1
    prefix3[".".join(parts[:3])] += 1
print("=== top-2-level groups (count of tensors) ===")
for k, v in prefix2.most_common(20):
    print("  %-52s %d" % (k, v))
print("=== top-3-level groups ===")
for k, v in prefix3.most_common(24):
    print("  %-58s %d" % (k, v))
print("=== examples containing vision or visual ===")
for n, p in m.named_parameters():
    low = n.lower()
    if "visual" in low or "vision" in low:
        print("  %-72s %s" % (n, tuple(p.shape)))
        if n.count(".") > 3:
            pass
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
    out = (o.read().decode("utf-8", "replace") + e.read().decode("utf-8", "replace")).strip()
    lines = out.splitlines()
    shown = 0
    for line in lines:
        if "visual" in line.lower() and shown > 60:
            break
        print(line)
        shown += 1
    cli.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
