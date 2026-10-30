# -*- coding: utf-8 -*-
r"""解码器 VLM 补 seed（C3）：3 新 seed × 3 臂 + seed 42 复跑校验（2026-10-10）。

## 现状（实测）

| 臂 | seed 42（400 样本 / 3 epoch） | 精度 |
|---|---|---|
| `both` | ✅ 502.4 s | **4-bit** |
| `vision_only` | ✅ 321.9 s | **4-bit** |
| `text_only` | ✅ 191.4 s | **bf16** ← **精度与其他两臂不一致** |

**→ 三臂精度不齐，且各只 1 seed，`cg_span` 分别为 0.2761 / 0.2778 / 0.3056（几乎贴在一起）。**

## 本驱动做两件事

| # | 目的 | 内容 |
|---|---|---|
| **A** | **校验我的 `--seed` 改动无副作用** | 用 `--seed 42` 复跑到 `outputs/vlm_seeds_repro/`，与归档的 `4bit/both_seed42.json` **逐值比对** |
| **B** | 补 3 个新 seed，**统一 4-bit** | seed 123 / 456 / 789 × 3 臂 = **9 run** → `outputs/vlm_seeds/` |

**配置统一为**：`--maxsamples 400 --epochs 3 --batch 4 --4bit`（与归档同配置，但 text_only 也走 4-bit）
**每 seed 一次调用**（三臂在同进程内串行，臂间 `del model` + `empty_cache`）。

**预计**：约 50 分钟（单 run 190–500 s，平均约 340 s × 12 run）。

    python tools\_p152_vlm_seed_driver.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PY = sys.executable
LOG = REPO / "outputs" / "_vlm_seeds.log"
ARMS = ("text_only", "vision_only", "both")
NEW_SEEDS = ("123", "456", "789")

CFG = ["--maxsamples", "400", "--epochs", "3", "--batch", "4", "--4bit"]


def log(m: str) -> None:
    line = f"[{time.strftime('%m-%d %H:%M:%S')}] {m}"
    print(line, flush=True)
    with io.open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def run(seed: str, outdir: str, arms: str) -> bool:
    cmd = [PY, "-u", "tools/_p47_qwen_train.py", "--apply", *CFG,
           "--seed", seed, "--arms", arms, "--outdir", outdir]
    env_note = f"seed={seed} arms={arms} → {outdir}"
    log(f"▶ {env_note}")
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=4 * 3600, cwd=str(REPO))
    if r.returncode == 0:
        return True
    err = next((l.strip() for l in (r.stderr or "").splitlines()
                if "Error" in l or "error" in l), "")
    log(f"   ❌ rc={r.returncode} {err[:130]}")
    return False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    n = len(NEW_SEEDS) * len(ARMS)
    print("=== 计划 ===")
    print(f"  A. 复跑校验：seed 42 × 3 臂 → outputs/vlm_seeds_repro/（与归档逐值比对）")
    print(f"  B. 补 seed：{', '.join(NEW_SEEDS)} × {len(ARMS)} 臂 = **{n} run** → outputs/vlm_seeds/")
    print(f"  配置：{' '.join(CFG)}")
    print(f"  日志：{LOG.relative_to(REPO)}")
    if not a.apply:
        print("  （预演）")
        return 0

    log("=" * 62)
    log(f"解码器 VLM 补 seed 启动（复跑 1 + 新跑 {n}）")

    # A. 复跑 seed 42 校验
    t0 = time.time()
    okA = run("42", "outputs/vlm_seeds_repro", ",".join(ARMS))
    log(f"   {'✅' if okA else '❌'} seed 42 复跑（{time.time()-t0:.0f}s）")

    # 比对
    arch = REPO / "outputs" / "vlm_strictfreeze" / "4bit"
    repro = REPO / "outputs" / "vlm_seeds_repro"
    print("\n=== A. 复跑 vs 归档（逐值）===")
    for arm in ("both", "vision_only"):
        f1 = arch / f"{arm}_seed42.json"
        f2 = repro / f"{arm}_seed42.json"
        if not (f1.exists() and f2.exists()):
            print(f"  {arm:<12} 文件不全，跳过")
            continue
        d1 = json.loads(io.open(f1, encoding="utf-8").read())
        d2 = json.loads(io.open(f2, encoding="utf-8").read())
        same = (d1.get("cg_span") == d2.get("cg_span")
                and d1.get("dg_span") == d2.get("dg_span"))
        print(f"  {arm:<12} 归档 cg_span={d1.get('cg_span'):.6f} dg_span={d1.get('dg_span'):.6f}")
        print(f"  {'':<12} 复跑 cg_span={d2.get('cg_span'):.6f} dg_span={d2.get('dg_span'):.6f}"
              f"  → {'✅ 逐位相同' if same else '⚠️ 不同'}")
        log(f"   repro {arm}: {'identical' if same else 'differs'}")

    # B. 新 seed
    done = fail = 0
    for seed in NEW_SEEDS:
        for arm in ARMS:
            f = REPO / "outputs" / "vlm_seeds" / f"{arm}_seed{seed}.json"
            if f.exists():
                log(f"· 已有 {f.name}，跳过")
                continue
            t1 = time.time()
            if run(seed, "outputs/vlm_seeds", arm):
                done += 1
                log(f"   ✅ {arm}/seed{seed}（{time.time()-t1:.0f}s）")
            else:
                fail += 1
    log(f"完成：成功 {done} ｜ 失败 {fail}")
    log("=" * 62)

    nfiles = len(list((REPO / "outputs" / "vlm_seeds").glob("*.json"))) \
        if (REPO / "outputs" / "vlm_seeds").exists() else 0
    log(f"outputs/vlm_seeds 现有 {nfiles}/{n} 个")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
