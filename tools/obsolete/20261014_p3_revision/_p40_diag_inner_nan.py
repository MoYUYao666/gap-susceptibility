# -*- coding: utf-8 -*-
r"""诊断 `inner = nan`：为什么 `⟨∇DG*, ∇L⟩` 取不到值（2026-10-08）。

## 已知

实验 A 的逐 epoch 输出恒为 `inner=+nan`，而 `DG*` 本身正常
（`lr=1e-4` 下跨度 0.0817，与归档同口径对齐）。

## 我的 `capture_inner` 做了什么

```python
gL  = [p.grad.clone() for p in params if p.grad is not None]      # 训练梯度
...
dg.backward()                                                      # ∇DG*
gdg = [p.grad.clone() for p in params if p.grad is not None]
inner = sum((a*b).sum() for a, b in zip(gdg, gL))
```

**可疑点**（按可能性排序）：
1. **`gL` 为空或长度为 0** → sum 空 → 0.0（不是 nan）… 故不是这个；
2. **`gL` 与 `gdg` 含 nan**：训练损失 `loss` 在早期很大（4.15），
   且 `_train_epoch` 内可能做过 `zero_grad` → `p.grad` 为 **None**（被过滤）或**陈旧/污染**；
3. **两个列表长度不等**：我判过 `len(gL) != len(gdg)` 就返回 None → 但返回 None 时**不追加**，
   故 `inner_hist` 会是空列表而不是 nan… 而实际打印出 `nan`，说明**取到了值且为 nan**；
4. **`dg` 本身是 nan**：若模型输出含 nan（bf16 溢出），`dg.backward()` 给出 nan 梯度。

## 本脚本

在 CPU 上用极小配置复现 `capture_inner`，逐步打印
`gL` 非空数、`gdg` 非空数、各自范数、以及 `dg` 的值，定位 nan 来源。

    python tools\_p40_diag_inner_nan.py
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
    from torch.optim import AdamW

    torch.manual_seed(42)
    cfg = ExperimentConfig(
        name="diag", lora=LoRAConfig(rank=4, alpha=8, apply_to_vision=True, apply_to_text=True),
        gap=GapConfig(compute_every_n_epochs=1),
        train=TrainConfig(dataset="flickr30k", batch_size=8, num_epochs=1, max_samples=32,
                          learning_rate=1e-4, clip_model="models/clip-vit-base-patch32",
                          save_dir=str(REPO / "outputs/_diag_inner")))
    tr = GapAwareTrainer(cfg)
    tr.device = "cpu"
    tr.setup_model()
    tr.peft_method = "lora"
    tr._trainable_params = [p for p in tr.model.parameters() if p.requires_grad]
    tr._current_gap_delta = 0.0
    tr.best_val_loss = float("inf")

    train_loader, val_loader, _ = create_dataloaders(
        dataset_name="flickr30k", data_dir=".", batch_size=8, max_samples=32)
    params = tr._trainable_params
    print(f"  可训参数张量: {len(params)}")

    opt = AdamW(params, lr=1e-4)
    print("\n  === 训练 1 epoch ===")
    loss = tr._train_epoch(train_loader, opt, None, 1)
    print(f"  epoch loss = {loss:.4f}")

    # 复现 capture_inner 的每一步
    print("\n  === 训练后 p.grad 状态 ===")
    gL = [p.grad for p in params if p.grad is not None]
    print(f"  非 None 的 grad 张量: {len(gL)} / {len(params)}")
    if gL:
        nans = sum(1 for g in gL if torch.isnan(g).any())
        norms = [float(g.norm()) for g in gL[:5]]
        print(f"  含 nan 的张量: {nans}")
        print(f"  前 5 个范数: {[round(x, 4) for x in norms]}")
    else:
        print("  ⚠ 全部为 None → 说明 _train_epoch 内有 zero_grad")

    print("\n  === ∇DG* 计算 ===")
    tr.model.eval()
    tr.model.zero_grad(set_to_none=True)
    imgs, txts = [], []
    with torch.enable_grad():
        for i, batch in enumerate(val_loader):
            if i >= 2:
                break
            ti = tr.processor(text=batch["caption"], return_tensors="pt", padding=True,
                              truncation=True, max_length=77)
            o = tr.model(pixel_values=batch["image"].to("cpu"),
                         input_ids=ti["input_ids"].to("cpu"),
                         attention_mask=ti["attention_mask"].to("cpu"))
            imgs.append(o.image_embeds)
            txts.append(o.text_embeds)
        import torch.nn.functional as F
        I = F.normalize(torch.cat(imgs).float(), p=2, dim=-1)
        T = F.normalize(torch.cat(txts).float(), p=2, dim=-1)
        print(f"  I.shape={tuple(I.shape)} ｜ I 含 nan: {torch.isnan(I).any().item()}")
        print(f"  T.shape={tuple(T.shape)} ｜ T 含 nan: {torch.isnan(T).any().item()}")
        dg = ((I - T) ** 2).sum(dim=-1).mean()
        print(f"  dg = {float(dg):.6f} ｜ 含 nan: {torch.isnan(dg).item()}")
        dg.backward()
    gdg = [p.grad for p in params if p.grad is not None]
    print(f"  ∇DG* 非 None: {len(gdg)} / {len(params)}")
    if gdg:
        print(f"  含 nan: {sum(1 for g in gdg if torch.isnan(g).any())}")
        print(f"  前 5 个范数: {[round(float(g.norm()), 4) for g in gdg[:5]]}")

    print("\n  === 结论 ===")
    if not gL:
        print("  → p.grad 全为 None：`_train_epoch` 结束时梯度已被清空 → 必须在训练步内取值")
    elif any(torch.isnan(g).any() for g in gL):
        print("  → 训练梯度含 nan")
    elif gdg and any(torch.isnan(g).any() for g in gdg):
        print("  → ∇DG* 含 nan")
    else:
        print("  → 两者均正常；nan 可能来自长训练下的数值溢出（需在真实配置下复测）")

    if len(gL) == len(gdg) and gL:
        inner = float(sum((a * b).sum() for a, b in zip(gdg, gL)))
        print(f"  inner = {inner:+.6e}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
