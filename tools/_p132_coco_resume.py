# -*- coding: utf-8 -*-
r"""续跑 COCO `text_only`，**逐 seed 调用 + 失败重试**（2026-10-10）。

## 为何改

原 driver 一次传 3 个 seed 给脚本 → 中途 `CUDA error: unknown error`（间歇性）
会**丢掉同批剩余 seed**。改为**每个 seed 单独调用**，并对失败重试 2 次
（每次前 `torch.cuda.empty_cache()` 由新进程自然获得干净上下文）。

**完成即跳过**（幂等）：已有 `results.json` 的 seed 不再跑。

    python tools\_p132_coco_resume.py [--apply]
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
LOG = REPO / "outputs" / "_coco_resume.log"

JOBS = [("r8", "8"), ("r32", "32"), ("r64", "64"), ("r2", "2")]
SEEDS = {"r8": ["42", "123", "456"], "r32": ["42", "123", "456"],
         "r64": ["42", "123", "456"], "r2": ["123", "456"]}
RETRY = 2


def log(m: str) -> None:
    line = f"[{time.strftime('%m-%d %H:%M:%S')}] {m}"
    print(line, flush=True)
    with io.open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def run_one(tag: str, rank: str, seed: str) -> bool:
    outdir = f"outputs/coco_sweep_text_only/{tag}"
    cmd = [PY, "experiments/strict_freeze_control.py",
           "--dataset", "coco", "--data-dir", ".",
           "--model", "models/clip-vit-base-patch32",
           "--out-dir", outdir, "--name", f"coco_{tag}_",
           "--rank", rank, "--alpha-mult", "2", "--tags", "text_only",
           "--seeds", seed, "--epochs", "10", "--max-samples", "5000",
           "--batch-size", "64", "--skip-frozen"]
    for attempt in range(1, RETRY + 2):
        try:
            r = subprocess.run(cmd, capture_output=True, text=True,
                               encoding="utf-8", errors="replace",
                               timeout=90 * 60, cwd=str(REPO))
        except subprocess.TimeoutExpired:
            log(f"      ⚠ 超时（90 min）attempt {attempt}")
            continue
        if r.returncode == 0:
            return True
        err = ""
        for ln in (r.stderr or "").splitlines():
            if "Error" in ln or "error" in ln:
                err = ln.strip()[:120]
                break
        log(f"      ✗ attempt {attempt} rc={r.returncode} {err}")
        time.sleep(20)
    return False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    todo = []
    skip = 0
    for tag, rank in JOBS:
        for s in SEEDS[tag]:
            f = REPO / "outputs" / "coco_sweep_text_only" / tag / "text_only" / \
                f"seed{s}" / "results.json"
            if f.exists():
                skip += 1
            else:
                todo.append((tag, rank, s))
    print(f"=== 已有 {skip} 个 ｜ 待跑 {len(todo)} 个 ===")
    for t in todo:
        print(f"  {t[0]:<5} seed {t[2]}")
    if not a.apply:
        print("  （预演）")
        return 0

    log("=" * 60)
    log(f"续跑 COCO text_only：{len(todo)} 个（逐 seed + 重试 {RETRY}）")
    ok = bad = 0
    for tag, rank, s in todo:
        log(f"▶ {tag} seed {s}")
        if run_one(tag, rank, s):
            ok += 1
            log(f"   ✅ {tag}/{s}")
        else:
            bad += 1
            log(f"   ❌ {tag}/{s} 三次均失败")
    log(f"完成：成功 {ok} ｜ 失败 {bad}")
    log("=" * 60)

    n = len(list((REPO / "outputs" / "coco_sweep_text_only").rglob("results.json")))
    log(f"现共 {n}/11 个结果文件")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
