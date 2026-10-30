# -*- coding: utf-8 -*-
r"""云端：**隔离诊断**——为何云端 CGΔ 与本地差 10 倍（2026-10-09）。

## 已排除

| 假设 | 实测 | 结论 |
|---|---|---|
| 数据缺失 | 1000 图全在，`results.csv` 完整，**0 回退警告** | ❌ 排除 |
| `n_trainable_params` 口径不同 | 本地/云端**完全相同**（98,304 / 245,760 / 147,456） | ❌ 排除 |
| 步数不同 | 均 320 步（10 epoch × 32） | ❌ 排除 |

## 待查（本脚本逐项打印）

1. **LoRA 初始化**：`lora_B` 是否为零（论文的严格冻结前提）；
2. **实际更新的参数数**；
3. **同一 seed 42 的 CGΔ**（本地有归档：`both` seed42 = **−0.0186**）；
4. **前 3 步的 loss 轨迹**（与本地对比）；
5. **freeze 检查**：`vision_nonzero_tensors` 是否为 0。

    $env:CLOUD_PW='...'; python tools\_cloud_isolate.py
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools"))
PY = "/root/miniconda3/bin/python"
WORK = "/root/autodl-tmp/work"

SCRIPT = r'''
import os, sys, json, torch
W = "/root/autodl-tmp/work"
os.chdir(W); sys.path.insert(0, W)

print("=== 版本 ===")
import transformers, torch as T
print("  torch", T.__version__, "｜ transformers", transformers.__version__)

from src.config import ExperimentConfig, LoRAConfig, TrainConfig
from src.trainer import GapAwareTrainer
from src.dataset import create_dataloaders

torch.manual_seed(42)
cfg = ExperimentConfig(
    name="isolate_b32_both_s42",
    lora=LoRAConfig(rank=4, alpha=8, apply_to_vision=True, apply_to_text=True),
    train=TrainConfig(dataset="flickr30k", batch_size=128, num_epochs=10,
                      max_samples=5000, clip_model="models/clip-vit-base-patch32",
                      save_dir="outputs/_isolate"),
)
tr = GapAwareTrainer(cfg)
tr.device = "cuda" if torch.cuda.is_available() else "cpu"
tr.setup_model()

print("\n=== LoRA 初始化检查（严格冻结前提：B 应为 0）===")
nzB = nzA = 0
totB = totA = 0
for n, p in tr.model.named_parameters():
    if "lora_B" in n:
        totB += 1
        if p.abs().max().item() > 0:
            nzB += 1
    if "lora_A" in n:
        totA += 1
        if p.abs().max().item() > 0:
            nzA += 1
print(f"  lora_B 非零张量: {nzB}/{totB}（应为 0）")
print(f"  lora_A 非零张量: {nzA}/{totA}（应为全部）")

n_tr = sum(p.numel() for p in tr.model.parameters() if p.requires_grad)
print(f"  n_trainable = {n_tr}")

# 冻结检查
vis_nz = 0
for n, p in tr.model.named_parameters():
    if "vision_model" in n and p.requires_grad:
        vis_nz += 1
print(f"  视觉塔中 requires_grad 的张量数: {vis_nz}")

loader, val_loader, _ = create_dataloaders(
    dataset_name="flickr30k", data_dir=".", batch_size=128, max_samples=5000)
print(f"  train batches = {len(loader)} ｜ val = {len(val_loader)}")

params = [p for p in tr.model.parameters() if p.requires_grad]
opt = torch.optim.AdamW(params, lr=1e-4, weight_decay=0.01)
sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=len(loader) * 10)

print("\n=== 训练 10 epoch（前 3 步 loss 打印）===")
losses = []
for ep in range(1, 11):
    tr.model.train()
    for i, b in enumerate(loader):
        imgs = b["image"].to(tr.device)
        ii = b["input_ids"].to(tr.device)
        am = b["attention_mask"].to(tr.device)
        out = tr.model(pixel_values=imgs, input_ids=ii, attention_mask=am)
        import torch.nn.functional as F
        I = F.normalize(out.image_embeds, p=2, dim=-1)
        Tt = F.normalize(out.text_embeds, p=2, dim=-1)
        logits = I @ Tt.T
        lab = torch.arange(I.shape[0], device=tr.device)
        loss = (F.cross_entropy(logits, lab) + F.cross_entropy(logits.T, lab)) / 2
        loss.backward()
        opt.step(); sched.step(); opt.zero_grad()
        if ep == 1 and i < 3:
            print(f"    ep1 step{i}: loss={loss.item():.4f}")
        losses.append(loss.item())

# 首末 gap
def gap():
    tr.model.eval()
    with torch.no_grad():
        II, TT = [], []
        for b in val_loader:
            out = tr.model(pixel_values=b["image"].to(tr.device),
                           input_ids=b["input_ids"].to(tr.device),
                           attention_mask=b["attention_mask"].to(tr.device))
            II.append(out.image_embeds); TT.append(out.text_embeds)
        I = torch.cat(II); Tt = torch.cat(TT)
        I = F.normalize(I, p=2, dim=-1); Tt = F.normalize(Tt, p=2, dim=-1)
        return float((I.mean(0) - Tt.mean(0)).norm()), float(((I - Tt) ** 2).sum(-1).mean())

cg1, dg1 = gap()
print(f"\n=== 训练后 ===\n  CG(final)={cg1:.4f} ｜ DG*(final)={dg1:.4f}")
print(f"  loss 首/末 = {losses[0]:.4f} / {losses[-1]:.4f}")
print("  （本地 both seed42: CGΔ=−0.0186，即 final 应比 initial 小）")
'''


def main() -> int:
    from _cloud_ssh import client, run

    c = client()
    try:
        io.open(REPO / "outputs" / "_remote_iso.py", "w", encoding="utf-8",
                newline="\n").write(SCRIPT)
        sftp = c.open_sftp()
        sftp.put(str(REPO / "outputs" / "_remote_iso.py"), f"{WORK}/_iso.py")
        sftp.close()
        run(c, f"cd {WORK} && {PY} _iso.py 2>&1 | tail -30", timeout=3600)
    finally:
        c.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
