# -*- coding: utf-8 -*-
r"""调试：评测循环里到底哪一步卡住（2026-10-12）。

用第 1 个检查点，逐步打印时间戳。

    python tools\_p217_debug_loop.py
"""
from __future__ import annotations

import glob
import io
import json
import os
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))

import numpy as np  # noqa: E402
import torch  # noqa: E402


def T(t0, msg):
    print(f"  [{time.time() - t0:7.1f}s] {msg}", flush=True)


def main() -> int:
    t0 = time.time()
    from transformers import CLIPModel, CLIPProcessor
    from datasets import Dataset as HFDataset
    from torch.utils.data import DataLoader
    from src.dataset import Flickr30kDataset, _collate_fn
    from src.lora import apply_lora_to_model
    from a1_h_common import per_image_tau
    T(t0, "imports 完成")

    import torch.nn.functional as F
    MODEL_ID = "openai/clip-vit-base-patch32"
    TEMPLATE = "a photo of a {}"
    N_SAMPLE, TOPK, BATCH = 5000, 5, 128

    processor = CLIPProcessor.from_pretrained(MODEL_ID, local_files_only=True)
    T(t0, "processor 就绪")
    parq = sorted(glob.glob(str(REPO / "data" / "imagenet_hf" / "*.parquet")))
    T(t0, f"parquet {len(parq)} 个")
    ds_in = HFDataset.from_parquet(parq)
    legacy_names = [n.split(",")[0].strip().replace("_", " ")
                    for n in ds_in.features["label"].names]
    T(t0, f"parquet 载入，类别 {len(legacy_names)}")
    rng = np.random.RandomState(42)
    idx = rng.choice(len(ds_in), N_SAMPLE, replace=False)
    sub = ds_in.select(list(idx))
    pil = list(sub["image"])
    lab = np.array(sub["label"])
    T(t0, f"样本 {len(pil)} 张")

    fm = CLIPModel.from_pretrained(MODEL_ID, local_files_only=True).eval().cuda()
    T(t0, "冻结模型到 cuda")

    @torch.no_grad()
    def enc(m, ps, imgs):
        out = []
        for i in range(0, len(imgs), BATCH):
            inp = ps(images=list(imgs[i:i + BATCH]), return_tensors="pt").to("cuda")
            v = m.vision_model(**inp)
            vp = v[1] if isinstance(v, tuple) else v.pooler_output
            out.append(F.normalize(m.visual_projection(vp), dim=-1))
        return torch.cat(out)

    frozen_img = enc(fm, processor, pil)
    T(t0, f"冻结图像编码完成 {tuple(frozen_img.shape)}")

    ti = processor(text=[TEMPLATE.format(c) for c in legacy_names],
                   return_tensors="pt", padding=True).to("cuda")
    with torch.no_grad():
        tout = fm.text_model(**ti)
        pooled = tout[1] if isinstance(tout, tuple) else tout.pooler_output
        tf = F.normalize(fm.text_projection(pooled), dim=-1)
    T(t0, f"冻结文本编码完成 {tuple(tf.shape)}")
    frozen_np = (frozen_img @ tf.T).float().cpu().numpy()
    frozen_topk = np.argsort(-frozen_np, axis=1)[:, :TOPK]
    T(t0, f"冻结 top1 = {float((frozen_topk[:, 0] == lab).mean() * 100):.2f}%")

    T(t0, "→ 开始 Flickr30k 数据集（这一步可能慢）")
    ds_f = Flickr30kDataset("flickr30k", split="train", max_samples=None,
                            pre_tokenize=True)
    T(t0, "Flickr30kDataset 构造完成")
    loader = DataLoader(torch.utils.data.Subset(ds_f, range(2000, 3000)), batch_size=64,
                        shuffle=False, num_workers=0, collate_fn=_collate_fn)
    T(t0, "DataLoader 构造完成")

    T(t0, "→ 建 LoRA 模型")
    m, layers = apply_lora_to_model(
        CLIPModel.from_pretrained(MODEL_ID, local_files_only=True),
        rank=8, alpha=16.0, apply_to_vision=True, apply_to_text=True)
    m = m.eval().cuda()
    T(t0, f"LoRA 模型就绪，{len(layers)} 层")

    p = REPO / "outputs" / "a1_rr_ckpt" / "coco" / "epoch1.pt"
    ck = torch.load(str(p), map_location="cpu", weights_only=False)
    sd = ck["lora_state_dict"]
    with torch.no_grad():
        for k, w in sd.items():
            layers[k].lora_A.data.copy_(w["A"].to(layers[k].lora_A.dtype))
            layers[k].lora_B.data.copy_(w["B"].to(layers[k].lora_B.dtype))
    T(t0, "权重载入完成")

    t1 = time.time()
    with torch.no_grad():
        img_c = enc(m, processor, pil)
    T(t0, f"检查点图像编码完成（{time.time() - t1:.1f}s）")

    t1 = time.time()
    with torch.no_grad():
        ti2 = processor(text=[TEMPLATE.format(c) for c in legacy_names],
                        return_tensors="pt", padding=True).to("cuda")
        tout2 = m.text_model(**ti2)
        pooled2 = tout2[1] if isinstance(tout2, tuple) else tout2.pooler_output
        tf2 = F.normalize(m.text_projection(pooled2), dim=-1)
    T(t0, f"检查点文本编码完成（{time.time() - t1:.1f}s）")

    S = (img_c @ tf2.T).float().cpu().numpy()
    pi = per_image_tau(frozen_np, S, frozen_topk)
    fin = pi[np.isfinite(pi)]
    T(t0, f"tau5 = {float(fin.mean()):.4f}  top1 = "
          f"{float((S.argmax(1) == lab).mean() * 100):.2f}%")

    t1 = time.time()
    fi2, ft2 = [], []
    with torch.no_grad():
        for j, b in enumerate(loader):
            oo = m(pixel_values=b["image"].cuda(), input_ids=b["input_ids"].cuda(),
                   attention_mask=b["attention_mask"].cuda(), return_loss=False)
            fi2.append(F.normalize(oo.image_embeds, dim=-1))
            ft2.append(F.normalize(oo.text_embeds, dim=-1))
            if j == 0:
                T(t0, "Flickr30k 第 1 个 batch 完成")
    cg = float((torch.cat(fi2).mean(0) - torch.cat(ft2).mean(0)).norm().item())
    T(t0, f"CG = {cg:.4f}（{time.time() - t1:.1f}s）")
    T(t0, "✅ 全部步骤通过")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
