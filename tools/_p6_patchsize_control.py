# -*- coding: utf-8 -*-
r"""实验 ③：**补 patch-16 骨干 + 多 rank**，加固"patch size 规律"（2026-10-07）。

## 要解决什么

论文的核心经验规律（`empirical.tex` Design Patterns）：

> "across all seven strict-freezing configurations measured, every patch-32 backbone has the text-only arm at
> the smallest gap change and every patch-16 backbone has the both-position arm there, **without exception**"

**两处软肋**：
1. **patch-16 组只有 1 个骨干**（BioCLIP，领域模型）→ 审稿人会说这是个体差异，不是 patch size 规律；
2. **7 个配置全在 rank-4 下测量** → 规律可能只在 rank-4 成立。

## 本脚本做什么

用 `experiments/strict_freeze_control.py` 的**同一协议**（全冻 + 仅放开 LoRA 的 A/B，
`vision_nonzero_tensors` 作为硬校验），在**若干骨干 × 多个 rank** 上跑三臂，检验：

| 检验 | 内容 |
|---|---|
| **P1** | 在**新增的 patch-16 骨干**上，both 位的 gap 变化是否确实最小 |
| **P2** | 该排序在 **r ∈ {4, 16, 64}** 上是否一致（排除"只在 rank-4 成立"） |
| **P3** | **方差分解**：模型身份 vs patch size 各自的贡献 |

**判据（事先写明）**：P1 成立且 P2 一致 → 规律加固；若 P1 在新增骨干上**不成立** →
**规律应降级为"在两个骨干上观察到"**（这是重要结果，必须如实报告）。

## 用法

    python tools\_p6_patchsize_control.py --backbone clip-vit-base-patch16 --ranks 4,16,64 --apply

    python tools\_p6_patchsize_control.py --dry            # 只看计划
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "experiments"))

OUT = REPO / "outputs" / "analysis" / "patchsize_control"
ARMS = {"text_only": dict(apply_to_vision=False, apply_to_text=True),
        "both":      dict(apply_to_vision=True,  apply_to_text=True),
        "vision_only": dict(apply_to_vision=True, apply_to_text=False)}
SEEDS = [42]
BATCH = 64
EPOCHS = 10
MAX_SAMPLES = 5000     # 与论文 strict-freeze 口径一致（5000 samples / 10 epochs）


def main() -> int:
    argv = sys.argv
    apply = "--apply" in argv
    dry = "--dry" in argv or not apply
    bb = argv[argv.index("--backbone") + 1] if "--backbone" in argv else "clip-vit-base-patch16"
    ranks = ([int(x) for x in argv[argv.index("--ranks") + 1].split(",")]
             if "--ranks" in argv else [4, 16, 64])
    seeds = ([int(x) for x in argv[argv.index("--seeds") + 1].split(",")]
             if "--seeds" in argv else SEEDS)
    mdir = REPO / "models" / bb

    print("=== 实验 ③：patch-size 规律的加固对照 ===")
    print(f"  骨干      : {bb}")
    print(f"  模型目录  : {mdir}  {'✅ 存在' if mdir.exists() else '❌ **不存在**'}")
    print(f"  rank      : {ranks} ｜ seeds {seeds} ｜ epochs {EPOCHS} ｜ max_samples {MAX_SAMPLES}")
    n_run = len(ARMS) * len(ranks) * len(seeds)
    print(f"  计划      : {n_run} run（{len(ARMS)} 臂 × {len(ranks)} rank × {len(seeds)} seed）")
    if not mdir.exists():
        print("\n  ❌ 模型不存在，无法开跑。请先运行 tools/_p4_download_clip_b16.py --apply")
        return 1
    if dry:
        print("\n  （预演；加 --apply 实跑）")
        return 0

    import torch
    from src.config import ExperimentConfig, LoRAConfig, TrainConfig
    from src.trainer import GapAwareTrainer
    from experiments.strict_freeze_control import strict_freeze

    dev = "cuda" if torch.cuda.is_available() else "cpu"
    OUT.mkdir(parents=True, exist_ok=True)
    recs = []
    for rank in ranks:
        for arm, flags in ARMS.items():
            for seed in seeds:
                tag = f"{bb}_r{rank}_{arm}_s{seed}"
                print(f"\n  ── {tag} ──", flush=True)
                torch.manual_seed(seed)
                lc = LoRAConfig(rank=rank, alpha=rank * 2, **flags)
                cfg = ExperimentConfig(
                    name=tag, lora=lc,
                    train=TrainConfig(dataset="flickr30k", batch_size=BATCH,
                                      num_epochs=EPOCHS, max_samples=MAX_SAMPLES,
                                      save_dir=str(OUT / tag), learning_rate=1e-4,
                                      clip_model=str(mdir)))
                tr = GapAwareTrainer(cfg)
                tr.setup_model()
                n_tr = strict_freeze(tr)
                params = [p for p in tr.model.parameters() if p.requires_grad]
                assert params, f"{tag}: 无任何可训参数"
                # 硬校验：可训参数必须只在 LoRA 的 A/B 上
                lora_ids = {id(p) for w in tr.lora_layers.values() for p in (w.lora_A, w.lora_B)}
                assert all(id(p) in lora_ids for p in params), f"{tag}: 存在非 LoRA 可训参数"

                # 训练（复用 trainer 的循环）——只取首末 gap 与有效秩
                gap0 = tr.measure_gap() if hasattr(tr, "measure_gap") else None
                tr.train()
                gap1 = tr.measure_gap() if hasattr(tr, "measure_gap") else None
                rec = dict(tag=tag, backbone=bb, rank=rank, arm=arm, seed=seed,
                           n_trainable=n_tr, gap0=gap0, gap1=gap1)
                recs.append(rec)
                print(f"     n_trainable={n_tr}  gap0={gap0}  gap1={gap1}")

    io.open(OUT / "patchsize_control.json", "w", encoding="utf-8", newline="").write(
        json.dumps({"backbone": bb, "ranks": ranks, "seeds": seeds,
                    "epochs": EPOCHS, "max_samples": MAX_SAMPLES,
                    "records": recs}, ensure_ascii=False, indent=1))
    print(f"\n  ✅ 已写 {(OUT / 'patchsize_control.json').relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
