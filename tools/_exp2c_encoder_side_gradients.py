# -*- coding: utf-8 -*-
r"""**优先级 2 补测**：把梯度按**编码器侧**分解，验证理论的 $g_v = 0$ 预测（2026-10-05）。

## 为什么必须做

理论的核心断言是：**文本侧适配消除视觉梯度项**（$g_v = 0$），故扰动源消失。

但上一版测的是**整个可训参数集**的 $\cos(\nabla DG^*,\nabla\mathcal L)$，
**没有分侧**——因此无法验证 $g_v = 0$。**这正是审稿人会要求的分解。**

## 测什么（按 LoRA 所属编码器分组）

| 量 | 视觉侧 | 文本侧 |
|---|---|---|
| $\|\nabla_{\theta_v} DG^*\|$ | ? | — |
| $\|g_v\|$（任务梯度） | ? | — |
| $\|g_t\|$ | — | ? |
| $\cos\phi_v$ / $\cos\phi_t$ | ? | ? |

## 理论预测（**先写明**）

| 位置 | 预测 |
|---|---|
| `text_only` | $g_v = 0$（视觉侧无任务梯度），$\|g_t\| > 0$ |
| `vision_only` | $g_t = 0$，$\|g_v\| > 0$ |
| `both` | 两侧都非零 |

**若 $g_v$ 在 text_only 下不为 0**，则理论的"逐位置"表述需修正为
"**$g_v$ 相对被削弱**"而非"归零"——**这本身是重要发现，必须如实报告**。

## 分组键（已实测）

`lora_layers` 的键形如 `vision.encoder.layers.N...` / `text.encoder.layers.N...`。

    python tools\_exp2c_encoder_side_gradients.py [--apply]
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
SEEDS = [42, 123, 456]
MAX_SAMPLES, BATCH, RANK, ALPHA_MULT = 2000, 64, 8, 2

CONFIGS = {
    "text_only":   dict(apply_to_vision=False, apply_to_text=True),
    "both":        dict(apply_to_vision=True,  apply_to_text=True),
    "vision_only": dict(apply_to_vision=True,  apply_to_text=False),
}


def strict_freeze(trainer) -> int:
    """全冻，仅放开 LoRA A/B（等价 `experiments/strict_freeze_control.py:85-94`）。"""
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
    print("=== 优先级 2 补测：按编码器侧分解梯度 ===")
    print("  理论预测: text_only → g_v = 0 ｜ vision_only → g_t = 0 ｜ both → 两侧非零")
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
                name="side_%s" % arm,
                lora=LoRAConfig(rank=RANK, alpha=RANK * ALPHA_MULT, **flags),
                train=TrainConfig(dataset="flickr30k", batch_size=BATCH, num_epochs=1,
                                  max_samples=MAX_SAMPLES,
                                  save_dir="outputs/theory/encoder_side/%s" % arm,
                                  learning_rate=1e-4, clip_model=PRISTINE))
            tr = GapAwareTrainer(cfg)
            tr.setup_model()
            strict_freeze(tr)

            # 按 LoRA 层名分侧
            side_of: dict[int, str] = {}
            for name, w in tr.lora_layers.items():
                s = "vision" if name.startswith("vision") else ("text" if name.startswith("text") else "other")
                side_of[id(w.lora_A)] = s
                side_of[id(w.lora_B)] = s
            params = [p for p in tr.model.parameters() if p.requires_grad]
            grp = {"vision": [p for p in params if side_of.get(id(p)) == "vision"],
                   "text": [p for p in params if side_of.get(id(p)) == "text"]}
            print(f"    {arm} seed={seed}: 视觉侧可训 {sum(p.numel() for p in grp['vision'])} ｜ "
                  f"文本侧 {sum(p.numel() for p in grp['text'])}", flush=True)

            loader, _, _ = create_dataloaders(dataset_name="flickr30k", data_dir=".",
                                              batch_size=BATCH, max_samples=MAX_SAMPLES)
            b = next(iter(loader))
            images = b["image"].to(dev)
            inp = {k: v.to(dev) for k, v in b.items() if k in ("input_ids", "attention_mask")}

            def embeds():
                o = tr.model(pixel_values=images, input_ids=inp["input_ids"],
                             attention_mask=inp["attention_mask"], return_loss=False)
                return F.normalize(o.image_embeds, p=2, dim=-1), F.normalize(o.text_embeds, p=2, dim=-1)

            # ∇DG*
            tr.model.zero_grad(set_to_none=True)
            ie, te = embeds()
            ((ie - te) ** 2).sum(dim=-1).mean().backward(retain_graph=True)
            a = {s: torch.cat([p.grad.flatten() for p in ps if p.grad is not None])
                 if any(p.grad is not None for p in ps) else torch.zeros(1, device=dev)
                 for s, ps in grp.items()}

            # ∇L
            tr.model.zero_grad(set_to_none=True)
            ie2, te2 = embeds()
            ls = tr.model.logit_scale.exp()
            lg = ls * ie2 @ te2.t()
            lb = torch.arange(lg.shape[0], device=dev)
            L = (F.cross_entropy(lg, lb) + F.cross_entropy(lg.t(), lb)) / 2.0
            if tr.peft_method == "lora":
                L = L + get_null_space_loss(tr.lora_layers)
            L.backward()
            g = {s: torch.cat([p.grad.flatten() for p in ps if p.grad is not None])
                 if any(p.grad is not None for p in ps) else torch.zeros(1, device=dev)
                 for s, ps in grp.items()}

            rec = {"arm": arm, "seed": seed}
            for s in ("vision", "text"):
                na, ng = float(a[s].norm()), float(g[s].norm())
                cos = (float(F.cosine_similarity(a[s].unsqueeze(0), g[s].unsqueeze(0)))
                       if na > 0 and ng > 0 else float("nan"))
                rec[f"norm_gradDG_{s}"] = na
                rec[f"norm_g_{s}"] = ng
                rec[f"cos_phi_{s}"] = cos
                rec[f"ratio_{s}"] = (na / ng) if ng > 0 else float("nan")
            records.append(rec)
            print(f"      ‖∇DG_v‖={rec['norm_gradDG_vision']:.4f} ‖g_v‖={rec['norm_g_vision']:.4f} "
                  f"cos_phi_v={rec['cos_phi_vision']:+.4f} ｜ "
                  f"‖∇DG_t‖={rec['norm_gradDG_text']:.4f} ‖g_t‖={rec['norm_g_text']:.4f} "
                  f"cos_phi_t={rec['cos_phi_text']:+.4f}", flush=True)

    print("\n=== 按位置汇总（均值）===")
    summary = {}
    for arm in CONFIGS:
        rs = [r for r in records if r["arm"] == arm]
        if not rs:
            continue
        s = {k: round(st.mean([r[k] for r in rs]), 6) for k in rs[0] if k not in ("arm", "seed")}
        summary[arm] = s
        print(f"  {arm:<12} ‖g_vision‖={s['norm_g_vision']:.4f}  ‖g_text‖={s['norm_g_text']:.4f}"
              f"  ｜ cos_phi_v={s['cos_phi_vision']:+.4f}  cos_phi_t={s['cos_phi_text']:+.4f}")

    print("\n=== 检验理论的 $g_v = 0$ 预测 ===")
    checks = {
        "text_only_vision_zero": summary.get("text_only", {}).get("norm_g_vision", 1) < 1e-6,
        "vision_only_text_zero": summary.get("vision_only", {}).get("norm_g_text", 1) < 1e-6,
        "both_both_nonzero": (summary.get("both", {}).get("norm_g_vision", 0) > 0
                              and summary.get("both", {}).get("norm_g_text", 0) > 0),
    }
    for k, v in checks.items():
        print(f"  {k:<26} {'✅ 成立' if v else '❌ 不成立'}")
    if not checks["text_only_vision_zero"]:
        tv = summary["text_only"]["norm_g_vision"]
        tt = summary["text_only"]["norm_g_text"]
        print(f"\n  ⚠ **理论的逐位置表述需修正**：text_only 下 ‖g_v‖ = {tv:.4f} ≠ 0"
              f"（为文本侧的 {100*tv/tt:.1f}%）")
        print("     → 应表述为『文本侧适配**消除**视觉项』改为『**大幅削弱**视觉项』，或说明")
        print("        g_v=0 指的是 **∇DG\\*** 意义上的视觉项而非任务梯度 g_v。")

    out = REPO / "outputs" / "theory" / "encoder_side"
    out.mkdir(parents=True, exist_ok=True)
    (out / "encoder_side.json").write_text(json.dumps(
        {"rank": RANK, "alpha": RANK * ALPHA_MULT, "seeds": SEEDS, "batch": BATCH,
         "checks": checks, "summary": summary, "records": records}, indent=2), encoding="utf-8")
    print(f"\n  ✅ 已写 {out.relative_to(REPO)}/encoder_side.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
