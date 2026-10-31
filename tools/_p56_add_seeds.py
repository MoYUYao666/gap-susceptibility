# -*- coding: utf-8 -*-
r"""风险 #1：给严格冻结对照**补 seed**（2026-10-08）。

## 为什么要补

审稿人最直接的一击：**"你三个骨干的结论各来自 1 个 seed"**。

| 骨干 | 现有 seed | 需补 |
|---|---|---|
| CLIP B/32 @ r8 | **5** ✅ | — |
| CLIP B/32 @ r4 | 1 | **+2** |
| CLIP B/16 @ r4 | 1 | **+2** |
| OpenCLIP B/32 @ r4 | 1 | **+2** |

**共 6 个配置 × 2 seed = 12 run**（每 run 约 10–20 min；`both` 臂较慢）→ **约 4 h**。

## 口径（**与原 run 完全一致**，不得改动任何参数）

`--epochs 10 --max-samples 5000 --batch-size 128 --rank 4 --alpha-mult 2`，严格冻结。

## 判据（先写明）

补 seed 后，**每个骨干的"最保护臂"不得改变**；
且给出**跨 seed 的 sd**，与已记录的 CLIP B/32（sd≈0.003）对比。
**若某骨干的排序在新 seed 下翻转 → 必须如实报告并降级该结论。**

    python tools\_p56_add_seeds.py [--apply]
"""
from __future__ import annotations

import io
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PY = r"D:\Anaconda\envs\pytorch\python.exe"
LOG = REPO / "outputs" / "_seeds_driver.log"

JOBS = [
    ("CLIP B/32 r4", "models/clip-vit-base-patch32", "outputs/strict_freeze_b32_r4", "b32_r4_"),
    ("CLIP B/16 r4", "models/clip-vit-base-patch16", "outputs/strict_freeze_b16/r4", "b16_r4_"),
    ("OpenCLIP r4", "models/openclip", "outputs/strict_freeze_oclip/r4", "oclip_r4_"),
]
NEW_SEEDS = "123 456"
ARMS = ("text_only", "both", "vision_only")


def log(msg: str) -> None:
    line = f"[{time.strftime('%m-%d %H:%M:%S')}] {msg}"
    print(line, flush=True)
    with io.open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def main() -> int:
    apply = "--apply" in sys.argv
    n = len(JOBS) * len(ARMS) * 2
    # 注意：已存在 results.json 的 run 会被跳过，故实际待跑数可能小于 n
    print("=== 补 seed：12 run（3 骨干 × 3 臂 × 2 seed）===")
    for name, _, outdir, _ in JOBS:
        print(f"  {name:<16} → {outdir}")
    print(f"  seeds: {NEW_SEEDS} ｜ 计划 {n} run（**已完成的会被跳过**）")
    print("  跑完自动接：完整 Γ_m 测量（tools/_p58_gamma_clip.py）")
    print(f"  日志: {LOG.relative_to(REPO)}")
    if not apply:
        print("  （预演；加 --apply 实跑）")
        return 0

    log("=" * 66)
    log(f"补 seed 启动（{n} run）")
    ok = fail = 0
    for name, model, outdir, prefix in JOBS:
        for arm in ARMS:
            cmd = [PY, "experiments/strict_freeze_control.py",
                   "--model", model, "--out-dir", outdir, "--name", prefix,
                   "--rank", "4", "--alpha-mult", "2", "--tags", arm,
                   "--seeds", *NEW_SEEDS.split(),
                   "--epochs", "10", "--max-samples", "5000",
                   "--batch-size", "64", "--skip-frozen"]   # 本地共享显存约束：128->64（已记录偏离）
            log(f"▶ {name} / {arm}")
            try:
                r = subprocess.run(cmd, capture_output=True, text=True,
                                   encoding="utf-8", errors="replace",
                                   timeout=3 * 3600, cwd=str(REPO))
                if r.returncode == 0:
                    ok += 1
                    log("   ✅ rc=0")
                else:
                    fail += 1
                    err = next((l for l in (r.stderr or "").splitlines() if "Error" in l), "")
                    log(f"   ❌ rc={r.returncode} {err[:130]}")
            except subprocess.TimeoutExpired:
                fail += 1
                log("   ⚠ 超时（3 h）")
    log(f"补 seed 结束：成功 {ok} ｜ 失败 {fail}")

    # **自动接 `Γ_m` 完整测量**（操作者选 A：等它出来再定论文口径）
    log("─" * 66)
    log("▶ 接：Γ_m 完整测量（CLIP 三臂，含 cos）")
    try:
        r = subprocess.run([PY, "tools/_p58_gamma_clip.py", "--apply"],
                           capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=3600, cwd=str(REPO))
        for ln in (r.stdout or "").splitlines():
            if any(t in ln for t in ("Γ_v", "Γ_t", "已写", "‖∇")):
                log("   | " + ln.strip()[:150])
        log(f"   Γ_m 测量 rc={r.returncode}")
    except subprocess.TimeoutExpired:
        log("   ⚠ Γ_m 测量超时（1 h）")
    log("=" * 66)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
