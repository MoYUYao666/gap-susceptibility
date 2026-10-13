# -*- coding: utf-8 -*-
r"""**优先级 1**：直接验证梯度流恒等式（2026-10-05）。

## 为什么

论文的 ODE 从梯度流恒等式推出：

$$\frac{d\,DG^*}{dt} = -\eta\,\langle \nabla_\theta DG^*,\ \nabla_\theta \mathcal{L}\rangle$$

但论文只用**轨迹拟合**间接验证（$R^2=0.986$）——**从未直接检验该恒等式**。
"拟合得好" ≠ "推导对"。审稿人很可能问。

## 做法

同一次构造下取两套梯度，再做一个**真实 SGD 步**：

| 量 | 求法 |
|---|---|
| $\nabla_\theta DG^*$ | `compute_dg_star_tensor(ie, te).backward(retain_graph=True)` |
| $\nabla_\theta \mathcal{L}$ | trainer 同款 InfoNCE（双向 CE 平均，`logit_scale.exp()`） |
| **预测** $\Delta DG^*$ | $-\eta\langle\nabla DG^*,\nabla\mathcal{L}\rangle$ |
| **实测** $\Delta DG^*$ | `opt.step()` 前后 $DG^*$ 之差 |

**易错点**：$DG^*$ 必须**在含 L2 归一化的计算图内**求导。若先 `.detach()` 再算 $DG^*$，
梯度会丢掉归一化那一段，恒等式必然对不上。本脚本不 detach。

## 判据（**先写明**，避免事后找理由）

- $\cos(\text{预测},\text{实测}) > 0.9$ 且中位相对误差 $<20\%$ → **直接成立**
- 系统性偏离则**如实记录方向与幅度**（本身即结果）

## 接口（均经核实，非臆测）

- `src.trainer.GapAwareTrainer` + `strict_freeze`（照抄 `experiments/strict_freeze_control.py:85-94`）
- `src.dataset.create_dataloaders(...)` → `(train, val, test)`
- 损失：`(CE(logits_per_image) + CE(logits_per_text)) / 2`，`logits = exp(logit_scale) * ie @ te.T`

    python tools\_exp1_gradflow_identity.py [--apply]
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
os.chdir(REPO)

from src.config import ExperimentConfig, LoRAConfig, TrainConfig   # noqa: E402
from src.trainer import GapAwareTrainer, get_null_space_loss       # noqa: E402
from src.dataset import create_dataloaders                         # noqa: E402

PRISTINE = str(REPO / "models" / "clip-vit-base-patch32")
ETA = 1e-4
RANK, ALPHA_MULT = 8, 2
SEEDS = [42, 123, 456]
MAX_SAMPLES = 2000
BATCH = 64

CONFIGS = {
    "text_only":   dict(apply_to_vision=False, apply_to_text=True),
    "both":        dict(apply_to_vision=True,  apply_to_text=True),
    "vision_only": dict(apply_to_vision=True,  apply_to_text=False),
}


def strict_freeze(trainer) -> int:
    """照抄 experiments/strict_freeze_control.py:85-94 —— 全冻，仅放开 LoRA 的 A/B。"""
    for p in trainer.model.parameters():
        p.requires_grad = False
    n = 0
    for w in trainer.lora_layers.values():
        for p in (w.lora_A, w.lora_B):
            p.requires_grad = True
            n += p.numel()
    return n


def main() -> int:
    apply = "--apply" in sys.argv
    print("=== 优先级 1：梯度流恒等式直接验证 ===")
    print(f"  模型 : {Path(PRISTINE).name}")
    print(f"  配置 : {list(CONFIGS)} ｜ rank={RANK} alpha={RANK*ALPHA_MULT}")
    print(f"  eta  : {ETA} ｜ seeds {SEEDS} ｜ batch {BATCH} ｜ max_samples {MAX_SAMPLES}")
    if not apply:
        print("\n  （预演；加 --apply 实跑，需 GPU）")
        return 0

    import statistics as st

    import torch
    import torch.nn.functional as F

    dev = "cuda" if torch.cuda.is_available() else "cpu"
    records = []

    for arm, flags in CONFIGS.items():
        for seed in SEEDS:
            torch.manual_seed(seed)
            lc = LoRAConfig(rank=RANK, alpha=RANK * ALPHA_MULT, **flags)
            # 照抄 experiments/strict_freeze_control.py 的构造方式（含 name / train.dataset /
            # train.save_dir；clip_model 必须显式传，否则训练用的是默认 HF 模型）
            cfg = ExperimentConfig(
                name="gfid_%s" % arm,
                lora=lc,
                train=TrainConfig(dataset="flickr30k", batch_size=BATCH,
                                  num_epochs=1, max_samples=MAX_SAMPLES,
                                  save_dir="outputs/theory/gradflow_identity/%s" % arm,
                                  learning_rate=ETA, clip_model=PRISTINE))
            tr = GapAwareTrainer(cfg)
            tr.setup_model()
            n_tr = strict_freeze(tr)
            params = [p for p in tr.model.parameters() if p.requires_grad]
            assert params, f"{arm}: 无任何可训参数"
            lora_ids = {id(p) for w in tr.lora_layers.values() for p in (w.lora_A, w.lora_B)}
            assert all(id(p) in lora_ids for p in params), f"{arm}: 存在非 LoRA 可训参数"

            loader, _, _ = create_dataloaders(
                dataset_name="flickr30k", data_dir=".", batch_size=BATCH,
                max_samples=MAX_SAMPLES)
            batch = next(iter(loader))
            images = batch["image"].to(dev)
            inp = {k: v.to(dev) for k, v in batch.items()
                   if k in ("input_ids", "attention_mask")}

            def fwd_embeds():
                """与 src/trainer.py:400-416 同口径：取 image_embeds/text_embeds 并 L2 归一化。"""
                o = tr.model(pixel_values=images, input_ids=inp["input_ids"],
                             attention_mask=inp["attention_mask"], return_loss=False)
                return F.normalize(o.image_embeds, p=2, dim=-1), F.normalize(o.text_embeds, p=2, dim=-1)

            def dg_scalar(ie, te):
                return ((ie - te) ** 2).sum(dim=-1).mean()

            def task_loss(ie, te):
                ls = tr.model.logit_scale.exp()
                lg = ls * ie @ te.t()
                lb = torch.arange(lg.shape[0], device=dev)
                loss = (F.cross_entropy(lg, lb) + F.cross_entropy(lg.t(), lb)) / 2.0
                if tr.peft_method == "lora":
                    loss = loss + get_null_space_loss(tr.lora_layers)
                return loss

            # ① ∇DG*
            tr.model.zero_grad(set_to_none=True)
            ie, te = fwd_embeds()
            dg_t = dg_scalar(ie, te)
            dg_t.backward(retain_graph=True)
            g_align = torch.cat([p.grad.flatten() for p in params if p.grad is not None])
            dg_before = dg_t.item()

            # ② ∇L（同一张图）
            tr.model.zero_grad(set_to_none=True)
            ie2, te2 = fwd_embeds()
            task_loss(ie2, te2).backward()
            g_task = torch.cat([p.grad.flatten() for p in params if p.grad is not None])

            inner = torch.dot(g_align.detach(), g_task.detach()).item()
            pred = -ETA * inner

            # ③ 真实优化器步
            opt = torch.optim.SGD(params, lr=ETA)
            opt.step()
            with torch.no_grad():
                ie3, te3 = fwd_embeds()
                actual = dg_scalar(ie3, te3).item() - dg_before

            ratio = actual / pred if abs(pred) > 1e-15 else float("nan")
            records.append(dict(arm=arm, seed=seed, n_trainable=n_tr, dg_before=dg_before,
                                inner_product=inner, predicted_delta=pred,
                                actual_delta=actual, ratio=ratio))
            print(f"  {arm:<12} seed={seed:<5} DG*={dg_before:.4f}  pred={pred:+.3e}  "
                  f"actual={actual:+.3e}  ratio={ratio:.3f}", flush=True)

    # 汇总
    preds = [r["predicted_delta"] for r in records]
    acts = [r["actual_delta"] for r in records]
    mx, my = st.mean(preds), st.mean(acts)
    sx = sum((p - mx) ** 2 for p in preds) ** 0.5
    sy = sum((a - my) ** 2 for a in acts) ** 0.5
    cos = sum((p - mx) * (a - my) for p, a in zip(preds, acts)) / (sx * sy) if sx and sy else float("nan")
    rel = [abs(a - p) / abs(p) for p, a in zip(preds, acts) if abs(p) > 1e-15]
    med = st.median(rel) if rel else float("nan")
    ok = (cos > 0.9) and rel and (med < 0.20)
    print("\n=== 汇总 ===")
    print(f"  n={len(records)} ｜ cos(预测,实测)={cos:.4f} ｜ 中位相对误差={med:.4f}")
    print(f"  → 判据（cos>0.9 且 中位相对误差<20%）: {'✅ 成立' if ok else '⚠ 未达判据'}")

    out = REPO / "outputs" / "theory" / "gradflow_identity"
    out.mkdir(parents=True, exist_ok=True)
    (out / "identity_check.json").write_text(json.dumps(
        {"eta": ETA, "rank": RANK, "alpha": RANK * ALPHA_MULT, "seeds": SEEDS,
         "batch": BATCH, "max_samples": MAX_SAMPLES,
         "cos_pred_vs_actual": cos, "median_rel_err": med, "passed": bool(ok),
         "records": records}, indent=2), encoding="utf-8")
    print(f"  ✅ 已写 {out.relative_to(REPO)}/identity_check.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
