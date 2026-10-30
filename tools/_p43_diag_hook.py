# -*- coding: utf-8 -*-
r"""诊断钩子为何未取到梯度（2026-10-08）。

## 现象

钩子已加（`_p41`），A 脚本已改为读 `self._last_train_grad`（`_p42`），
但实测仍报 `2/2 个 epoch 未取到训练梯度`。

## 本脚本查三件事

1. `_capture_train_grad` 是否真的被置为 True；
2. **`self._trainable_params` 指向的是哪些张量**、其中**有 grad 的有几个**
   （怀疑：trainer 的 `_trainable_params` 与 LoRA 注入后的实际可训张量不一致）；
3. `loss.backward()` 之后、`zero_grad` 之前，**全模型**有多少张量有 grad。

    python tools\_p43_diag_hook.py
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

    cfg = ExperimentConfig(
        name="diag", lora=LoRAConfig(rank=4, alpha=8, apply_to_vision=True, apply_to_text=True),
        gap=GapConfig(compute_every_n_epochs=1),
        train=TrainConfig(dataset="flickr30k", batch_size=8, num_epochs=1, max_samples=32,
                          learning_rate=1e-4, clip_model="models/clip-vit-base-patch32",
                          save_dir=str(REPO / "outputs/_diag_hook")))
    tr = GapAwareTrainer(cfg)
    tr.device = "cpu"
    tr.setup_model()

    print("=== ① _trainable_params 是什么 ===")
    tp = getattr(tr, "_trainable_params", None)
    print(f"  _trainable_params: {type(tp).__name__} ｜ 长度 {len(tp) if tp else 0}")
    if tp:
        print(f"  其中 requires_grad=True 的: {sum(1 for p in tp if p.requires_grad)}")
        print(f"  形状前 3 个: {[tuple(p.shape) for p in tp[:3]]}")

    print("\n=== ② 全模型可训张量 ===")
    alltrain = [p for p in tr.model.parameters() if p.requires_grad]
    print(f"  可训张量: {len(alltrain)}")

    print("\n=== ③ 手动跑一步，看 backward 后谁有 grad ===")
    tr.peft_method = "lora"
    tr._current_gap_delta = 0.0
    tr.best_val_loss = float("inf")
    tr.missing_sim = None

    import torch.nn.functional as F
    from torch.optim import AdamW
    loader, _, _ = create_dataloaders(dataset_name="flickr30k", data_dir=".",
                                      batch_size=8, max_samples=32)
    opt = AdamW(alltrain, lr=1e-4)
    batch = next(iter(loader))
    out = tr.model(pixel_values=batch["image"].to("cpu"),
                   input_ids=batch["input_ids"].to("cpu"),
                   attention_mask=batch["attention_mask"].to("cpu"),
                   return_loss=False)
    I = F.normalize(out.image_embeds, p=2, dim=-1)
    T = F.normalize(out.text_embeds, p=2, dim=-1)
    loss = F.cross_entropy(tr.model.logit_scale.exp() * I @ T.T, torch.arange(I.shape[0]))
    loss.backward()
    n_all = sum(1 for p in tr.model.parameters() if p.grad is not None)
    n_train = sum(1 for p in alltrain if p.grad is not None)
    n_tp = sum(1 for p in (tp or []) if p.grad is not None)
    print(f"  backward 后：全模型有 grad 的张量 {n_all}")
    print(f"              可训张量中      {n_train} / {len(alltrain)}")
    print(f"              _trainable_params 中 {n_tp} / {len(tp) if tp else 0}")

    print("\n=== 结论 ===")
    if n_train and not n_tp:
        print("  → **`_trainable_params` 与真正的可训张量不是同一批对象**")
        print("     钩子里应改用 `[p for p in self.model.parameters() if p.requires_grad]`")
    elif not n_train:
        print("  → 可训张量本身没拿到梯度（检查 LoRA 注入）")
    else:
        print("  → 两者都有梯度；问题在钩子的触发条件或读取时机")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
