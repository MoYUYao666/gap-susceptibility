# -*- coding: utf-8 -*-
r"""方案②（重写）：单模型评测全部逐 epoch 检查点（2026-10-12）。

## 上一版为什么挂

`_p214` 同进程**载入两个 CLIP**（冻结 + LoRA）→ 内存压力下卡死。
**修法**：只载入一次 CLIP，套 LoRA；**`lora_B` 零初始化**（`src/lora.py:56`），
故 **B=0 时前向 == 冻结基座** → 用同一个模型先算冻结基座，再逐检查点覆盖 A/B。

## 协议（与 `tools/a1_h_offset.py` 一致）

- `openai/clip-vit-base-patch32`｜模板 `a photo of a {}`｜legacy1001 类表
- ImageNet 5k（`RandomState(42)`）→ `tau5`（`a1_h_common.per_image_tau`，冻结 top-5）与 `top1_5k`
- Flickr30k val rows 2000–3000 → `CG`
- 每 10 个检查点算一次 CG（省时；其余沿用上次）

    python tools\_p218_eval_all_epochs.py [--apply] [--limit N]
"""
from __future__ import annotations

import argparse
import glob
import io
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))

import numpy as np  # noqa: E402
import torch  # noqa: E402
import torch.nn.functional as F  # noqa: E402
from transformers import CLIPModel, CLIPProcessor  # noqa: E402
from torch.utils.data import DataLoader  # noqa: E402
from datasets import Dataset as HFDataset  # noqa: E402

from a1_h_common import per_image_tau  # noqa: E402
from src.dataset import Flickr30kDataset, _collate_fn  # noqa: E402
from src.lora import apply_lora_to_model  # noqa: E402

MODEL_ID = "openai/clip-vit-base-patch32"
TEMPLATE = "a photo of a {}"
N_SAMPLE = 5000
TOPK = 5
BATCH = 128
CG_EVERY = 10
OUT = REPO / "outputs" / "a1_epoch_sweep.json"


@torch.no_grad()
def enc_images(model, processor, pil_list):
    feats = []
    for i in range(0, len(pil_list), BATCH):
        inp = processor(images=list(pil_list[i:i + BATCH]),
                        return_tensors="pt").to("cuda")
        v = model.vision_model(**inp)
        vp = v[1] if isinstance(v, tuple) else v.pooler_output
        feats.append(F.normalize(model.visual_projection(vp), dim=-1))
    return torch.cat(feats)


@torch.no_grad()
def enc_text(model, processor, texts):
    ti = processor(text=list(texts), return_tensors="pt", padding=True).to("cuda")
    t = model.text_model(**ti)
    p = t[1] if isinstance(t, tuple) else t.pooler_output
    return F.normalize(model.text_projection(p), dim=-1)


@torch.no_grad()
def flickr_cg(model, loader):
    fi, ft = [], []
    for b in loader:
        o = model(pixel_values=b["image"].cuda(), input_ids=b["input_ids"].cuda(),
                  attention_mask=b["attention_mask"].cuda(), return_loss=False)
        fi.append(F.normalize(o.image_embeds, dim=-1))
        ft.append(F.normalize(o.text_embeds, dim=-1))
    return float((torch.cat(fi).mean(0) - torch.cat(ft).mean(0)).norm().item())


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()
    t0 = time.time()

    def T(m):
        print(f"  [{time.time() - t0:7.1f}s] {m}", flush=True)

    processor = CLIPProcessor.from_pretrained(MODEL_ID, local_files_only=True)
    parq = sorted(glob.glob(str(REPO / "data" / "imagenet_hf" / "*.parquet")))
    if not parq:
        print("  ❌ 无 data/imagenet_hf/*.parquet")
        return 1
    ds_in = HFDataset.from_parquet(parq)
    names = [n.split(",")[0].strip().replace("_", " ") for n in ds_in.features["label"].names]
    assert len(names) == 1001
    sub = ds_in.select(list(np.random.RandomState(42).choice(len(ds_in), N_SAMPLE,
                                                             replace=False)))
    pil = list(sub["image"])
    lab = np.array(sub["label"])
    T(f"数据就绪：ImageNet {len(pil)} 张，类别 {len(names)}")

    # 单模型 + LoRA
    model, layers, _ = apply_lora_to_model(
        CLIPModel.from_pretrained(MODEL_ID, local_files_only=True),
        rank=8, alpha=16.0, apply_to_vision=True, apply_to_text=True)
    model = model.eval().cuda()
    T(f"模型就绪（LoRA {len(layers)} 层，B 零初始化）")

    ds_f = Flickr30kDataset("flickr30k", split="train", max_samples=None,
                            pre_tokenize=True)
    loader = DataLoader(torch.utils.data.Subset(ds_f, range(2000, 3000)), batch_size=64,
                        shuffle=False, num_workers=0, collate_fn=_collate_fn)
    T("Flickr30k loader 就绪")

    # 冻结基座（B=0 → 前向即冻结）
    with torch.no_grad():
        bmax = max(float(layers[k].lora_B.abs().max()) for k in layers)
    assert bmax == 0.0, f"lora_B 非零（{bmax}）→ 不能当冻结基座"
    frozen_img = enc_images(model, processor, pil)
    frozen_tf = enc_text(model, processor, [TEMPLATE.format(c) for c in names])
    frozen_np = (frozen_img @ frozen_tf.T).float().cpu().numpy()
    frozen_topk = np.argsort(-frozen_np, axis=1)[:, :TOPK]
    frozen_top1 = float((frozen_topk[:, 0] == lab).mean() * 100)
    frozen_cg = flickr_cg(model, loader)
    frozen_disp = 0.0
    T(f"冻结基座：top1_5k={frozen_top1:.2f}%  CG={frozen_cg:.4f}（B 最大 {bmax}）")

    jobs = []
    for ds in ("coco", "dtd", "food101"):
        for e in range(1, 11):
            jobs.append({"dataset": ds, "seed": 42, "epoch": e,
                         "path": f"outputs/a1_rr_ckpt/{ds}/epoch{e}.pt"})
        for s in (43, 44):
            for e in range(1, 11):
                jobs.append({"dataset": ds, "seed": s, "epoch": e,
                             "path": f"outputs/a1_rr_ckpt/seed{s}/{ds}/epoch{e}.pt"})
    for e in range(1, 11):
        jobs.append({"dataset": "flickr30k_ref", "seed": 42, "epoch": e,
                     "path": f"outputs/a1_rr_ckpt/flickr30k_ref/epoch{e}.pt"})
    jobs = [j for j in jobs if (REPO / j["path"]).exists()]
    if args.limit:
        jobs = jobs[:args.limit]
    T(f"待评测 {len(jobs)} 个检查点")

    if not args.apply:
        print("  （预演；加 --apply 开跑）")
        return 0

    results = []
    for i, j in enumerate(jobs, 1):
        ts = time.time()
        try:
            ck = torch.load(str(REPO / j["path"]), map_location="cpu", weights_only=False)
            sd = ck["lora_state_dict"]
            with torch.no_grad():
                for k, w in sd.items():
                    layers[k].lora_A.data.copy_(w["A"].to(layers[k].lora_A.dtype))
                    layers[k].lora_B.data.copy_(w["B"].to(layers[k].lora_B.dtype))
            img_c = enc_images(model, processor, pil)
            tf_c = enc_text(model, processor, [TEMPLATE.format(c) for c in names])
            S = (img_c @ tf_c.T).float().cpu().numpy()
            pi = per_image_tau(frozen_np, S, frozen_topk)
            fin = pi[np.isfinite(pi)]
            tau = float(fin.mean()) if fin.size else None
            top1 = float((S.argmax(1) == lab).mean() * 100)
            disp = float((img_c - frozen_img).norm(dim=-1).mean().item())
            cg = flickr_cg(model, loader) if (i % CG_EVERY == 0 or i == 1) else None
            results.append({
                "dataset": j["dataset"], "seed": j["seed"], "epoch": j["epoch"],
                "source_ckpt": j["path"], "tau5": round(tau, 6) if tau else None,
                "top1_5k": round(top1, 4),
                "CG_flickr_val": round(cg, 6) if cg else None,
                "displacement": round(disp, 6), "n_scored": int(fin.size),
            })
            print(f"  [{i}/{len(jobs)}] {j['dataset']}/s{j['seed']}/ep{j['epoch']:<2} "
                  f"tau={tau:.4f} top1={top1:.2f}"
                  + (f" CG={cg:.4f}" if cg else "") + f" ({time.time() - ts:.1f}s)",
                  flush=True)
        except Exception as e:
            print(f"  [{i}/{len(jobs)}] ❌ {j['path']}: {type(e).__name__}: {str(e)[:80]}",
                  flush=True)
            results.append({**j, "error": f"{type(e).__name__}: {str(e)[:150]}"})

    out = {"meta": {
        "script": "tools/_p218_eval_all_epochs.py",
        "purpose": "plan (2): evaluate every per-epoch checkpoint to test the within-dataset "
                   "tau ranking at n=30 instead of n=3",
        "model": MODEL_ID, "template": TEMPLATE, "n_sample": N_SAMPLE, "topk": TOPK,
        "frozen_top1_5k": round(frozen_top1, 4),
        "frozen_cg_flickr": round(frozen_cg, 6),
        "cg_recomputed_every": CG_EVERY,
        "generated": datetime.now(timezone.utc).isoformat(),
        "elapsed_sec": round(time.time() - t0, 1),
        "n_checkpoints": len(results),
        "n_error": sum(1 for r in results if "error" in r),
    }, "checkpoints": results}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    io.open(OUT, "w", encoding="utf-8", newline="").write(
        json.dumps(out, ensure_ascii=False, indent=1))
    T(f"✅ 已写 {OUT.relative_to(REPO)}：{len(results)} 个检查点，"
      f"{out['meta']['n_error']} 失败")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
