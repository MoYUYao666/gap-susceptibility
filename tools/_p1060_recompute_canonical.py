# -*- coding: utf-8 -*-
r"""Recompute DG* and CG for the archived LLaVA runs under the canonical definition.

Why this exists: the archived LLaVA records were produced with a gap definition written inside
`tools/_p820_llava_sites.py` -- mean cross-modal distance minus the two within-modality distances -- whereas
the paper and the ODE use `src/dg_star_tracker.py:compute`:

    DG* = mean_i || I_i - T_i ||^2      (paired, squared, after L2 normalisation)
    CG  = || mean_i I_i - mean_i T_i ||
    DG_empirical = sqrt( CG^2 + || sigma_I - sigma_T ||^2 )

and the embedding extraction follows `tools/_p47_qwen_train.py`: the last hidden state, mean-pooled over the
non-padding positions for the text side and over the image-token positions for the vision side.

No training happens here. The LoRA adapters are already saved (`outputs/llava_bf16_sites_cloud/*.pt`), so each
arm is one load plus one forward pass over the held-out pairs. The first thing to establish is whether the
frozen arm is stable under this definition: if it moves as much as the arms being compared, the quantity cannot
resolve anything on this model and the recomputation stops there.

    python tools/_p1060_recompute_canonical.py --url <ssh> --arms frozen [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import os
import sys
from pathlib import Path

import paramiko

REPO = Path(__file__).resolve().parents[1]
HOST = os.environ.get("P3SSH_HOST", "")
PORT = int(os.environ.get("P3SSH_PORT", "22"))
PASS = os.environ.get("P3SSH_PASS", "")

REMOTE_SCRIPT = r'''#!/usr/bin/env bash
# Recompute DG*/CG under the canonical definition from the saved LoRA adapters. Forward passes only.
set -uo pipefail
cd /root/p3
export PYTHONIOENCODING=utf-8
export HF_HOME=/root/autodl-tmp/hf
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export PYTORCH_ALLOC_CONF=expandable_segments:True
PY=/root/miniconda3/bin/python
ROOT=/root/p3/coco_eval
ARMS="${ARMS:-frozen}"
EVAL_PAIRS="${EVAL_PAIRS:-500}"

echo "=== device ==="
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader

$PY - "$ARMS" "$EVAL_PAIRS" "$ROOT" <<'PYEOF'
import json, sys, io
from pathlib import Path
import torch
import torch.nn.functional as F
from PIL import Image
from transformers import LlavaForConditionalGeneration, AutoProcessor
from peft import PeftModel

arms = [a for a in sys.argv[1].split(",") if a]
eval_pairs = int(sys.argv[2])
root = Path(sys.argv[3])
MODEL = "llava-hf/llava-1.5-7b-hf"
ADAPTERS = Path("/root/p3/adapters")

ann = json.loads((root / "annotations" / "captions_val2014.json").read_text(encoding="utf-8"))
by_img = {}
for c in ann["annotations"]:
    by_img.setdefault(c["image_id"], []).append(c["caption"])
ids = [i for i in by_img if (root / "val2014" / ("COCO_val2014_%012d.jpg" % i)).exists()]
held = ids[:eval_pairs]
print("  held-out pairs:", len(held), flush=True)

proc = AutoProcessor.from_pretrained(MODEL)
proc.tokenizer.padding_side = "right"
IMG_ID = 32000


def embed(model, batch_ids):
    """Canonical extraction: last hidden state -> mean pool per side -> L2 normalise."""
    ims = [Image.open(root / "val2014" / ("COCO_val2014_%012d.jpg" % i)).convert("RGB") for i in batch_ids]
    pre = "USER: <image>\nDescribe this image in detail.\nASSISTANT: "
    inp = proc(images=ims, text=[pre] * len(ims), return_tensors="pt", padding=True,
               truncation=True, max_length=2048)
    if inp["pixel_values"].dtype == torch.uint8:
        inp["pixel_values"] = inp["pixel_values"].to(torch.float32) / 255.0
    inp["pixel_values"] = inp["pixel_values"].to(torch.bfloat16)
    inp = {k: (v.to(0) if hasattr(v, "to") else v) for k, v in inp.items()}
    with torch.no_grad():
        out = model(**inp, output_hidden_states=True)
    hid = out.hidden_states[-1]                                  # (B, L, D)
    mask = inp["attention_mask"].unsqueeze(-1).to(hid.dtype)
    T = (hid * mask).sum(1) / mask.sum(1).clamp(min=1)           # text side: all real positions
    tok = inp["input_ids"]
    vm = (tok == IMG_ID).unsqueeze(-1).to(hid.dtype)
    n = vm.sum(1)
    I = (hid * vm).sum(1) / n.clamp(min=1) if float(n.min()) > 0 else T
    return F.normalize(I.float(), p=2, dim=-1), F.normalize(T.float(), p=2, dim=-1)


def canonical(I, T):
    """src/dg_star_tracker.py:compute, verbatim in structure."""
    dg_star = ((I - T) ** 2).sum(dim=-1).mean().item()
    mu_i, mu_t = I.mean(0), T.mean(0)
    cg = (mu_i - mu_t).norm(p=2).item()
    var_term = (I.std(dim=0) - T.std(dim=0)).norm(p=2).item() ** 2
    dg_emp = (cg ** 2 + var_term) ** 0.5
    return dg_star, cg, dg_emp


results = {}
for arm in arms:
    print(f"\n=== {arm} ===", flush=True)
    model = LlavaForConditionalGeneration.from_pretrained(
        MODEL, torch_dtype=torch.bfloat16, device_map={"": 0}, low_cpu_mem_usage=True)
    if arm != "frozen":
        ck = ADAPTERS / f"{arm}_ckpt.pt"
        if not ck.exists():
            print(f"  !! adapter {ck} missing; skipping", flush=True)
            del model
            torch.cuda.empty_cache()
            continue
        payload = torch.load(ck, map_location="cpu")
        sd = payload["model"] if isinstance(payload, dict) and "model" in payload else payload
        missing, unexpected = model.load_state_dict(sd, strict=False)
        print(f"  loaded {len(sd)} tensors from {ck.name}; "
              f"missing {len(missing)}, unexpected {len(unexpected)}", flush=True)
        if unexpected:
            print(f"  !! unexpected keys, e.g. {list(unexpected)[:3]}", flush=True)
    model.eval()

    dgs, cgs, emps = [], [], []
    for s in range(0, len(held), 32):
        I, T = embed(model, held[s:s + 32])
        d, c, e = canonical(I, T)
        dgs.append(d); cgs.append(c); emps.append(e)
    rec = {"arm": arm, "n": len(held),
           "dg_star": sum(dgs) / len(dgs), "cg": sum(cgs) / len(cgs), "dg_empirical": sum(emps) / len(emps),
           "batches": len(dgs), "dg_star_first_batch": dgs[0], "dg_star_last_batch": dgs[-1]}
    print("  canonical DG* %.6f  CG %.6f  DG_emp %.6f" % (rec["dg_star"], rec["cg"], rec["dg_empirical"]), flush=True)
    print("  batch spread: first %.6f last %.6f (max-min %.6f)" % (
        dgs[0], dgs[-1], max(dgs) - min(dgs)), flush=True)
    results[arm] = rec
    del model
    torch.cuda.empty_cache()

out = Path("/root/p3/outputs/canonical_recompute.json")
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8")
print("\n  wrote", out)
PYEOF
echo CANONICAL_DONE
'''


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--arms", default="frozen")
    ap.add_argument("--eval-pairs", type=int, default=500)
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
    sftp = cli.open_sftp()
    with sftp.open("/root/p3/_p1060_canonical.sh", "w") as fh:
        fh.write(REMOTE_SCRIPT)
    sftp.close()
    cmd = (f"cd /root/p3 && chmod +x _p1060_canonical.sh && "
           f"ARMS={a.arms} EVAL_PAIRS={a.eval_pairs} bash _p1060_canonical.sh 2>&1 | tail -40")
    _i, o, e = cli.exec_command(cmd, timeout=1800)
    print((o.read().decode("utf-8", "replace") + e.read().decode("utf-8", "replace")).strip())
    cli.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
