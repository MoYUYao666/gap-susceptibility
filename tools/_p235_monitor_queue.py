# -*- coding: utf-8 -*-
r"""监控决策实验的**数据生成**：逐 epoch 评测 (val_loss, τ, top1_50k)（2026-10-12）。

## 为什么

补"监控器决策"的真实验，需要逐 epoch 的 **val_loss**（现有归档缺），
才能比较「按 τ 停 vs 按 val_loss 停 vs 按 top-1 停」。

**逐 epoch 权重已存盘**（`epoch{N}.pt`），故只需 **eval-only**（无训练）。

## 目标（λ_reg=0 = 纯 LoRA = 论文协议）

| 配置 | seed | 待评测 epoch |
|---|---|---|
| `lr0.0` | 42 | 4, 6, 7, 8, 9（1/2/3/5/10 已有） |
| `lr0.0` | 123 | 1–10（全缺） |
| `lr0.0` | 456 | 1–10（全缺） |

共 **25 个** epoch。每个调用 `tools/train_class_aligned.py --eval-only --epoch N`，
产出 `eval_epoch{N}.json`（含 `tau_final` / `top1_50k` / `val_loss`）。

**每个 epoch 用独立子进程**（避免长跑内存泄漏），失败重试 2 次。

    python tools\_p235_monitor_queue.py [--apply]
"""
from __future__ import annotations

import argparse
import glob
import io
import json
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PY = sys.executable
LOG = REPO / "outputs" / "_monitor_queue.log"
ROOT = REPO / "outputs" / "a1_class_aligned"
RETRY = 2

RUNS = [("0.0", 42), ("0.0", 123), ("0.0", 456)]
EPOCHS = list(range(1, 11))


def log(m: str) -> None:
    line = f"[{time.strftime('%m-%d %H:%M:%S')}] {m}"
    print(line, flush=True)
    with io.open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def out_path(lam: str, seed: int, ep: int) -> Path:
    return ROOT / f"lr{lam}" / f"seed{seed}" / f"eval_epoch{ep}.json"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args()

    todo = []
    for lam, seed in RUNS:
        for ep in EPOCHS:
            p = out_path(lam, seed, ep)
            if not p.exists():
                ck = ROOT / f"lr{lam}" / f"seed{seed}" / f"epoch{ep}.pt"
                if ck.exists():
                    todo.append((lam, seed, ep))
                else:
                    print(f"  🔴 缺权重: {ck.relative_to(REPO)}")
    if a.limit:
        todo = todo[:a.limit]

    print("=" * 84)
    print(f"待评测: {len(todo)} 个 epoch × (50k top-1 + val_loss + τ)")
    print("=" * 84)
    for lam, seed, ep in todo:
        print(f"  lr{lam}/seed{seed}/epoch{ep}")
    print(f"\n  预计 {len(todo) * 7.5 / 60:.1f} 小时")
    if not a.apply:
        print("  （预演；加 --apply 开跑）")
        return 0

    log("=" * 72)
    log(f"监控决策数据生成启动：{len(todo)} 个 epoch")
    ok = fail = 0
    t0 = time.time()
    for i, (lam, seed, ep) in enumerate(todo, 1):
        cmd = [PY, "tools/train_class_aligned.py",
               "--lambda-reg", lam, "--seed", str(seed), "--epochs", "10",
               "--eval-only", "--epoch", str(ep)]
        done = False
        for attempt in range(1, RETRY + 2):
            t1 = time.time()
            try:
                r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                                   errors="replace", timeout=1800, cwd=str(REPO))
            except subprocess.TimeoutExpired:
                log(f"  [{i}/{len(todo)}] ⚠ 超时 lr{lam}/s{seed}/ep{ep} attempt {attempt}")
                continue
            if r.returncode == 0 and out_path(lam, seed, ep).exists():
                d = json.loads(io.open(out_path(lam, seed, ep), encoding="utf-8").read())
                log(f"  [{i}/{len(todo)}] ✅ lr{lam}/s{seed}/ep{ep} "
                    f"τ={d['tau_final']:.4f} top1_50k={d['top1_50k']:.2f} "
                    f"val_loss={d['val_loss']:.4f} ({time.time() - t1:.0f}s)")
                done = True
                break
            tail = [l for l in (r.stderr or "").splitlines() if l.strip()][-1:] or [""]
            log(f"  [{i}/{len(todo)}] ✗ lr{lam}/s{seed}/ep{ep} rc={r.returncode} "
                f"{tail[0][:90]}")
            time.sleep(15)
        ok += 1 if done else 0
        fail += 0 if done else 1

    log(f"完成：成功 {ok} ｜ 失败 {fail} ｜ 耗时 {(time.time() - t0) / 60:.1f} 分钟")
    # 汇总
    for lam, seed in RUNS:
        have = sum(1 for ep in EPOCHS if out_path(lam, seed, ep).exists())
        log(f"  lr{lam}/seed{seed}: {have}/10 epoch 已评测")
    log("=" * 72)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
