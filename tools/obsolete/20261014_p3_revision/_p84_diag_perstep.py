# -*- coding: utf-8 -*-
r"""诊断 `_p83` 的 Σip 为何与 `_p81` 差一个数量级（2026-10-10）。

## 现象（冒烟，1 epoch / 500 样本 / batch 64）

| 臂 | `_p83` Σip 全步均值 | `_p81` ep0 | loss 走向 |
|---|---|---|---|
| `text_only` | +21.35 | +19.50 | 0.688 → **0.939（上升）** |
| `both` | **+3.83** | +18.81 | 0.869 → 0.512 |
| `vision_only` | **+286.69** | +17.64 | 1.133 → 0.791 |

**三个可疑点**：① `vision_only` 量级离谱；② `both`/`vision_only` 小一个数量级；
③ `text_only` 的 loss 上升。

## 本脚本

在**同一批**上，用**两种顺序**各算一次内积，并打印**逐侧分解**：
- **顺序 A**（`_p83` 的做法）：任务梯度 → `opt.step()` → zero_grad → 测 `DG*` 梯度
- **顺序 B**（`_p81` 的做法）：任务梯度 → 克隆 gL（不 step）→ zero_grad → 测 `DG*` 梯度

**判据**：若 A 与 B 结果不同 → **顺序是问题**；若相同 → 问题在别处。

    python tools\_p84_diag_perstep.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--batch", type=int, default=64)
    args = ap.parse_args()
    if not args.apply:
        print("=== 诊断：两种顺序下的 Σip ===")
        return 0

    import torch
    import torch.nn.functional as F
    from src.config import ExperimentConfig, LoRAConfig, TrainConfig
    from src.trainer import GapAwareTrainer
    from src.dataset import create_dataloaders

    device = "cuda" if torch.cuda.is_available() else "cpu"
    loader, _, _ = create_dataloaders(dataset_name="flickr30k", data_dir=".",
                                      batch_size=args.batch, max_samples=128)
    b = next(iter(loader))

    for arm, flags in (("text_only", dict(apply_to_vision=False, apply_to_text=True)),
                       ("both", dict(apply_to_vision=True, apply_to_text=True)),
                       ("vision_only", dict(apply_to_vision=True, apply_to_text=False))):
        print(f"\n=== {arm} ===", flush=True)
        torch.manual_seed(42)
        cfg = ExperimentConfig(
            name=f"diag_{arm}", lora=LoRAConfig(rank=8, alpha=16, **flags),
            train=TrainConfig(dataset="flickr30k", batch_size=args.batch,
                              num_epochs=1, max_samples=128,
                              clip_model="models/clip-vit-base-patch32",
                              save_dir=str(REPO / "outputs/_diag")))
        tr = GapAwareTrainer(cfg)
        tr.device = device
        tr.setup_model()
        params = [(n, p) for n, p in tr.model.named_parameters() if p.requires_grad]
        pmap = dict(params)
        imgs = b["image"].to(device)
        ii = b["input_ids"].to(device)
        am = b["attention_mask"].to(device)

        def task_grad():
            tr.model.zero_grad(set_to_none=True)
            o = tr.model(pixel_values=imgs, input_ids=ii, attention_mask=am)
            I = F.normalize(o.image_embeds, p=2, dim=-1)
            T = F.normalize(o.text_embeds, p=2, dim=-1)
            lg = 100.0 * I @ T.T
            lab = torch.arange(I.shape[0], device=device)
            loss = (F.cross_entropy(lg, lab) + F.cross_entropy(lg.T, lab)) / 2
            loss.backward()
            g = {n: (pmap[n].grad.detach().float().clone()
                     if pmap[n].grad is not None else None) for n, _ in params}
            return float(loss), g

        def dg_grad():
            tr.model.zero_grad(set_to_none=True)
            o = tr.model(pixel_values=imgs, input_ids=ii, attention_mask=am)
            I = F.normalize(o.image_embeds.float(), p=2, dim=-1)
            T = F.normalize(o.text_embeds.float(), p=2, dim=-1)
            dg = ((I - T) ** 2).sum(-1).mean()
            dg.backward()
            return {n: (pmap[n].grad.detach().float().clone()
                        if pmap[n].grad is not None else None) for n, _ in params}

        def inner(gL, gD):
            out = {}
            for side, key in (("v", "vision_model"), ("t", "text_model")):
                names = [n for n in gL if key in n]
                if not names:
                    out[side] = None
                    continue
                out[side] = float(sum(torch.dot(gD[n].flatten(), gL[n].flatten())
                                      for n in names
                                      if gD.get(n) is not None and gL.get(n) is not None))
            return out

        # 顺序 B（_p81 的做法）：不 step
        loss0, gL0 = task_grad()
        d0 = inner(gL0, dg_grad())
        print(f"  顺序B(不step): loss={loss0:.4f} ｜ ip_v={d0['v']} ｜ ip_t={d0['t']}"
              f" ｜ Σ={sum(x for x in d0.values() if x is not None):+.4f}", flush=True)

        # 顺序 A（_p83 的做法）：先 step 再测
        loss1, gL1 = task_grad()
        opt = torch.optim.AdamW([p for _, p in params], lr=1e-4, weight_decay=0.01)
        opt.step()
        d1 = inner(gL1, dg_grad())
        print(f"  顺序A(step后) : loss={loss1:.4f} ｜ ip_v={d1['v']} ｜ ip_t={d1['t']}"
              f" ｜ Σ={sum(x for x in d1.values() if x is not None):+.4f}", flush=True)

        # 再测一次"训练前"（第一个 batch 的 loss）
        tr2 = GapAwareTrainer(cfg)
        tr2.device = device
        tr2.setup_model()
        p2 = [(n, p) for n, p in tr2.model.named_parameters() if p.requires_grad]
        pm2 = dict(p2)
        with torch.no_grad():
            o = tr2.model(pixel_values=imgs, input_ids=ii, attention_mask=am)
            I = F.normalize(o.image_embeds, p=2, dim=-1)
            T = F.normalize(o.text_embeds, p=2, dim=-1)
            lg = 100.0 * I @ T.T
            lab = torch.arange(I.shape[0], device=device)
            l0 = float((F.cross_entropy(lg, lab) + F.cross_entropy(lg.T, lab)) / 2)
        print(f"  初始化时 loss={l0:.4f}（随机基线 ≈ ln({args.batch})="
              f"{torch.log(torch.tensor(float(args.batch))).item():.3f}）", flush=True)
        del tr, tr2
        if device == "cuda":
            torch.cuda.empty_cache()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
