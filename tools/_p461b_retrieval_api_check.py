# -*- coding: utf-8 -*-
r"""诊断：CLIP 检索管线在 4 种调用方式下的 R@1（2026-10-12）。

## 为什么需要

`tools/_p461_clip_ranksweep.py` 的 `rank=0` 冻结基线在 Flickr30k 1K test 上
只得到 i2t R@1 = 0.145 / t2i R@1 = 0.0105——远低于 OpenAI CLIP ViT-B/32 的
已知水平，说明**评测管线有问题**，不是模型问题。本脚本用 4 种调用方式对照，
定位到底是 (a) 文本 padding 方式 还是 (b) 特征提取 API 造成的。

4 种方式：
  A. `padding="max_length", max_length=77` + `get_image_features/get_text_features`
  B. `padding=True`（动态）+ 同 API
  C. `padding=True` + 联合 `model(**inputs)` 的 `logits_per_image`
  D. `padding="max_length"` + 联合 `model(**inputs)`

## 用途

**只用于诊断**，其数字不作为论文主张；`_p461` 的正式配置以本脚本结论为准
（结论写进 `docs/P3_DOWNSTREAM.md`）。

    python tools\_p461b_retrieval_api_check.py
"""
from __future__ import annotations

import io
import json
import os
import sys
from pathlib import Path

os.environ.setdefault("HF_HUB_OFFLINE", "1")

import torch
import torch.nn.functional as F

REPO = Path(__file__).resolve().parents[1]
MANIFEST = REPO / "outputs" / "analysis" / "p3d_manifest.json"
MODEL_DIR = REPO / "models" / "clip-vit-base-patch32"
N_IMG = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 200


def r1_i2t(sim, C):
    N = sim.shape[0]
    top1 = sim.topk(1, dim=1).indices // C
    return (top1.squeeze(1) == torch.arange(N)).float().mean().item()


def main() -> int:
    from PIL import Image
    from transformers import CLIPModel, CLIPProcessor

    test = json.loads(io.open(MANIFEST, encoding="utf-8").read())["datasets"]["flickr30k"]["test"]
    imgdir = REPO / "flickr30k" / "flickr30k-images"
    imgs = []
    for s in test[:N_IMG]:
        with Image.open(imgdir / s["image"]) as im:
            imgs.append(im.convert("RGB"))
    caps_flat = [c for s in test[:N_IMG] for c in s["captions"][:5]]
    C = 5

    model = CLIPModel.from_pretrained(str(MODEL_DIR), local_files_only=True).eval()
    proc = CLIPProcessor.from_pretrained(str(MODEL_DIR), local_files_only=True)
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    model = model.to(dev)
    print(f"device={dev}  images={len(imgs)}  captions={len(caps_flat)}")

    px = torch.stack([proc(images=im, return_tensors="pt")["pixel_values"][0] for im in imgs])
    with torch.no_grad():
        IE = F.normalize(model.get_image_features(pixel_values=px.to(dev)).pooler_output.float(),
                         p=2, dim=-1)

    out = {}
    for name, kw in [("max_length", dict(padding="max_length", max_length=77)),
                     ("dynamic", dict(padding=True))]:
        enc = proc.tokenizer(text=caps_flat, return_tensors="pt", truncation=True, **kw)
        ids, am = enc["input_ids"].to(dev), enc["attention_mask"].to(dev)
        with torch.no_grad():
            TE = F.normalize(model.get_text_features(input_ids=ids,
                                                     attention_mask=am).pooler_output.float(),
                             p=2, dim=-1)
        sim = (IE @ TE.T).cpu()
        out[f"A/B_{name}_features"] = r1_i2t(sim, C)

        # 联合调用（同一 tokenizer 输出）
        px_b = px[:8].to(dev)
        ids_b = ids[:8 * C]
        am_b = am[:8 * C]
        with torch.no_grad():
            logits = model(pixel_values=px_b, input_ids=ids_b,
                           attention_mask=am_b).logits_per_image  # (8, 8*C)
        out[f"C/D_{name}_joint"] = (logits.argmax(dim=1) // C == torch.arange(8, device=dev)).float().mean().item()

    # 诊断量：对角相似度 vs 非对角
    enc = proc.tokenizer(text=caps_flat, return_tensors="pt", truncation=True, padding=True)
    with torch.no_grad():
        TE = F.normalize(model.get_text_features(input_ids=enc["input_ids"].to(dev),
                                                 attention_mask=enc["attention_mask"].to(dev)
                                                 ).pooler_output.float(), p=2, dim=-1)
    sim = (IE @ TE.T).cpu()
    own = sim[torch.arange(N_IMG).repeat_interleave(C), torch.arange(N_IMG * C)]
    print(f"  同图相似度 mean={own.mean():.4f} std={own.std():.4f}; "
          f"全体 mean={sim.mean():.4f}")
    print(f"  文本嵌入范数（归一化前）mean={TE.norm(dim=-1).mean():.3f}")

    # 分块 R@1：定位是否存在"前 200 好、后面崩"的数据错位
    if N_IMG % 200 == 0 and N_IMG > 200:
        print("  分块 i2t R@1（每 200 图）:")
        for s in range(0, N_IMG, 200):
            e = s + 200
            sub = sim[s:e, s * C:e * C]
            print(f"    [{s}:{e}] {r1_i2t(sub, C):.4f}")

    print("\n=== 4 种调用方式的 i2t R@1 ===")
    for k, v in out.items():
        print(f"  {k:<28} R@1={v:.4f}")
    print("  参照：OpenAI CLIP ViT-B/32 在 Flickr30k 1K test 上 i2t R@1 约 0.81（文献值，非本机实测）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
