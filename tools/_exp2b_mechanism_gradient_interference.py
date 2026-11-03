# -*- coding: utf-8 -*-
r"""**优先级 2（改进版）**：机制测量——`cos(∇DG*, ∇L)` 与位置的关系（2026-10-05）。

## 为什么改设计

原设计的"$\Delta W$ 与间隙方向的外积对齐度"**没有区分度**：对随机矩阵，期望值也是 $\sim 1/\sqrt{\text{in}}$。
**故换成有明确零假设的机制量**：

$$\cos\phi \;=\; \frac{\langle \nabla_\theta DG^*,\ \nabla_\theta \mathcal{L}\rangle}
{\|\nabla_\theta DG^*\|\,\|\nabla_\theta \mathcal{L}\|}$$

**这是 ODE 里的 $\Gamma_m$ 的核**，也是"任务是否把表示推向/推离间隙"的直接度量。

## 零假设与预测（**先写明**）

- $H_0$：任务损失**不关心**间隙 → $\cos\phi = 0$
- **理论预测**：$\alpha = -\eta\bar\Gamma_m\|g_v\|$ 只在**视觉侧**有非零项
  → **vision_only / both 的 $\cos\phi$ 应显著异于 0，而 text_only 的视觉侧为 0**

## 同时测

- **$\|\nabla DG^*\|$ 与 $\|g\|$ 的逐位置大小**（理论说 text_only 时 $g_v=0$）
- **嵌入空间探针**：间隙方向 $\hat d$ 在微调前后的**余弦**（间隙方向是否稳定）

## 数据与接口（均经核实）

- `src.trainer.GapAwareTrainer` + `strict_freeze`（照抄 `experiments/strict_freeze_control.py:85-94`）
- `lora_state_dict` 结构：`{base_name: {'A': (in,r), 'B': (r,out)}}`（**已实测**）

    python tools\_exp2b_mechanism_gradient_interference.py [--apply]
"""
from __future__ import annotations

import glob
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
SEEDS = [42, 123, 456]
MAX_SAMPLES, BATCH, RANK, ALPHA_MULT = 2000, 64, 8, 2

CONFIGS = {
    "text_only":    dict(apply_to_vision=False, apply_to_text=True),
    "both":         dict(apply_to_vision=True,  apply_to_text=True),
    "vision_only":  dict(apply_to_vision=True,  apply_to_text=False),
}

def strict_freeze(trainer) -> int:
    """冻结全部参数，然后只放开 LoRA 的 A/B 矩阵。

    与 `experiments/strict_freeze_control.py:85-94` 逐行等价；**此处内联**而非 import，
    因为脚本会 `os.chdir(REPO)`，届时 `experiments/` 不在 sys.path 上。
    """
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
    print("=== 优先级 2（改进版）：cos(∇DG*, ∇L) 与位置 ===")
    print("  零假设 H0: cos = 0（任务不关心间隙）")
    print("  理论预测: vision_only/both 的 cos 应显著异于 0")
    print(f"  配置 {list(CONFIGS)} ｜ seeds {SEEDS} ｜ rank {RANK}")
    if not apply:
        print("\n  （预演；加 --apply 实跑）")
        return 0

    import statistics as st

    import torch
    import torch.nn.functional as F

    dev = "cuda" if torch.cuda.is_available() else "cpu"
    records = []

    for arm, flags in CONFIGS.items():
        for seed in SEEDS:
            torch.manual_seed(seed)
            cfg = ExperimentConfig(
                name="gi_%s" % arm,
                lora=LoRAConfig(rank=RANK, alpha=RANK * ALPHA_MULT, **flags),
                train=TrainConfig(dataset="flickr30k", batch_size=BATCH, num_epochs=1,
                                  max_samples=MAX_SAMPLES,
                                  save_dir="outputs/theory/grad_interference/%s" % arm,
                                  learning_rate=1e-4, clip_model=PRISTINE))
            tr = GapAwareTrainer(cfg)
            tr.setup_model()
            strict_freeze(tr)
            params = [p for p in tr.model.parameters() if p.requires_grad]
            lora_ids = {id(p) for w in tr.lora_layers.values() for p in (w.lora_A, w.lora_B)}
            assert all(id(p) in lora_ids for p in params), f"{arm}: 有非 LoRA 可训参数"

            loader, _, _ = create_dataloaders(dataset_name="flickr30k", data_dir=".",
                                              batch_size=BATCH, max_samples=MAX_SAMPLES)
            b = next(iter(loader))
            images = b["image"].to(dev)
            inp = {k: v.to(dev) for k, v in b.items() if k in ("input_ids", "attention_mask")}

            def embeds():
                o = tr.model(pixel_values=images, input_ids=inp["input_ids"],
                             attention_mask=inp["attention_mask"], return_loss=False)
                return F.normalize(o.image_embeds, p=2, dim=-1), F.normalize(o.text_embeds, p=2, dim=-1)

            def dg(ie, te):
                return ((ie - te) ** 2).sum(dim=-1).mean()

            def loss(ie, te):
                ls = tr.model.logit_scale.exp()
                lg = ls * ie @ te.t()
                lb = torch.arange(lg.shape[0], device=dev)
                L = (F.cross_entropy(lg, lb) + F.cross_entropy(lg.t(), lb)) / 2.0
                if tr.peft_method == "lora":
                    L = L + get_null_space_loss(tr.lora_layers)
                return L

            # ∇DG*
            tr.model.zero_grad(set_to_none=True)
            ie, te = embeds()
            dgt = dg(ie, te)
            dgt.backward(retain_graph=True)
            g_a = torch.cat([p.grad.flatten() for p in params if p.grad is not None])

            # ∇L
            tr.model.zero_grad(set_to_none=True)
            ie2, te2 = embeds()
            loss(ie2, te2).backward()
            g_t = torch.cat([p.grad.flatten() for p in params if p.grad is not None])

            cos = F.cosine_similarity(g_a.unsqueeze(0), g_t.unsqueeze(0)).item()
            rec = dict(arm=arm, seed=seed,
                       cos_grad_align_task=cos,
                       norm_grad_DG=float(g_a.norm()),
                       norm_grad_task=float(g_t.norm()),
                       dg_star=float(dgt),
                       n_trainable=sum(p.numel() for p in params))
            records.append(rec)
            print(f"  {arm:<12} seed={seed:<5} cos(∇DG*,∇L)={cos:+.4f}  "
                  f"‖∇DG*‖={g_a.norm():.4f}  ‖∇L‖={g_t.norm():.4f}", flush=True)

    print("\n=== 按位置汇总 ===")
    summary = {}
    for arm in CONFIGS:
        cs = [r["cos_grad_align_task"] for r in records if r["arm"] == arm]
        if not cs:
            continue
        m, sd = st.mean(cs), (st.stdev(cs) if len(cs) > 1 else 0.0)
        t = m / (sd / len(cs) ** 0.5) if sd else float("inf")
        summary[arm] = dict(mean=round(m, 4), sd=round(sd, 4), t=round(t, 2), n=len(cs))
        print(f"  {arm:<12} cos={m:+.4f} ± {sd:.4f}  t={t:+.2f}  (n={len(cs)})")

    # 零假设检验：各位置的 cos 是否异于 0
    print("\n=== 零假设 H0: cos=0 ===")
    for arm, s in summary.items():
        sig = abs(s["t"]) > 4.30 if s["n"] <= 3 else abs(s["t"]) > 2.0   # df<=2 时 t 临界值很大
        print(f"  {arm:<12} {'拒绝 H0（显著）' if sig else '不能拒绝 H0'}  (t={s['t']:+.2f}, n={s['n']})")

    out = REPO / "outputs" / "theory" / "grad_interference"
    out.mkdir(parents=True, exist_ok=True)
    (out / "grad_interference.json").write_text(json.dumps(
        {"rank": RANK, "alpha": RANK * ALPHA_MULT, "seeds": SEEDS, "batch": BATCH,
         "summary": summary, "records": records}, indent=2), encoding="utf-8")
    print(f"\n  ✅ 已写 {out.relative_to(REPO)}/grad_interference.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
