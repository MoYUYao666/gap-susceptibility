# -*- coding: utf-8 -*-
r"""task-9 GPU 链式执行器（**单进程串行**，符合项目铁律）。

## 为什么写成链

本项目的 GPU 由多人共享（`p3-downstream` / `p3-stats` / 本任务），已吃过并发的亏
（每 epoch 从 47s 拖到 250s）。本脚本：

1. **等卡**：轮询 `nvidia-smi`，直到显存占用低于阈值且**没有其它 python 计算进程**
   占用（或到 `--wait-max` 超时后放弃并**不启动**）；
2. **逐段串行**执行，任一段失败**立即停止**（不继续跑后面的，避免污染结果）；
3. 每段结束打印耗时，便于插空让卡。

## 用法（后台跑）

    python tools\_p452_gpu_chain.py --wait-max 40 --seeds 42,123 --epochs 4
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PY = r"D:\Anaconda\envs\pytorch\python.exe"
LOG = REPO / "outputs" / "analysis" / "_p452_gpu_chain.log"


def log(msg: str):
    """写日志。**显式 UTF-8**：实测不指定编码时中文会写成 mojibake
    （PowerShell 重定向默认用本地代码页，日志里出现"鍏跺畠python璁＄畻杩涚▼"这类乱码），
    而日志是要留档、要被人读的。"""
    line = f"[{time.strftime('%H:%M:%S')}] {msg}"
    print(line, flush=True)
    with open(LOG, "a", encoding="utf-8", newline="") as f:
        f.write(line + "\n")


def gpu_state():
    """返回 (显存占用 MiB, 利用率 %, 其它 python 计算进程数)。"""
    out = subprocess.run(
        ["nvidia-smi", "--query-compute-apps=pid,process_name,used_memory",
         "--format=csv,noheader"],
        capture_output=True, text=True).stdout
    other = 0
    for line in out.strip().splitlines():
        if not line.strip():
            continue
        parts = [p.strip() for p in line.split(",")]
        if len(parts) >= 2 and "python" in parts[1].lower():
            other += 1
    q = subprocess.run(
        ["nvidia-smi", "--query-gpu=memory.used,utilization.gpu",
         "--format=csv,noheader,nounits"], capture_output=True, text=True).stdout
    try:
        mem, util = [int(x.strip()) for x in q.strip().split(",")[:2]]
    except Exception:  # noqa: BLE001
        mem, util = -1, -1
    return mem, util, other


def wait_until(hhmm: str):
    """等到某个墙钟时刻（HH:MM，今天）再继续。用于遵守与他人的 GPU 排期约定。"""
    hh, mm = (int(x) for x in hhmm.split(":"))
    target = time.localtime()
    target = time.mktime((target.tm_year, target.tm_mon, target.tm_mday,
                          hh, mm, 0, 0, 0, -1))
    now = time.time()
    secs = target - now
    if secs <= 0:
        log(f"起始时间门 {hhmm} 已过（now={time.strftime('%H:%M:%S')}），立即开始")
        return
    log(f"起始时间门：等到 {hhmm}（还需 {secs / 60:.1f} min）—— 遵守与 p3-downstream 的排期约定")
    while time.time() < target:
        time.sleep(30)
    log(f"已到 {hhmm}，开始等卡")


def wait_for_gpu(wait_max_min: float, mem_threshold: int = 2500) -> bool:
    t0 = time.time()
    log(f"等卡中（阈值：显存 < {mem_threshold} MiB 且无其它 python 计算进程；"
        f"最长 {wait_max_min:.0f} min）")
    while (time.time() - t0) < wait_max_min * 60:
        mem, util, other = gpu_state()
        log(f"  gpu: mem={mem} MiB util={util}% 其它python计算进程={other}")
        if mem >= 0 and mem < mem_threshold and other == 0:
            log("  → 卡空闲，开始执行")
            return True
        time.sleep(60)
    log("  → 等卡超时，**不启动**（避免与他人并发）")
    return False


def run(stage: str, args: list[str]) -> bool:
    log(f"=== 开始：{stage} ===")
    t0 = time.time()
    p = subprocess.run([PY] + args, cwd=str(REPO), capture_output=True, text=True)
    dt = time.time() - t0
    tail = (p.stdout or "")[-4000:]
    errt = (p.stderr or "")[-2000:]
    with open(LOG, "a", encoding="utf-8", newline="") as f:
        f.write(f"\n----- {stage} stdout tail -----\n{tail}\n")
        if errt:
            f.write(f"\n----- {stage} stderr tail -----\n{errt}\n")
    ok = p.returncode == 0
    log(f"=== 结束：{stage}｜{'OK' if ok else f'FAIL rc={p.returncode}'}｜耗时 {dt / 60:.1f} min ===")
    if not ok:
        log(f"  stderr tail: {errt[-800:]}")
    return ok


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--wait-max", type=float, default=40.0, help="等卡上限（分钟）")
    ap.add_argument("--seeds", type=str, default="42,123")
    ap.add_argument("--epochs", type=int, default=4)
    ap.add_argument("--batch", type=int, default=4)
    ap.add_argument("--skip-wait", action="store_true")
    ap.add_argument("--not-before", type=str, default=None,
                    help="墙钟起始门（HH:MM）：到点前不碰卡，用于遵守他人的 GPU 排期")
    ap.add_argument("--with-adalora", action="store_true",
                    help="主实验后再跑 AdaLoRA 同预算基线（R2.4/R3.9）")
    args = ap.parse_args()
    if not args.apply:
        print("预演：--apply 实跑（会等卡后串行执行 Γ 测量 → 方案 → 校验 → 训练）")
        return 0

    LOG.parent.mkdir(parents=True, exist_ok=True)
    log("=" * 70)
    log(f"task-9 GPU 链启动｜seeds={args.seeds} epochs={args.epochs} batch={args.batch}")

    if args.not_before and not args.skip_wait:
        wait_until(args.not_before)
    if not args.skip_wait and not wait_for_gpu(args.wait_max):
        return 2

    stages = [
        ("A1 Γ 测量（3 seed）", ["tools\\_p432_gamma_blocks.py", "--apply"]),
        ("A2 显存/耗时标定", ["tools\\_p430_gpu_calib.py"]),
        ("B1 生成分配方案", ["tools\\_p438_alloc_plans.py", "--apply"]),
        ("B2 CPU 校验方案", ["tools\\_p441_validate_plans.py"]),
        ("B3 训练前逐方案断言", ["tools\\_p434_alloc_train.py", "--apply", "--verify"]),
        ("C 同预算训练（主实验）", ["tools\\_p434_alloc_train.py", "--apply",
                                  "--seeds", args.seeds, "--epochs", str(args.epochs),
                                  "--batch", str(args.batch)]),
        ("D 汇总", ["tools\\_p440_aggregate.py", "--apply"]),
    ]
    if args.with_adalora:
        # AdaLoRA 同预算基线（R2.4/R3.9）。放在主实验之后：主实验是 R2.2/R3.21 的核心，
        # 不能因为基线超时而被牺牲。若时间不够，宁可**不做**并如实说明。
        stages += [
            ("E1 AdaLoRA 搜配置（CPU）", ["tools\\_p451_baseline_adalora.py", "--search"]),
            ("E2 AdaLoRA 实测参数量", ["tools\\_p451_baseline_adalora.py", "--probe"]),
            ("E3 AdaLoRA 训练", ["tools\\_p451_baseline_adalora.py", "--apply",
                                "--seeds", args.seeds, "--epochs", str(args.epochs),
                                "--batch", str(args.batch)]),
            ("D2 重新汇总（含 AdaLoRA）", ["tools\\_p440_aggregate.py", "--apply"]),
        ]
    for stage, cmd in stages:
        if not run(stage, cmd):
            log(f"链在「{stage}」停止")
            return 1
    log("全链完成")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
