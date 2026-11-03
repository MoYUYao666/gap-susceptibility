# -*- coding: utf-8 -*-
r"""seed 升级总队列：把 1–3 seed 的实验提到 **5 seed**（2026-10-10 晚）。

## 操作者指令

> **"所有 1-3 seed 你都可以视成本来提升为 5 seed，像这个实验你提升至 7 或 9 seed 试试吧"**

## 范围（**只做"论文仍在用"的**）

| # | 组 | 现状 | 目标 | 成本 |
|---|---|---|---|---|
| 1 | `outputs/coco_sweep_text_only`（+ COCO r4 缺的） | 3 | 5 | ~22 min |
| 2 | `strict_freeze_b32_r4` × 3 臂 | 3 | 5 | ~75 min |
| 3 | `strict_freeze_oclip/r4` × 3 臂 | 3 | 5 | ~35 min |
| 4 | `outputs/adapter` × 10 组 | 3 | 5 | 待测 |
| 5 | `outputs/theory/beta_pilot` × 3 组 | 3 | 5 | 待测 |
| 6 | **`strict_freeze_b16/r4` × 3 臂** | 3 | 5 | **~489 min**（最慢，放最后） |

**不做**：`_archive_broken_*`（已归档坏数据）、`a1_class_aligned`（A1 线，另稿）、
`outputs/coco/coco_*`（旧协议，论文已声明被取代）、`outputs/` 顶层无 seed 层的旧结果。

## 纪律

- **串行**（单卡；铁律：绝不并发两个 GPU 实验）
- **幂等**：已有 `results.json` 的 (组, 臂, seed) 跳过 → 可随时中断重跑
- 每个 run 完成后追加日志；崩溃不会丢已完成的 run

    python tools\_p165_seed_upgrade_queue.py [--list] [--apply]
"""
from __future__ import annotations

import argparse
import io
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PY = sys.executable
LOG = REPO / "outputs" / "_seed_upgrade.log"
NEW_SEEDS = ["789", "1011"]

# ── 任务定义 ──
# 每项：(标签, 输出目录, 模型, 数据集, 额外参数, 臂列表)
JOBS = [
    # 1. COCO text_only（缺 r4 之外的 seed）—— 用 _p94 的口径
    ("coco_textonly_r4", "outputs/coco_sweep_text_only", None, "coco",
     ["--rank", "4", "--alpha-mult", "2"], ["text_only"]),
    # 2. CLIP B/32 r4
    ("b32_r4", "outputs/strict_freeze_b32_r4", "models/clip-vit-base-patch32", "flickr30k",
     ["--rank", "4", "--alpha-mult", "2"], ["text_only", "both", "vision_only"]),
    # 3. OpenCLIP r4
    ("oclip_r4", "outputs/strict_freeze_oclip/r4", "models/openclip-laion2b", "flickr30k",
     ["--rank", "4", "--alpha-mult", "2"], ["text_only", "both", "vision_only"]),
    # 6. CLIP B/16 r4（最慢，最后）
    ("b16_r4", "outputs/strict_freeze_b16/r4", "models/clip-vit-base-patch16", "flickr30k",
     ["--rank", "4", "--alpha-mult", "2"], ["text_only", "both", "vision_only"]),
]


def log(m: str) -> None:
    line = f"[{time.strftime('%m-%d %H:%M:%S')}] {m}"
    print(line, flush=True)
    with io.open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def exists(outdir: str, arm: str, seed: str) -> bool:
    return (REPO / outdir / arm / f"seed{seed}" / "results.json").exists()


def run(tag: str, outdir: str, model, dataset: str, extra: list, arm: str, seed: str) -> bool:
    cmd = [PY, "experiments/strict_freeze_control.py",
           "--dataset", dataset, "--data-dir", ".",
           "--out-dir", outdir, "--name", f"{tag}_",
           "--tags", arm, "--seeds", seed,
           "--epochs", "10", "--max-samples", "5000", "--batch-size", "64",
           "--skip-frozen", *extra]
    if model:
        cmd += ["--model", model]
    t0 = time.time()
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=6 * 3600, cwd=str(REPO))
    dt = time.time() - t0
    if r.returncode == 0:
        log(f"   ✅ {tag}/{arm}/seed{seed}（{dt:.0f}s）")
        return True
    err = next((l.strip() for l in (r.stderr or "").splitlines()
                if "Error" in l or "error" in l), "")
    log(f"   ❌ {tag}/{arm}/seed{seed} rc={r.returncode} {err[:120]}")
    return False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()

    todo = []
    for tag, outdir, model, dataset, extra, arms in JOBS:
        for arm in arms:
            for seed in NEW_SEEDS:
                if not exists(outdir, arm, seed):
                    todo.append((tag, outdir, model, dataset, extra, arm, seed))

    print(f"=== 队列：{len(todo)} 个 run ===")
    from collections import Counter
    c = Counter(t[0] for t in todo)
    for k, v in c.items():
        print(f"  {k:<20} {v} run")
    if a.list:
        for t in todo:
            print(f"   {t[0]:<20} {t[5]:<12} seed{t[6]}")
        return 0
    if not a.apply:
        print("  （预演；--apply 实跑）")
        return 0

    log("=" * 66)
    log(f"seed 升级队列启动：{len(todo)} run → 5 seed")
    ok = fail = 0
    for t in todo:
        tag, outdir, model, dataset, extra, arm, seed = t
        log(f"▶ {tag}/{arm}/seed{seed}")
        if run(tag, outdir, model, dataset, extra, arm, seed):
            ok += 1
        else:
            fail += 1
    log(f"完成：成功 {ok} ｜ 失败 {fail}")
    log("=" * 66)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
