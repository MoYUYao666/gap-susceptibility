# -*- coding: utf-8 -*-
r"""在 **legacy 约定**下复算 $\|g_v\|$ 对 rank 的斜率 $k$（论文称 $k = 0.043$）。

## 为什么必须用 legacy 约定（**这是本次得到的一个实质发现**）

先前用**严格冻结**的 checkpoint 复算，得到 `‖g_v‖ = 0.0000`（所有 rank）。
**这不是脚本 bug，而是该量在严格冻结下退化**：

- `strict_freeze()` 把所有参数设为 `requires_grad=False`，只放开 LoRA 的 A/B；
- **text-only 臂的 LoRA 只在文本侧** → **视觉侧没有任何可训参数** → **视觉任务梯度恒为 0**。

所以 **Effective Rank Saturation（$\|g_v\|$ 对 rank 平坦）只在 legacy 约定下可测**——那时视觉塔可训。
论文的 $k=0.043$ 因此**必须用 legacy 的 checkpoint 复算**，而不是严格冻结的。

## 数据源

`outputs/flickr30k/rq1_rank{4,8,16,32,64}/best_checkpoint.pt`（legacy 约定，视觉塔可训）。

注：论文称 $r\in[1,64]$，但 legacy 只跑了 4/8/16/32/64（无 1、2），故复算覆盖 $r\in[4,64]$。

    python tools\_pa_recompute_k.py            # 预演
    python tools\_pa_recompute_k.py --apply    # 复算
"""
from __future__ import annotations

import io
import json
import math
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

CKPTS = {
    4: "outputs/flickr30k/rq1_rank4/best_checkpoint.pt",
    8: "outputs/flickr30k/rq1_rank8/best_checkpoint.pt",
    16: "outputs/flickr30k/rq1_rank16/best_checkpoint.pt",
    32: "outputs/flickr30k/rq1_rank32/best_checkpoint.pt",
    64: "outputs/flickr30k/rq1_rank64/best_checkpoint.pt",
}


def main() -> int:
    apply = "--apply" in sys.argv
    print("=== legacy 约定的 checkpoint（视觉塔可训）===")
    have = []
    for rk, p in sorted(CKPTS.items()):
        full = REPO / p
        ok = full.exists()
        print("  rank %-3d %s  %s" % (rk, "✅" if ok else "❌ 缺",
                                      f"{full.stat().st_size/1e6:.1f} MB" if ok else "—"))
        if ok:
            have.append(rk)
    print("\n  可用 rank: %s（论文称 r∈[1,64]；legacy 未跑 1、2）" % have)
    if not apply:
        print("\n  （预演，加 --apply 复算）")
        return 0

    import torch
    sys.path.insert(0, str(REPO))
    sys.path.insert(0, str(REPO / "src"))   # gap_susceptibility.py 在 src/ 下，需单独加入 path
    from src.config import ExperimentConfig, LoRAConfig, TrainConfig   # noqa: E402
    from src.trainer import GapAwareTrainer                            # noqa: E402
    from src.dataset import create_dataloaders                         # noqa: E402
    from gap_susceptibility import compute_gap_susceptibility          # noqa: E402

    PRISTINE = str(REPO / "models" / "clip-vit-base-patch32")
    DEV = "cuda" if torch.cuda.is_available() else "cpu"
    _, val_loader, _ = create_dataloaders(dataset_name="flickr30k", data_dir=".", batch_size=128,
                                          max_samples=5000)

    pts = []
    for rk in sorted(have):
        # legacy 约定：**不调用** strict_freeze()，故视觉侧保持可训 → ‖g_v‖ 可测
        cfg = ExperimentConfig(
            name="k_legacy_r%d" % rk,
            lora=LoRAConfig(rank=rk, alpha=rk * 2, apply_to_vision=False, apply_to_text=True),
            train=TrainConfig(dataset="flickr30k", clip_model=PRISTINE, device=DEV, save_dir="/tmp/k"))
        tr = GapAwareTrainer(cfg)
        tr.setup_model()
        sd = torch.load(REPO / CKPTS[rk], map_location=DEV, weights_only=False)
        tr.model.load_state_dict(sd, strict=False)

        n_trainable = sum(p.numel() for p in tr.model.parameters() if p.requires_grad)
        batch = next(iter(val_loader))
        images = batch["image"].to(DEV)
        texts = batch["caption"]
        ti = tr.processor(text=texts, return_tensors="pt", padding=True, truncation=True, max_length=77)
        out = tr.model(pixel_values=images, input_ids=ti["input_ids"].to(DEV),
                       attention_mask=ti["attention_mask"].to(DEV), return_loss=False)
        g = compute_gap_susceptibility(tr.model, out.image_embeds, out.text_embeds)
        ngv = float(g["norm_g_v"]) if isinstance(g, dict) and "norm_g_v" in g else float("nan")
        pts.append((rk, ngv))
        print("  rank %-3d 可训 %-10d ‖g_v‖ = %.4f" % (rk, n_trainable, ngv))

    xs = [math.log(r) for r, _ in pts]
    ys = [v for _, v in pts]
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    den = sum((x - mx) ** 2 for x in xs)
    k = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / den if den else float("nan")
    print("\n=== 拟合（legacy 约定）===")
    print("  rank:   %s" % [r for r, _ in pts])
    print("  ‖g_v‖:  %s" % ["%.4f" % v for _, v in pts])
    print("  斜率 k = %.4f   （论文称 0.043）" % k)
    # ⚠ 全 0 的结果**不写出文件**：一个 slope_k=0.0 的 JSON 会被误读成"复算成功"。
    # text-only 臂的 ||g_v|| 在构造上恒为 0（见 docs/K043_INVESTIGATION.md 事实 2），
    # 要复算 k 必须改用 **both 或 vision_only** 臂。
    if all(v == 0.0 for _, v in pts):
        print("\n  ⚠ 所有 rank 的 ||g_v|| 均为 0 —— 说明用错了臂（text-only 在构造上恒为 0）。")
        print("    **不写出结果文件**，以免 slope_k=0.0 被误读为复算成功。")
        print("    请改用 both 或 vision_only 臂（见 docs/K043_INVESTIGATION.md 的重测配方）。")
        return 1
    out_p = REPO / "outputs" / "analysis" / "k_recomputed_legacy.json"
    out_p.parent.mkdir(parents=True, exist_ok=True)
    io.open(out_p, "w", encoding="utf-8").write(json.dumps(
        {"convention": "legacy (backbone trainable)", "slope_k": k,
         "points": [{"rank": r, "norm_g_v": v} for r, v in pts], "paper_value": 0.043}, indent=2))
    print("  ✅ 已写出 %s" % out_p.relative_to(REPO))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
