# -*- coding: utf-8 -*-
r"""方案②：评测**全部逐 epoch 检查点**，用组内 n=30 重检 τ 的排序力（2026-10-12）。

## 为什么

`tools/_p209` 发现：τ 的池化相关（+0.85）与组内相关（−0.27）**方向相反**（Simpson 悖论）。
但组内每数据集只有 **3 个 seed** → **n=3 的相关不可靠**，不能据此定论。

**现归档里有 **120 个检查点**（4 数据集 × 10 epoch × 3 seed），论文只评了 13 个**
（`a1_h_offset.py` 写死 `epoch10.pt`）。→ **补评 107 个即可把组内 n 从 3 提到 30，无需训练。**

## 评测内容（与 `a1_h_offset.py` 同一协议）

- 模型 `openai/clip-vit-base-patch32`｜模板 `a photo of a {}`
- ImageNet 5k 样本（`RandomState(42)`，legacy1001 类表）→ `top1_5k`
- Flickr30k val rows 2000–3000 → `CG`
- `tau5` 用 `a1_h_common.per_image_tau`（冻结 top-5 集）
- 逐检查点还存几何量（类内散布、margin）

**每个数字都写进 JSON 并带 `source_ckpt` 字段。**

    python tools\_p214_eval_all_epochs.py [--apply] [--limit N]
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
PLACEHOLDER_IDX = 1000
BATCH = 128
OUT = REPO / "outputs" / "a1_epoch_sweep.json"


@torch.no_grad()
def encode_images(model, processor, pil_list, batch=BATCH):
    feats = []
    for i in range(0, len(pil_list), batch):
        inp = processor(images=list(pil_list[i:i + batch]),
                        return_tensors="pt").to("cuda")
        vout = model.vision_model(**inp)
        vp = vout[1] if isinstance(vout, tuple) else vout.pooler_output
        feats.append(F.normalize(model.visual_projection(vp), dim=-1))
    return torch.cat(feats)


@torch.no_grad()
def text_feats(model, processor, texts):
    ti = processor(text=list(texts), return_tensors="pt", padding=True).to("cuda")
    tout = model.text_model(**ti)
    pooled = tout[1] if isinstance(tout, tuple) else tout.pooler_output
    return F.normalize(model.text_projection(pooled), dim=-1)


def build_lora(vision=True, text=True, rank=8, alpha=16.0):
    m, layers, _ = apply_lora_to_model(
        CLIPModel.from_pretrained(MODEL_ID, local_files_only=True),
        rank=rank, alpha=alpha, apply_to_vision=vision, apply_to_text=text)
    return m, layers


def load_ckpt(model, layers, path):
    ck = torch.load(path, map_location="cpu", weights_only=False)
    sd = ck["lora_state_dict"] if isinstance(ck, dict) and "lora_state_dict" in ck else ck
    miss = set(sd) - set(layers)
    extra = set(layers) - set(sd)
    if miss or extra:
        raise ValueError(f"LoRA key mismatch ({len(miss)} unknown, {len(extra)} unfilled)")
    with torch.no_grad():
        for k, w in sd.items():
            layers[k].lora_A.data.copy_(w["A"].to(layers[k].lora_A.dtype))
            layers[k].lora_B.data.copy_(w["B"].to(layers[k].lora_B.dtype))
    return model


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--limit", type=int, default=0, help="只跑前 N 个（调试）")
    args = ap.parse_args()
    t0 = time.time()

    # ── 冻结基座（与 a1_h_offset.py 同协议）──
    parq = sorted(glob.glob(str(REPO / "data" / "imagenet_hf" / "*.parquet")))
    if not parq:
        print("  ❌ 找不到 data/imagenet_hf/*.parquet")
        return 1
    torch.manual_seed(0)
    np.random.seed(0)
    processor = CLIPProcessor.from_pretrained(MODEL_ID, local_files_only=True)
    ds_in = HFDataset.from_parquet(parq)
    legacy_names = [n.split(",")[0].strip().replace("_", " ")
                    for n in ds_in.features["label"].names]
    assert len(legacy_names) == 1001, f"类表 {len(legacy_names)} != 1001"
    rng = np.random.RandomState(42)
    idx = rng.choice(len(ds_in), N_SAMPLE, replace=False)
    sub = ds_in.select(list(idx))
    pil = list(sub["image"])
    lab = np.array(sub["label"])

    fm = CLIPModel.from_pretrained(MODEL_ID, local_files_only=True).cuda().eval()
    tf_frozen = text_feats(fm, processor, [TEMPLATE.format(c) for c in legacy_names])
    fm = fm.cuda()
    frozen_img = encode_images(fm, processor, pil)
    frozen_np = (frozen_img @ tf_frozen.T).float().cpu().numpy()
    frozen_topk = np.argsort(-frozen_np, axis=1)[:, :TOPK]
    frozen_top1 = float((frozen_topk[:, 0] == lab).mean() * 100)

    # Flickr30k val 2000-3000（算 CG）
    ds_f = Flickr30kDataset("flickr30k", split="train", max_samples=None,
                            pre_tokenize=True)
    loader = DataLoader(torch.utils.data.Subset(ds_f, range(2000, 3000)), batch_size=64,
                        shuffle=False, num_workers=0, collate_fn=_collate_fn)
    fi, ft = [], []
    with torch.no_grad():
        for b in loader:
            o = fm(pixel_values=b["image"].cuda(), input_ids=b["input_ids"].cuda(),
                   attention_mask=b["attention_mask"].cuda(), return_loss=False)
            fi.append(F.normalize(o.image_embeds, dim=-1))
            ft.append(F.normalize(o.text_embeds, dim=-1))
    fi, ft = torch.cat(fi), torch.cat(ft)
    frozen_cg = float((fi.mean(0) - ft.mean(0)).norm().item())

    print("=" * 88)
    print("冻结基座（与 tools/a1_h_offset.py 同协议）")
    print("=" * 88)
    print(f"  模型 {MODEL_ID} ｜ 模板 {TEMPLATE} ｜ 类别 {len(legacy_names)}")
    print(f"  ImageNet 5k top-1 = {frozen_top1:.2f}% ｜ Flickr30k val CG = {frozen_cg:.4f}")
    print(f"  frozen tau5 = 1.0（按定义：与自身比）")

    # ── 检查点清单 ──
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
    print()
    print("=" * 88)
    print(f"待评测检查点: {len(jobs)} 个")
    print("=" * 88)
    from collections import Counter
    for k, v in sorted(Counter(f"{j['dataset']}/seed{j['seed']}" for j in jobs).items()):
        print(f"  {k:<24} {v} 个")

    if not args.apply:
        print("\n  （预演；加 --apply 开跑）")
        return 0

    # ── 逐检查点评测 ──
    model, layers = build_lora(vision=True, text=True, rank=8, alpha=16.0)
    model = model.cuda().eval()
    results = []
    for i, j in enumerate(jobs, 1):
        ts = time.time()
        try:
            load_ckpt(model, layers, str(REPO / j["path"]))
            with torch.no_grad():
                tfc = text_feats(model, processor, [TEMPLATE.format(c)
                                                    for c in legacy_names])
                imgc = encode_images(model, processor, pil)
                S = (imgc @ tfc.T).float().cpu().numpy()
                pi = per_image_tau(frozen_np, S, frozen_topk)
                fin = pi[np.isfinite(pi)]
                tau = float(fin.mean()) if fin.size else None
                top1 = float((S.argmax(1) == lab).mean() * 100)
                # CG
                o = model(pixel_values=None) if False else None
                fi2, ft2 = [], []
                for b in loader:
                    oo = model(pixel_values=b["image"].cuda(),
                               input_ids=b["input_ids"].cuda(),
                               attention_mask=b["attention_mask"].cuda(),
                               return_loss=False)
                    fi2.append(F.normalize(oo.image_embeds, dim=-1))
                    ft2.append(F.normalize(oo.text_embeds, dim=-1))
                cg = float((torch.cat(fi2).mean(0) - torch.cat(ft2).mean(0)).norm().item())
                # 几何
                norms = imgc.norm(dim=-1)
                disp = float((imgc - frozen_img).norm(dim=-1).mean().item())
                S_c = S[np.arange(len(lab)), lab]
                margin = float(S_c.mean())
            rec = {"dataset": j["dataset"], "seed": j["seed"], "epoch": j["epoch"],
                   "source_ckpt": j["path"], "tau5": round(tau, 6) if tau else None,
                   "top1_5k": round(top1, 4), "CG_flickr_val": round(cg, 6),
                   "displacement": round(disp, 6), "margin_mean": round(margin, 6),
                   "n_scored": int(fin.size)}
            results.append(rec)
            print(f"  [{i}/{len(jobs)}] {j['dataset']}/seed{j['seed']}/ep{j['epoch']:<2} "
                  f"tau={tau:.4f} top1={top1:.2f} CG={cg:.4f} "
                  f"({time.time() - ts:.1f}s)")
        except Exception as e:
            print(f"  [{i}/{len(jobs)}] ❌ {j['path']}: {type(e).__name__}: {str(e)[:90]}")
            results.append({**j, "error": f"{type(e).__name__}: {str(e)[:150]}"})
        if i % 10 == 0:
            torch.cuda.empty_cache()

    out = {
        "meta": {
            "script": "tools/_p214_eval_all_epochs.py",
            "purpose": "plan (2): evaluate every per-epoch checkpoint so the within-dataset "
                       "tau ranking can be tested at n=30 instead of n=3",
            "model": MODEL_ID, "template": TEMPLATE,
            "n_sample": N_SAMPLE, "topk": TOPK,
            "frozen_top1_5k": frozen_top1, "frozen_cg_flickr": frozen_cg,
            "generated": datetime.now(timezone.utc).isoformat(),
            "elapsed_sec": round(time.time() - t0, 1),
            "n_checkpoints": len(results),
            "n_error": sum(1 for r in results if "error" in r),
        },
        "checkpoints": results,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    io.open(OUT, "w", encoding="utf-8", newline="").write(
        json.dumps(out, ensure_ascii=False, indent=1))
    print()
    print("=" * 88)
    print(f"✅ 已写 {OUT.relative_to(REPO)}")
    print(f"   {len(results)} 个检查点，{out['meta']['n_error']} 个失败，"
          f"耗时 {out['meta']['elapsed_sec']:.0f}s")
    print("=" * 88)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
