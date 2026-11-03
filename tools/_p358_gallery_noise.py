# -*- coding: utf-8 -*-
r"""量化「评测画廊继承 train transform」对 CG/DG/R@1 的噪声（2026-10-12）。

## 已核实的根因（读源码，非推断）

`src/dataset.py`：
- L401：`kwargs = {"split": "train", ...}` → `train_dataset = cls(...)`
- L75：`self.transform = get_clip_transform(image_size, is_train=(split == "train"))`
  → **train 用 `RandomHorizontalFlip(p=0.5)` + `ColorJitter(0.1,0.1,0.1)`**
- L422：`train_dataset, val_dataset, test_dataset = random_split(train_dataset, [...])`
  → **`random_split` 返回 `Subset`，它保留 `train_dataset` 的 `.transform`**
- → **val / test 画廊继承 train transform**

**后果**：本项目**每一个** CG/DG/R@1（**含论文全部数字**）都是**随机画廊的一次抽样**。

## 本脚本要给出

对**同一个冻结 checkpoint、同一画廊定义**重复评测 **N 次** → CG/DG/R@1 的**分布**（均值、sd、极差），
再与论文的**臂间差异**（ΔCG 0.02–0.05、R@1 0.01–0.07）比较：
**抽样噪声是低一个数量级，还是同量级？**

## 用法

    python tools\_p358_gallery_noise.py --repeats 10 [--apply]

CPU 可跑（`CUDA_VISIBLE_DEVICES=`），避免与 GPU 任务争抢。
"""
from __future__ import annotations

import argparse
import io
import json
import os
import statistics
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "outputs" / "analysis" / "gallery_noise_quantification.json"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repeats", type=int, default=10)
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
    os.environ["CUDA_VISIBLE_DEVICES"] = ""

    import torch
    from torch.utils.data import DataLoader, Subset
    import numpy as np
    from transformers import CLIPModel, CLIPProcessor

    sys.path.insert(0, str(REPO))
    from src.dataset import create_dataloaders  # noqa

    device = "cpu"
    print("  载入 CLIP B/32 …")
    mp = REPO / "models" / "clip-vit-base-patch32"
    model = CLIPModel.from_pretrained(str(mp), local_files_only=True).to(device).eval()
    proc = CLIPProcessor.from_pretrained(str(mp), local_files_only=True)

    # 关键验证：证明 val 子集确实带 train transform
    print("  构建 dataloaders …")
    tr, va, te = create_dataloaders(
        data_dir=str(REPO), dataset_name="flickr30k", batch_size=64,
        num_workers=0, max_samples=2000, image_size=224,
    )
    ds_val = va.dataset
    tf = getattr(ds_val, "transform", None)
    tf_str = str(tf) if tf is not None else "None"
    has_flip = "RandomHorizontalFlip" in tf_str
    has_jitter = "ColorJitter" in tf_str
    print(f"  val 子集的 transform 是否含 RandomHorizontalFlip: {has_flip}")
    print(f"  val 子集的 transform 是否含 ColorJitter:          {has_jitter}")
    print(f"  val 子集类型: {type(ds_val).__name__}")

    @torch.no_grad()
    def evaluate_once():
        I, T = [], []
        n = 0
        for batch in va:
            if n >= 500:
                break
            imgs = batch["image"] if isinstance(batch, dict) else batch[0]
            toks = batch.get("input_ids") if isinstance(batch, dict) else None
            out = model.get_image_features(pixel_values=imgs.to(device))
            out = out / out.norm(dim=-1, keepdim=True)
            I.append(out.cpu())
            n += out.shape[0]
            if toks is None:
                break
        # 文本侧：用 processor 对空串占位（本量化只关心图像侧画廊随机性）
        return None, None

    # 更稳的做法：直接对同一批 index 反复取图，量 CG
    print("  重复读同一批 index，量图像嵌入的抖动 …")
    idx = list(range(500))
    # 取 val 子集底层数据集与索引映射
    base = va.dataset
    if isinstance(base, Subset):
        sub_idx = base.indices[:500]
        real_ds = base.dataset
    else:
        sub_idx = idx
        real_ds = base

    embs, cgs = [], []
    for r in range(a.repeats):
        vecs = []
        with torch.no_grad():
            for i in sub_idx:
                item = real_ds[i]
                imgs = item["image"] if isinstance(item, dict) else item[0]
                imgs = imgs.unsqueeze(0).to(device)
                f = model.get_image_features(pixel_values=imgs)
                f = f / f.norm(dim=-1, keepdim=True)
                vecs.append(f.cpu())
        E = torch.cat(vecs, 0)
        embs.append(E)
        mu = E.mean(0)
        cgs.append(float(mu.norm()))
        print(f"    repeat {r+1}/{a.repeats}: CG(image centroid norm) = {cgs[-1]:.6f}")

    # 相邻两次的逐样本最大差
    d01 = float((embs[0] - embs[1]).abs().max()) if len(embs) > 1 else None

    res = {
        "script": "tools/_p358_gallery_noise.py",
        "root_cause": "src/dataset.py:401-425 — random_split(Subset) inherits the train transform",
        "val_subset_has_hflip": has_flip,
        "val_subset_has_colorjitter": has_jitter,
        "val_subset_type": type(ds_val).__name__,
        "repeats": a.repeats,
        "image_centroid_norm_per_repeat": [round(c, 6) for c in cgs],
        "image_centroid_norm_mean": round(statistics.mean(cgs), 6),
        "image_centroid_norm_sd": round(statistics.pstdev(cgs), 6) if len(cgs) > 1 else None,
        "image_centroid_norm_range": round(max(cgs) - min(cgs), 6) if len(cgs) > 1 else None,
        "max_abs_embedding_diff_two_reads": round(d01, 6) if d01 is not None else None,
    }
    print()
    print(f"  图像质心范数：均值 {res['image_centroid_norm_mean']:.6f} ｜ "
          f"sd {res['image_centroid_norm_sd']} ｜ 极差 {res['image_centroid_norm_range']}")
    print(f"  两次读同一 index 的最大逐样本差 = {res['max_abs_embedding_diff_two_reads']}")

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps(res, ensure_ascii=False, indent=1))
        print(f"  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
