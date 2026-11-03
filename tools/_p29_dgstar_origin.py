# -*- coding: utf-8 -*-
r"""判决性测试：`setup_model()` 后**不训练**测 DG\*，看是否等于 frozen 基线（2026-10-08）。

## 要回答什么

实测差异：**归档 v1_both_r8 起始 DG\\* = 1.4767**，而**我的 trainer 基座 run 起始 = 1.88**。

**逻辑**：LoRA 若 `lora_B` 为零初始化，则注入后模型**输出与 frozen 完全一致**，
故 DG\* 起始值应等于 frozen 基线（≈1.48）。
**我的却是 1.88 → 说明注入或初始化有偏差。**

## 测三件事

1. `setup_model()` 后立即测 DG\*（**未训练**）→ 期望 ≈ 归档的 1.4767；
2. 检查 `lora_B` 是否全零、`lora_A` 的初始化分布；
3. 与**纯 frozen 模型**（无 LoRA）测得的 DG\* 对比。

**判据**：若三者的 DG\* 不一致 → 定位到具体环节；若一致 → 差异在别处（数据/评估）。

    python tools\_p29_dgstar_origin.py
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
    from transformers import CLIPModel, CLIPProcessor

    torch.manual_seed(42)
    dev = "cuda" if torch.cuda.is_available() else "cpu"

    # ① 纯 frozen 模型（无 LoRA）的 DG*
    print("=== ① 纯 frozen 模型（无 LoRA 注入）===")
    fm = CLIPModel.from_pretrained(str(REPO / "models/clip-vit-base-patch32"),
                                   local_files_only=True).to(dev).eval()
    proc = CLIPProcessor.from_pretrained(str(REPO / "models/clip-vit-base-patch32"),
                                         local_files_only=True)
    _, val_loader, _ = create_dataloaders(dataset_name="flickr30k", data_dir=".",
                                          batch_size=64, max_samples=5000)
    print(f"  val loader: {len(val_loader)} 批 × batch64 ≈ {len(val_loader)*64} 样本")

    def measure(model, n_batches=32):
        import torch.nn.functional as F
        ii, tt = [], []
        with torch.no_grad():
            for k, b in enumerate(val_loader):
                if k >= n_batches:
                    break
                tx = proc(text=b["caption"], return_tensors="pt", padding=True,
                          truncation=True, max_length=77)
                o = model(pixel_values=b["image"].to(dev),
                          input_ids=tx["input_ids"].to(dev),
                          attention_mask=tx["attention_mask"].to(dev))
                ii.append(o.image_embeds); tt.append(o.text_embeds)
        I = F.normalize(torch.cat(ii).float(), p=2, dim=-1)
        T = F.normalize(torch.cat(tt).float(), p=2, dim=-1)
        return float(((I - T) ** 2).sum(dim=-1).mean())

    dg_frozen = measure(fm)
    print(f"  → frozen DG* = {dg_frozen:.4f}   （归档 v1_both_r8 起始 1.4767）")

    # ② setup_model() 后（LoRA 已注入，未训练）
    print("\n=== ② LoRA 注入后、未训练 ===")
    cfg = ExperimentConfig(
        name="probe", lora=LoRAConfig(rank=8, alpha=16, apply_to_vision=True, apply_to_text=True),
        gap=GapConfig(compute_every_n_epochs=1),
        train=TrainConfig(dataset="flickr30k", batch_size=64, num_epochs=1, max_samples=5000,
                          learning_rate=1e-4, clip_model="models/clip-vit-base-patch32",
                          save_dir=str(REPO / "outputs/_probe")))
    tr = GapAwareTrainer(cfg)
    tr.device = dev
    tr.setup_model()
    dg_lora = measure(tr.model)
    print(f"  → LoRA 注入后 DG* = {dg_lora:.4f}")
    print(f"  → 与 frozen 之差 = {dg_lora - dg_frozen:+.4f}  "
          f"{'✅ 一致（B 零初始化）' if abs(dg_lora-dg_frozen) < 0.02 else '❌ 不一致 → 初始化有偏差'}")

    # ③ 检查 lora_B 是否全零
    print("\n=== ③ lora_B 初始化检查 ===")
    nz = tot = 0
    for n, p in tr.model.named_parameters():
        if "lora_B" in n:
            tot += 1
            if float(p.abs().max()) > 0:
                nz += 1
    print(f"  lora_B 张量 {tot} 个 ｜ 非零 {nz} 个 → "
          f"{'✅ 全零（标准 LoRA）' if nz == 0 else '❌ 有非零（初始化被改动）'}")
    nzA = sum(1 for n, p in tr.model.named_parameters()
              if "lora_A" in n and float(p.abs().max()) > 0)
    totA = sum(1 for n, _ in tr.model.named_parameters() if "lora_A" in n)
    print(f"  lora_A 张量 {totA} 个 ｜ 非零 {nzA} 个（应全部非零）")

    # ④ 用 trainer 自己的 _compute_dg_star_record 测一次（与我的脚本同路径）
    print("\n=== ④ trainer 的 _compute_dg_star_record（与 A 脚本同路径）===")
    tr.enable_dg_star_tracking()
    rec = tr._compute_dg_star_record(val_loader, 0)
    print(f"  → tracker 给出的 DG* = {rec.dg_star:.4f}  ｜ cg = {rec.cg:.4f}")
    print(f"  → 与 ①/② 对比：frozen {dg_frozen:.4f} ｜ lora {dg_lora:.4f} ｜ tracker {rec.dg_star:.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
