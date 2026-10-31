# -*- coding: utf-8 -*-
r"""Run the canonical DG*/CG recomputation for the frozen arm on the host.

This is the check that decides everything: if the frozen arm (which trains nothing) moves the canonical metric
as much as the trained arms move it, the quantity cannot resolve anything on this model and the work stops with
an honest report rather than four arms of noise.

The script is written to the host and run there; it loads the base weights from the local mirror cache (no
network), applies each arm's saved adapter when asked, and prints the canonical numbers with the batch spread so
stability is visible rather than asserted.

    python tools/_p1107_run_canonical.py --arms frozen [--apply]
"""
from __future__ import annotations

import argparse
import os
import sys
import time

import paramiko

HOST = os.environ.get("P3SSH_HOST", "")
PORT = int(os.environ.get("P3SSH_PORT", "22"))
PASS = os.environ.get("P3SSH_PASS", "")

BODY = r'''#!/usr/bin/env bash
# Recompute DG*/CG under src/dg_star_tracker.py's definition, forward passes only.
set -uo pipefail
cd /root/p3
export PYTHONIOENCODING=utf-8
export HF_HOME=/root/autodl-tmp/hf
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export PYTORCH_ALLOC_CONF=expandable_segments:True
PY=/root/miniconda3/bin/python
ARMS="${ARMS:-frozen}"
EVAL_PAIRS="${EVAL_PAIRS:-500}"

echo "=== device ==="
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader

$PY - "$ARMS" "$EVAL_PAIRS" <<'PYEOF'
import json, sys, glob, os
from pathlib import Path
import torch
import torch.nn.functional as F
from PIL import Image
from transformers import AutoProcessor, LlavaForConditionalGeneration

arms = [a for a in sys.argv[1].split(",") if a]
eval_pairs = int(sys.argv[2])
ROOT = Path("/root/p3/coco_eval")
MODEL = "/root/autodl-tmp/hf/hub/models--llava-hf--llava-1.5-7b-hf/snapshots/main"
ADAPTERS = Path("/root/p3/adapters")

# the snapshot dir holds symlinks into ../../blobs; resolve to real files if needed
if not (Path(MODEL) / "model.safetensors.index.json").exists():
    alt = Path("/root/autodl-tmp/hf/hub/models--llava-hf--llava-1.5-7b-hf/blobs")
    print("  !! index file missing under", MODEL, "| blobs:", sorted(p.name for p in alt.glob("*.safetensors"))[:4])

ann = json.loads((ROOT / "annotations" / "captions_val2014.json").read_text(encoding="utf-8"))
by_img = {}
for c in ann["annotations"]:
    by_img.setdefault(c["image_id"], []).append(c["caption"])
ids = [i for i in by_img if (ROOT / "val2014" / ("COCO_val2014_%012d.jpg" % i)).exists()]
held = ids[:eval_pairs]
print("  held-out pairs:", len(held), flush=True)

proc = AutoProcessor.from_pretrained(MODEL)
proc.tokenizer.padding_side = "right"
IMG_ID = 32000


def embed(model, batch_ids):
    """Canonical extraction: last hidden state -> mean pool per side -> L2 normalise."""
    ims = [Image.open(ROOT / "val2014" / ("COCO_val2014_%012d.jpg" % i)).convert("RGB") for i in batch_ids]
    pre = "USER: <image>\nDescribe this image in detail.\nASSISTANT: "
    inp = proc(images=ims, text=[pre] * len(ims), return_tensors="pt", padding=True,
               truncation=True, max_length=2048)
    if inp["pixel_values"].dtype == torch.uint8:
        inp["pixel_values"] = inp["pixel_values"].to(torch.float32) / 255.0
    inp["pixel_values"] = inp["pixel_values"].to(torch.bfloat16)
    inp = {k: (v.to(0) if hasattr(v, "to") else v) for k, v in inp.items()}
    with torch.no_grad():
        out = model(**inp, output_hidden_states=True)
    hid = out.hidden_states[-1]
    tok = inp["input_ids"]
    # The image tokens must be excluded from the text side. On a LLaVA sequence they are 576 of ~596
    # positions, so averaging over every non-padding position makes T almost the same tensor as I and the
    # metric degenerates into a self-comparison: measured cos(I,T) = 0.9997 and DG* = 4.3e-4, while the
    # difference between including and excluding them has norm 51-56 against raw norms of ~60-70.
    # `tools/_p47_qwen_train.py` masks the vision range out for the same reason.
    mask_txt = inp["attention_mask"].bool() & (tok != IMG_ID)
    m = mask_txt.unsqueeze(-1).to(hid.dtype)
    T = (hid * m).sum(1) / m.sum(1).clamp(min=1)
    vm = (tok == IMG_ID).unsqueeze(-1).to(hid.dtype)
    n = vm.sum(1)
    I = (hid * vm).sum(1) / n.clamp(min=1) if float(n.min()) > 0 else T
    return F.normalize(I.float(), p=2, dim=-1), F.normalize(T.float(), p=2, dim=-1)


def canonical(I, T):
    """src/dg_star_tracker.py:compute, same structure."""
    dg_star = ((I - T) ** 2).sum(dim=-1).mean().item()
    mu_i, mu_t = I.mean(0), T.mean(0)
    cg = (mu_i - mu_t).norm(p=2).item()
    var_term = (I.std(dim=0) - T.std(dim=0)).norm(p=2).item() ** 2
    return dg_star, cg, (cg ** 2 + var_term) ** 0.5


results = {}
for arm in arms:
    print(f"\n=== {arm} ===", flush=True)
    model = LlavaForConditionalGeneration.from_pretrained(
        MODEL, torch_dtype=torch.bfloat16, device_map={"": 0}, low_cpu_mem_usage=True)
    seed_used = None
    if arm != "frozen":
        # files are named <arm>_s<seed>_ckpt.pt and not every arm has every seed (text_only has only s456)
        cands = sorted(ADAPTERS.glob(f"{arm}_s*_ckpt.pt")) or sorted(ADAPTERS.glob(f"{arm}*_ckpt.pt"))
        if not cands:
            print(f"  !! no adapter for {arm} in {ADAPTERS}; skipping", flush=True)
            results[arm] = {"arm": arm, "error": "no adapter"}
            continue
        ck = cands[0]
        seed_used = ck.stem.split("_s")[-1].replace("_ckpt", "") if "_s" in ck.stem else "?"
        payload = torch.load(ck, map_location="cpu")
        sd = payload["model"] if isinstance(payload, dict) and "model" in payload else payload
        missing, unexpected = model.load_state_dict(sd, strict=False)
        print(f"  adapter {ck.name} (seed {seed_used}): {len(sd)} tensors; "
              f"missing {len(missing)}, unexpected {len(unexpected)}", flush=True)
        if unexpected:
            print("  !! unexpected keys:", list(unexpected)[:3], flush=True)
    model.eval()

    dgs, cgs, emps = [], [], []
    for s in range(0, len(held), 32):
        I, T = embed(model, held[s:s + 32])
        d, c, e = canonical(I, T)
        dgs.append(d); cgs.append(c); emps.append(e)
    rec = {"arm": arm, "seed": seed_used, "n": len(held),
           "dg_star": sum(dgs) / len(dgs), "cg": sum(cgs) / len(cgs),
           "dg_empirical": sum(emps) / len(emps), "batches": len(dgs),
           "dg_first": dgs[0], "dg_last": dgs[-1], "dg_min": min(dgs), "dg_max": max(dgs),
           "cg_min": min(cgs), "cg_max": max(cgs)}
    print("  canonical DG* %.6f | CG %.6f | DG_emp %.6f" % (rec["dg_star"], rec["cg"], rec["dg_empirical"]), flush=True)
    print("  batch spread: DG* %.6f..%.6f (range %.6f) | CG %.6f..%.6f" % (
        rec["dg_min"], rec["dg_max"], rec["dg_max"] - rec["dg_min"], rec["cg_min"], rec["cg_max"]), flush=True)
    results[arm] = rec
    del model
    torch.cuda.empty_cache()

out = Path("/root/p3/outputs/canonical_recompute.json")
out.parent.mkdir(parents=True, exist_ok=True)
prev = {}
if out.exists():
    try:
        prev = json.loads(out.read_text(encoding="utf-8"))
    except Exception:
        prev = {}
prev.update(results)
out.write_text(json.dumps(prev, ensure_ascii=False, indent=1), encoding="utf-8")
print("\n  wrote", out)
PYEOF
echo CANONICAL_DONE
'''


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--arms", default="frozen")
    ap.add_argument("--eval-pairs", type=int, default=500)
    ap.add_argument("--wait", type=int, default=0, help="seconds to wait for the download first")
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

    def sh(cmd: str, timeout: int = 600) -> str:
        _i, o, e = cli.exec_command(cmd, timeout=timeout)
        return (o.read().decode("utf-8", "replace") + e.read().decode("utf-8", "replace")).strip()

    sftp = cli.open_sftp()
    with sftp.open("/root/p3/_p1107_canonical.sh", "w") as fh:
        fh.write(BODY)
    sftp.close()
    print("  canonical script uploaded")

    # wait for the weights if asked
    if a.wait:
        deadline = time.time() + a.wait
        while time.time() < deadline:
            tail = sh("tail -1 /root/p3/mirror_mt.log 2>/dev/null | tr -d '\\r'")
            done = sh("grep -c 'OK' /root/p3/mirror_mt.log 2>/dev/null || echo 0")
            print(f"    [{time.strftime('%H:%M')}] {tail[:100]}  ok_files={done}")
            if done.strip() == "3":
                break
            time.sleep(120)

    print("=== index file present? ===")
    print(sh("ls -la /root/autodl-tmp/hf/hub/models--llava-hf--llava-1.5-7b-hf/snapshots/main/ | head -14"))
    print("=== blobs ===")
    print(sh("ls -la /root/autodl-tmp/hf/hub/models--llava-hf--llava-1.5-7b-hf/blobs/ | head -12"))

    print(f"\n=== running canonical recomputation: arms={a.arms} ===")
    cmd = (f"cd /root/p3 && chmod +x _p1107_canonical.sh && "
           f"ARMS={a.arms} EVAL_PAIRS={a.eval_pairs} bash _p1107_canonical.sh 2>&1 | tail -30")
    print(sh(cmd, timeout=2400))
    cli.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
