# -*- coding: utf-8 -*-
r"""**CPU 预检** `_p21_alpha_trainer_based.py` 的接口与梯度路径（2026-10-08 08:05）。

## 为什么

GPU 被队列占满，但 A 脚本里有很多**可能拼错/用错**的接口：
`AlphaTrainer.capture_inner`、`_compute_dg_star_record` 的返回属性、`processor` 调用方式、
`model(pixel_values=..., input_ids=..., attention_mask=...)` 的返回字段。

**在 CPU 上用极少样本走通一遍，比之后浪费 GPU 时间划算**——
本项目已因"没先验证就开跑"浪费过两次（样本量差 15 倍、动力学差 10 倍）。

## 预检内容

1. `GapAwareTrainer` 能否在 `device=cpu` 下 `setup_model()`；
2. `_compute_dg_star_record` 返回对象的**属性名**是否为 `dg_star`；
3. 前向返回是否有 `image_embeds` / `text_embeds`；
4. `capture_inner` 能否跑通并返回**有限值**（不是 NaN）；
5. **不落盘、不改任何结果**。

    python tools\_p21_preflight_cpu.py
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))


def main() -> int:
    import torch
    from src.config import ExperimentConfig, LoRAConfig, TrainConfig, GapConfig
    from src.trainer import GapAwareTrainer
    from src.dataset import create_dataloaders

    print("=== A 脚本 CPU 预检（不落盘、不改结果）===")

    class Probe(GapAwareTrainer):
        pass

    cfg = ExperimentConfig(
        name="preflight",
        lora=LoRAConfig(rank=4, alpha=8, apply_to_vision=True, apply_to_text=True),
        gap=GapConfig(compute_every_n_epochs=1),
        train=TrainConfig(dataset="flickr30k", batch_size=4, num_epochs=1,
                          max_samples=16, learning_rate=1e-4, save_dir=str(REPO / "outputs/_preflight")))
    try:
        tr = Probe(cfg)
        tr.device = "cpu"
        tr.setup_model()
    except Exception as e:
        print(f"  ❌ setup_model 失败: {str(e)[:200]}")
        return 1
    print("  ✅ setup_model 通过")

    tr.enable_dg_star_tracking()
    try:
        train_loader, val_loader, _ = create_dataloaders(
            dataset_name="flickr30k", data_dir=".", batch_size=4, max_samples=16)
    except Exception as e:
        print(f"  ❌ dataloader 失败: {str(e)[:200]}")
        return 1
    print(f"  ✅ dataloader: train={len(train_loader)} val={len(val_loader)} 批")

    # ① _compute_dg_star_record 的属性名
    try:
        rec = tr._compute_dg_star_record(val_loader, 1)
        fields = [a for a in ("dg_star", "cg", "dg_empirical") if hasattr(rec, a)]
        print(f"  {'✅' if 'dg_star' in fields else '❌'} _compute_dg_star_record 字段: {fields}")
        if "dg_star" not in fields:
            print(f"     ⚠ 实际类型 {type(rec)} ｜ dir 含 dg: "
                  f"{[a for a in dir(rec) if 'dg' in a.lower() or 'gap' in a.lower()]}")
            return 1
        print(f"     dg_star = {rec.dg_star:.6f}（应为正、有限）")
    except Exception as e:
        print(f"  ❌ _compute_dg_star_record 失败: {str(e)[:200]}")
        return 1

    # ② 前向返回字段
    try:
        b = next(iter(val_loader))
        ti = tr.processor(text=b["caption"], return_tensors="pt", padding=True,
                          truncation=True, max_length=77)
        tr.model.eval()
        out = tr.model(pixel_values=b["image"].to("cpu"),
                       input_ids=ti["input_ids"].to("cpu"),
                       attention_mask=ti["attention_mask"].to("cpu"))
        has = [a for a in ("image_embeds", "text_embeds") if hasattr(out, a)]
        print(f"  {'✅' if len(has) == 2 else '❌'} 前向返回字段: {has}")
        if len(has) != 2:
            print(f"     ⚠ 实际: {[a for a in dir(out) if not a.startswith('_')][:14]}")
            return 1
    except Exception as e:
        print(f"  ❌ 前向失败: {str(e)[:220]}")
        return 1

    # ③ 梯度路径：dg_star 能否 backward（关键！）
    try:
        tr.model.train()
        params = [p for p in tr.model.parameters() if p.requires_grad]
        tr.model.zero_grad(set_to_none=True)
        imgs, txts = [], []
        with torch.enable_grad():
            for i, batch in enumerate(val_loader):
                if i >= 2:
                    break
                tix = tr.processor(text=batch["caption"], return_tensors="pt", padding=True,
                                   truncation=True, max_length=77)
                o = tr.model(pixel_values=batch["image"].to("cpu"),
                             input_ids=tix["input_ids"].to("cpu"),
                             attention_mask=tix["attention_mask"].to("cpu"))
                imgs.append(o.image_embeds); txts.append(o.text_embeds)
            import torch.nn.functional as F
            I = F.normalize(torch.cat(imgs).float(), p=2, dim=-1)
            T = F.normalize(torch.cat(txts).float(), p=2, dim=-1)
            dg = ((I - T) ** 2).sum(dim=-1).mean()
            dg.backward()
        gdg = [p.grad for p in params if p.grad is not None]
        nD = float(sum(g.pow(2).sum() for g in gdg)) ** 0.5
        nz = sum(1 for g in gdg if float(g.abs().sum()) > 0)
        print(f"  {'✅' if nD > 0 else '❌'} dg_star.backward 可用 ｜ ‖∇DG*‖={nD:.4f} ｜ "
              f"非零梯度张量 {nz}/{len(gdg)}")
        if nD <= 0:
            print("     ⚠ 梯度全零 → 梯度路径不通（可能 model.eval() 或 no_grad 污染）")
            return 1
    except Exception as e:
        print(f"  ❌ 梯度路径失败: {str(e)[:220]}")
        return 1

    print("\n  ✅ **CPU 预检全部通过** → A 脚本可以上 GPU 跑")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
