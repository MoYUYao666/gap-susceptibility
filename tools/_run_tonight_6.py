# -*- coding: utf-8 -*-
r"""晚上跑的六个实验（2026-10-03）。

## 这六个是什么（**全部是真正缺的配置**）

操作者原选："跨骨干 rank sweep（4）+ CLIP vision_only + rank1"，
但核实发现两点，已更正：

1. **CLIP 的 vision_only 在 rank 8 已有 5 seeds**（`outputs/strict_freeze/vision_only/`，
   ΔCG +0.0049…+0.0164）→ 重跑是浪费，换成 k 曲线最缺的点；
2. **SigLIP 无 `--rank` 参数**，其 rank 由实验配置决定；既有 `s3_siglip_lora_r4` 是
   **both 位置且为 legacy 约定**（n_trainable=175,102,466）→ 不能替代，已在
   `SIGLIP_EXPERIMENTS` 新增 `s7_siglip_lora_r4_{text_only,both}`。

| # | 实验 | 目的 | 产物 |
|---|---|---|---|
| 1 | SigLIP r4 text_only | **跨骨干 rank sweep**：检验"约定改变 → rank 方向反转"是否跨骨干成立 | `outputs/siglip_strict/seed*/s7_siglip_lora_r4_text_only/` |
| 2 | SigLIP r4 both | 同上 | `…/s7_siglip_lora_r4_both/` |
| 3 | OpenCLIP r4 text_only + both | 同上 | `outputs/strict_freeze_openclip_rank/r4/` |
| 4 | CLIP r1 text_only | **补 k 曲线起点**（论文称 $r\in[1,64]$） | `outputs/strict_freeze_rank/r1/` |
| 5 | CLIP r64 text_only | **补 k 曲线终点** | `outputs/strict_freeze_rank/r64/` |

**跨骨干部分用 rank 4**：CLIP 上 r4 与 r32 的间隙差异最大（−0.0285 vs −0.0754），两点即可判方向，
且 r4 比 r32 快。

## 协议（与既有严格冻结一致）

5000 样本 / 10 epochs / 严格冻结（只训 LoRA 的 A/B 矩阵）/ alpha = rank × 2。
SigLIP 与 OpenCLIP 用 5 seeds；CLIP 的 k 两点用 3 seeds 省时。

    python tools\_run_tonight_6.py            # 预演
    python tools\_run_tonight_6.py --apply    # 执行
"""
from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PY = r"D:\Anaconda\envs\pytorch\python.exe"

SIGLIP_COMMON = ["--strict-freeze", "--max_samples", "5000", "--epochs", "10",
                 "--batch_size", "64", "--skip_full_ft", "--data_dir", "."]

# 每个作业：(标签, 命令, seeds)
JOBS: list[tuple[str, list[str], list[str]]] = [
    ("SigLIP r4 text_only",
     [PY, "experiments/siglip_experiments.py", *SIGLIP_COMMON,
      "--only", "s7_siglip_lora_r4_text_only"],
     ["42", "123", "456", "789", "1024"]),
    ("SigLIP r4 both",
     [PY, "experiments/siglip_experiments.py", *SIGLIP_COMMON,
      "--only", "s7_siglip_lora_r4_both"],
     ["42", "123", "456", "789", "1024"]),
    ("OpenCLIP r4 text_only+both",
     [PY, "experiments/strict_freeze_control.py", "--model", "models/openclip",
      "--name", "oclip_", "--rank", "4", "--tags", "text_only", "both",
      "--skip-frozen", "--epochs", "10", "--max-samples", "5000", "--batch-size", "128",
      "--out-dir", "outputs/strict_freeze_openclip_rank/r4"],
     ["42", "123", "456", "789", "1024"]),
    ("CLIP r1 text_only",
     [PY, "experiments/strict_freeze_control.py", "--rank", "1", "--tags", "text_only",
      "--skip-frozen", "--epochs", "10", "--max-samples", "5000", "--batch-size", "128",
      "--out-dir", "outputs/strict_freeze_rank/r1"],
     ["42", "123", "456"]),
    ("CLIP r64 text_only",
     [PY, "experiments/strict_freeze_control.py", "--rank", "64", "--tags", "text_only",
      "--skip-frozen", "--epochs", "10", "--max-samples", "5000", "--batch-size", "128",
      "--out-dir", "outputs/strict_freeze_rank/r64"],
     ["42", "123", "456"]),
]


def main() -> int:
    apply = "--apply" in sys.argv
    print("晚上的实验（%d 个作业）｜ 协议：5000 样本 / 10 epochs / 严格冻结\n" % len(JOBS))
    for name, cmd, seeds in JOBS:
        print("  • %s" % name)
        print("      seeds: %s" % ",".join(seeds))
    print("\n  说明：SigLIP 无 --rank，rank 由配置决定；已新增 s7_siglip_lora_r4_{text_only,both}。")
    print("  预计：SigLIP 两项 ≈ 2×1.5h ｜ OpenCLIP ≈ 1.5h ｜ CLIP r1/r64 ≈ 0.5h → 约 4–5 小时")
    if not apply:
        print("\n  （预演，加 --apply 执行）")
        return 0

    t0 = time.time()
    for name, cmd, seeds in JOBS:
        print("\n%s\n▶ %s  (seeds=%s)\n%s" % ("=" * 70, name, ",".join(seeds), "=" * 70))
        full = cmd + ["--seeds", *seeds] if "strict_freeze_control" in " ".join(cmd) else cmd
        # SigLIP 脚本按 seed 逐个调用（其 --seed 是单值）
        if "siglip_experiments" in " ".join(cmd):
            for s in seeds:
                r = subprocess.run(full + ["--seed", s], cwd=REPO, capture_output=True,
                                   text=True, encoding="utf-8", errors="replace")
                keep = [l for l in (r.stdout or "").splitlines()
                        if any(k in l for k in ("严格冻结", "done", "✅", "❌", "time="))]
                for l in keep[-3:]:
                    print("  " + l.strip()[:140])
                if r.returncode != 0:
                    print("  ⚠ seed=%s 退出码 %d" % (s, r.returncode))
                    for l in (r.stderr or "").strip().splitlines()[-3:]:
                        print("    stderr: " + l[:130])
        else:
            r = subprocess.run(full, cwd=REPO, capture_output=True, text=True,
                               encoding="utf-8", errors="replace")
            keep = [l for l in (r.stdout or "").splitlines()
                    if any(k in l for k in ("strict]", "done]", "✅", "❌", "total ", "拒绝运行"))]
            for l in keep[-6:]:
                print("  " + l.strip()[:150])
            if r.returncode != 0:
                print("  ⚠ 退出码 %d" % r.returncode)
                for l in (r.stderr or "").strip().splitlines()[-3:]:
                    print("    stderr: " + l[:130])
    print("\n总耗时 %.1f 分钟" % ((time.time() - t0) / 60))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
