# -*- coding: utf-8 -*-
r"""排队执行补充实验（避免 GPU 争用，串行跑）。

## 包含的实验

| 实验 | 目的 | 命令要点 |
|---|---|---|
| **A. SigLIP vision_only** | 补全 SigLIP 三臂位置图谱（CLIP 已有 text_only/both/vision_only） | `siglip_experiments.py --only s6_siglip_lora_vision_only` |
| **B. 严格冻结 rank sweep（rank 4/16/32）** | 设计模式②"更低 rank 更保对齐"此前**只在 rank 8 验证过**；补 rank 维度 | `strict_freeze_control.py --rank N --tags text_only both` |

## 协议对齐

- SigLIP：5000 样本 / 10 epochs / batch 64 / 5 seeds（与已有 rig 一致）
- rank sweep：5000 样本 / 10 epochs / batch 128 / **3 seeds**（42/123/456，省时；方向判定够用）
  alpha = rank × 2（即 rank4→α8、rank16→α32、rank32→α64，保持论文的比例口径）

## 用法

    python tools\_run_extra_experiments.py            # 预演
    python tools\_run_extra_experiments.py --apply    # 执行（串行，约数小时）
"""
from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PY = r"D:\Anaconda\envs\pytorch\python.exe"

SIGLIP_JOBS = [
    (42, "s6_siglip_lora_vision_only", "seed42"),
    (123, "s6_siglip_lora_vision_only", "seed123"),
    (456, "s6_siglip_lora_vision_only", "seed456"),
    (789, "s6_siglip_lora_vision_only", "seed789"),
    (1024, "s6_siglip_lora_vision_only", "seed1024"),
]

RANK_SWEEP = [
    # 每个 rank 必须写到**独立目录**：`strict_freeze_control.py` 的"已存在则跳过"是按
    # `OUT_DIR/tag/seedN/results.json` 判断的；若三个 rank 共用同一个 OUT_DIR，
    # rank16/rank32 会直接读到 rank4 的结果并"跳过"，**数据互相污染且不报错**。
    (4, ["text_only", "both"], "outputs/strict_freeze_rank/r4"),
    (16, ["text_only", "both"], "outputs/strict_freeze_rank/r16"),
    (32, ["text_only", "both"], "outputs/strict_freeze_rank/r32"),
]
SWEEP_SEEDS = ["42", "123", "456"]


def run(cmd: list[str], label: str) -> bool:
    t0 = time.time()
    print(f"\n{'='*70}\n▶ {label}\n  {' '.join(cmd[-8:])}\n{'='*70}")
    r = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    keep = [l for l in (r.stdout or "").splitlines()
            if any(k in l for k in ("strict]", "done]", "✅", "❌", "strict 冻结", "总耗时", "total "))]
    for l in keep[-6:]:
        print("  " + l.strip()[:150])
    print(f"  ⏱ {time.time()-t0:.0f}s ｜ 退出码 {r.returncode}")
    if r.returncode != 0:
        for l in (r.stderr or "").strip().splitlines()[-5:]:
            print("  stderr: " + l[:150])
    return r.returncode == 0


def main() -> int:
    apply = "--apply" in sys.argv
    n = len(SIGLIP_JOBS) + len(RANK_SWEEP) * len(SWEEP_SEEDS)
    print(f"共 {n} 个作业（串行）。约：SigLIP vision_only 5×~1h/5、rank sweep 3 rank × 3 seed × 2 臂")
    if not apply:
        for seed, only, _ in SIGLIP_JOBS:
            print(f"  [SigLIP] seed={seed} only={only}")
        for rank, tags, out in RANK_SWEEP:
            print(f"  [rank={rank}] tags={tags} seeds={SWEEP_SEEDS} out={out}")
        print("\n（预演，加 --apply 执行）")
        return 0

    ok = 0
    for seed, only, sub in SIGLIP_JOBS:
        cmd = [PY, "experiments/siglip_experiments.py", "--strict-freeze", "--seed", str(seed),
               "--only", only, "--max_samples", "5000", "--epochs", "10", "--batch_size", "64",
               "--skip_full_ft", "--data_dir", ".", "--outputs_dir",
               f"outputs/siglip_strict/{sub}"]
        if run(cmd, f"SigLIP vision_only seed={seed}"):
            ok += 1

    for rank, tags, out in RANK_SWEEP:
        cmd = [PY, "experiments/strict_freeze_control.py", "--rank", str(rank),
               "--tags", *tags, "--seeds", *SWEEP_SEEDS, "--skip-frozen",
               "--epochs", "10", "--max-samples", "5000", "--batch-size", "128",
               "--out-dir", out]
        if run(cmd, f"rank sweep rank={rank} tags={tags}"):
            ok += 1

    print(f"\n完成 {ok}/{n} 个作业")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
