# -*- coding: utf-8 -*-
r"""决定性对照：`_p79`（+64）与 `_p83`/`_p84`（−22）为何符号相反？（2026-10-10）

## 已测

| 脚本 | 协议 | `text_only` 的 Σ |
|---|---|---|
| `_p79` | batch 128，7 批**平均**，**不 step** | **+64.49** |
| `_p84` 顺序 B | batch 64，**单批**，**不 step** | **−22.04** |

**两者都是"不 step"，差别是**：batch 大小（128 vs 64）、批数（7 vs 1）、
以及 `_p79` 在 `_p84` 里被我改写过（连 `cos` 也算了）。

## 本脚本

**同一批数据、同一模型、同一 seed**，只改 **batch 大小**（64 / 128），
各算一次 Σ，并**打印逐批明细**（不平均）→ 看是"批间差异极大"还是"系统性符号差"。

**判据**：
- 若**同一 batch 大小下**符号稳定 → 问题是 batch 大小；
- 若**批间在 ±50 之间乱跳** → 说明**单批测量极不稳定**，
  "轨迹平均"必须用**很多批**，且 `_p79` 的 +64 与 `_p84` 的 −22 都只是噪声。

    python tools\_p85_sign_check.py [--apply]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--n-batches", type=int, default=7)
    args = ap.parse_args()
    if not args.apply:
        print("=== 符号对照：同一模型、同一 seed，只改 batch 大小 ===")
        return 0

    import torch
    import torch.nn.functional as F
    from src.config import ExperimentConfig, LoRAConfig, TrainConfig
    from src.trainer import GapAwareTrainer
    from src.dataset import create_dataloaders

    device = "cuda" if torch.cuda.is_available() else "cpu"

    for bs in (64, 128):
        print(f"\n{'='*58}\n=== batch = {bs} ===", flush=True)
        loader, _, _ = create_dataloaders(dataset_name="flickr30k", data_dir=".",
                                          batch_size=bs, max_samples=1024)
        batches = [b for i, b in enumerate(loader) if i < args.n_batches]
        torch.manual_seed(42)
        cfg = ExperimentConfig(
            name=f"sign_{bs}",
            lora=LoRAConfig(rank=8, alpha=16, apply_to_vision=False, apply_to_text=True),
            train=TrainConfig(dataset="flickr30k", batch_size=bs, num_epochs=1,
                              max_samples=1024, clip_model="models/clip-vit-base-patch32",
                              save_dir=str(REPO / "outputs/_sign")))
        tr = GapAwareTrainer(cfg)
        tr.device = device
        tr.setup_model()
        params = [(n, p) for n, p in tr.model.named_parameters() if p.requires_grad]
        pmap = dict(params)

        print(f"  {'批':>3}{'loss':>10}{'ip_v':>13}{'ip_t':>13}{'Σ':>13}")
        tot = 0.0
        for k, b in enumerate(batches):
            imgs = b["image"].to(device)
            ii = b["input_ids"].to(device)
            am = b["attention_mask"].to(device)
            # 任务梯度（不 step）
            tr.model.zero_grad(set_to_none=True)
            o = tr.model(pixel_values=imgs, input_ids=ii, attention_mask=am)
            I = F.normalize(o.image_embeds, p=2, dim=-1)
            T = F.normalize(o.text_embeds, p=2, dim=-1)
            lg = 100.0 * I @ T.T
            lab = torch.arange(I.shape[0], device=device)
            loss = (F.cross_entropy(lg, lab) + F.cross_entropy(lg.T, lab)) / 2
            loss.backward()
            gL = {n: (pmap[n].grad.detach().float().clone()
                      if pmap[n].grad is not None else None) for n, _ in params}
            # ∇DG*
            tr.model.zero_grad(set_to_none=True)
            o2 = tr.model(pixel_values=imgs, input_ids=ii, attention_mask=am)
            I2 = F.normalize(o2.image_embeds.float(), p=2, dim=-1)
            T2 = F.normalize(o2.text_embeds.float(), p=2, dim=-1)
            dg = ((I2 - T2) ** 2).sum(-1).mean()
            dg.backward()
            gD = {n: (pmap[n].grad.detach().float().clone()
                      if pmap[n].grad is not None else None) for n, _ in params}
            iv = it = 0.0
            for side, key in (("v", "vision_model"), ("t", "text_model")):
                names = [n for n in gL if key in n]
                if not names:
                    continue
                v = float(sum(torch.dot(gD[n].flatten(), gL[n].flatten())
                              for n in names
                              if gD.get(n) is not None and gL.get(n) is not None))
                if side == "v":
                    iv = v
                else:
                    it = v
            tot += iv + it
            print(f"  {k:>3}{float(loss):>10.4f}{iv:>+13.3f}{it:>+13.3f}{iv+it:>+13.3f}",
                  flush=True)
        n = max(len(batches), 1)
        print(f"  ── 平均 Σ = {tot/n:+.4f}（{n} 批）")
        del tr
        if device == "cuda":
            torch.cuda.empty_cache()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
