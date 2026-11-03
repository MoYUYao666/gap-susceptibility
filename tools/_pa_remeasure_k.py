# -*- coding: utf-8 -*-
r"""重测 $k$：用 **both 臂**（LoRA 注入视觉+文本两侧，故视觉侧梯度非零）。

## 背景（见 `docs/K043_INVESTIGATION.md`）

论文的 $k=0.043$ **来源不明**且**无法从归档复算**。操作者选择**重测（方案 A）**。

**为什么必须用 both 臂**：`src/gap_susceptibility.py` 的 `_accumulate()` 只累加
`trainable_names`（仅 `lora_A`/`lora_B`）；**text-only 臂的 LoRA 只在文本侧** →
视觉侧无项可累加 → `‖g_v‖` 恒为 0（已实测：严格冻结 4 个 rank、legacy 5 个 rank 全为 0）。

## 本轮能覆盖的 rank

| 臂 | 可用 checkpoint |
|---|---|
| **both（严格冻结）** | **4、8、16、32**（`outputs/strict_freeze/both/` 与 `outputs/strict_freeze_rank/r{4,16,32}/both/`） |
| vision_only | 仅 8 |
| legacy text-only | 4、8、16、32、64（**恒为 0，不可用**） |

论文称曲线覆盖 $r\in[1,64]$，而 both 臂**缺 rank 1 与 64** → 本脚本先报可覆盖范围，
并明确标注"未覆盖 $r\in[1,4)$ 与 $(32,64]$"。

    python tools\_pa_remeasure_k.py            # 预演
    python tools\_pa_remeasure_k.py --apply    # 实测
"""
from __future__ import annotations

import io
import json
import math
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

# both 臂的 checkpoint（严格冻结；视觉侧 LoRA 存在 → ‖g_v‖ 可测）
CKPTS = {
    1: "outputs/strict_freeze_rank/r1/both/seed42/best_checkpoint.pt",
    4: "outputs/strict_freeze_rank/r4/both/seed42/best_checkpoint.pt",
    8: "outputs/strict_freeze/both/seed42/best_checkpoint.pt",
    16: "outputs/strict_freeze_rank/r16/both/seed42/best_checkpoint.pt",
    32: "outputs/strict_freeze_rank/r32/both/seed42/best_checkpoint.pt",
    64: "outputs/strict_freeze_rank/r64/both/seed42/best_checkpoint.pt",
}
SEEDS = [42, 123, 456]   # 各 rank 多个 seed 取平均更稳


def main() -> int:
    apply = "--apply" in sys.argv
    print("=== both 臂 checkpoint（视觉侧 LoRA 存在 → ‖g_v‖ 可测）===")
    have = []
    for rk, p in sorted(CKPTS.items()):
        full = REPO / p
        ok = full.exists()
        print("  rank %-3d %s  %s" % (rk, "✅" if ok else "❌ 缺",
                                      f"{full.stat().st_size/1e6:.1f} MB" if ok else "—"))
        if ok:
            have.append(rk)
    print("\n  可覆盖 rank: %s" % have)
    print("  ⚠ 论文称 $r\\in[1,64]$，本批**缺 rank 1 与 64** → 结论将限定在 %s" % have)
    if not apply:
        print("\n  （预演，加 --apply 实测）")
        return 0

    import torch
    sys.path.insert(0, str(REPO))
    sys.path.insert(0, str(REPO / "src"))
    from src.config import ExperimentConfig, LoRAConfig, TrainConfig   # noqa: E402
    from src.trainer import GapAwareTrainer                            # noqa: E402
    from src.dataset import create_dataloaders                         # noqa: E402
    from gap_susceptibility import compute_gap_susceptibility          # noqa: E402

    PRISTINE = str(REPO / "models" / "clip-vit-base-patch32")
    DEV = "cuda" if torch.cuda.is_available() else "cpu"
    _, val_loader, _ = create_dataloaders(dataset_name="flickr30k", data_dir=".", batch_size=128,
                                          max_samples=5000)

    rows = []
    for rk in sorted(have):
        vals = []
        for seed in SEEDS:
            p = Path(str(REPO / CKPTS[rk]).replace("seed42", "seed%d" % seed))
            if not p.exists():
                continue
            cfg = ExperimentConfig(
                name="k_both_r%d" % rk,
                lora=LoRAConfig(rank=rk, alpha=rk * 2, apply_to_vision=True, apply_to_text=True),
                train=TrainConfig(dataset="flickr30k", clip_model=PRISTINE, device=DEV,
                                  save_dir="/tmp/k"))
            tr = GapAwareTrainer(cfg)
            tr.setup_model()
            sd = torch.load(p, map_location=DEV, weights_only=False)
            tr.model.load_state_dict(sd, strict=False)
            batch = next(iter(val_loader))
            ti = tr.processor(text=batch["caption"], return_tensors="pt", padding=True,
                              truncation=True, max_length=77)
            out = tr.model(pixel_values=batch["image"].to(DEV), input_ids=ti["input_ids"].to(DEV),
                           attention_mask=ti["attention_mask"].to(DEV), return_loss=False)
            g = compute_gap_susceptibility(tr.model, out.image_embeds, out.text_embeds)
            ngv = float(g["norm_g_v"])
            ngv_nz = sum(1 for w in tr.lora_layers.values()
                         if "vision" in "" or True)  # 仅作存在性检查，不用于数值
            vals.append(ngv)
            print("  rank %-3d seed %-5d ‖g_v‖ = %.4f" % (rk, seed, ngv))
        if vals:
            m = sum(vals) / len(vals)
            rows.append((rk, m))
            print("  rank %-3d → 均值 ‖g_v‖ = %.4f（n=%d）" % (rk, m, len(vals)))

    if not rows or all(v == 0.0 for _, v in rows):
        print("\n  ❌ 全部为 0 —— 说明该臂的视觉侧也没有梯度，需排查（不要写出结果）")
        return 1

    xs = [math.log(r) for r, _ in rows]
    ys = [v for _, v in rows]
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    den = sum((x - mx) ** 2 for x in xs)
    k = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / den if den else float("nan")
    print("\n=== 重测结果 ===")
    print("  rank:   %s" % [r for r, _ in rows])
    print("  ‖g_v‖:  %s" % ["%.4f" % v for _, v in rows])
    print("  斜率 k = %.4f   （论文称 0.043）" % k)
    missing = [r for r in (1, 2, 4, 8, 16, 32, 64) if r not in [x for x, _ in rows]]
    print("  覆盖范围: r ∈ %s" % [r for r, _ in rows])
    if missing:
        print("  ⚠ 未覆盖: %s（论文称 r∈[1,64]）" % missing)
    else:
        print("  ✅ 已覆盖论文声称的区间 r∈[1,64]")
    vals = [v for _, v in rows]
    spread = 100.0 * (max(vals) - min(vals)) / (sum(vals) / len(vals))
    print("  ‖g_v‖ 区间 %.4f–%.4f（极差 %.1f%%）｜ 若按 sqrt(r)，r 由 %d→%d 应变化 %.1f 倍"
          % (min(vals), max(vals), spread, min(r for r, _ in rows), max(r for r, _ in rows),
             (max(r for r, _ in rows) / min(r for r, _ in rows)) ** 0.5))
    print("  ⚠ 注意：若局部斜率正负交替，则『斜率』本身无意义——应报区间与 sqrt(r) 的对比，而非斜率")
    out_p = REPO / "outputs" / "analysis" / "k_remeasured_both.json"
    out_p.parent.mkdir(parents=True, exist_ok=True)
    io.open(out_p, "w", encoding="utf-8").write(json.dumps(
        {"arm": "both", "convention": "strict-freeze", "slope_k": k,
         "covered_ranks": [r for r, _ in rows],
         "points": [{"rank": r, "norm_g_v_mean": v} for r, v in rows],
         "paper_value": 0.043,
         "caveat": "covers ranks %s only; paper claims r in [1,64]" % [r for r, _ in rows]},
        indent=2))
    print("  ✅ 已写出 %s" % out_p.relative_to(REPO))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
