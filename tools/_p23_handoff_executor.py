# -*- coding: utf-8 -*-
r"""**交接执行器**：等 ③b `vision_only` 完成 → 替换旧执行器 → 按新队列继续（2026-10-08 07:58）。

## 为什么要替换

正在运行的执行器实例（PID 52164）用的是**启动时构建的队列**（旧代码，18 项），
**不含新插入的**：同秩对照 CLIP B/32 r4（三臂）+ 实验 A。
若不替换，它会直接跳到 COCO 12 配置（36 h），把两个更重要的任务排在最后。

## 时机

`vision_only` 实测 46 s/step、32 步/epoch、10 epoch → 约 8:40 完成。
**完成标志**：`outputs/strict_freeze_b16/r4/vision_only/seed42/results.json` 出现且非空。

## 动作顺序（**关键：先停旧执行器，再启新的，避免两个执行器抢 GPU**）

1. 轮询等 `vision_only` 的 `results.json` 出现；
2. **停掉旧执行器**（按 PID 精确停，**不按 CPU/启动时间筛**——那是先前误杀驱动的错法）；
3. 等 GPU 空闲（旧执行器的训练子进程随其父进程的 `results.json` 落盘而自然结束）；
4. **启动新执行器** → 它会跳过已完成的 1–3，从**同秩对照**开始。

## 安全

- **确认 ③b 的 `results.json` 已落盘**才停旧执行器 → **不会丢弃 2 h 的训练**；
- 每一步都追加写 `outputs/_handoff_executor.log`。

    python tools\_p23_handoff_executor.py --apply
"""
from __future__ import annotations

import io
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PY = r"D:\Anaconda\envs\pytorch\python.exe"
LOG = REPO / "outputs" / "_handoff_executor.log"
VISION_OUT = REPO / "outputs/strict_freeze_b16/r4/vision_only/seed42/results.json"


def log(msg: str) -> None:
    line = f"[{time.strftime('%m-%d %H:%M:%S')}] {msg}"
    print(line, flush=True)
    with io.open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def py_procs(pattern: str) -> list[int]:
    """按**命令行**找 python 进程（显式 UTF-8，避免 GBK 崩溃）。"""
    ps = ("[Console]::OutputEncoding = [Text.Encoding]::UTF8; "
          "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | "
          "ForEach-Object { \"$($_.ProcessId)|$($_.CommandLine)\" }")
    try:
        r = subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                           capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=60)
    except Exception:
        return []
    out = []
    for ln in (r.stdout or "").splitlines():
        if "|" in ln:
            pid, cl = ln.split("|", 1)
            if pattern in cl:
                try:
                    out.append(int(pid.strip()))
                except ValueError:
                    pass
    return out


def gpu_mb() -> int:
    try:
        r = subprocess.run(["nvidia-smi", "--query-gpu=memory.used",
                            "--format=csv,noheader,nounits"],
                           capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=20)
        return int((r.stdout or "0").strip().splitlines()[0])
    except Exception:
        return 0


def main() -> int:
    apply = "--apply" in sys.argv
    if not apply:
        print("  交接执行器：等 vision_only 落盘 → 停旧执行器 → 启新执行器")
        print(f"  监视文件: {VISION_OUT.relative_to(REPO)}")
        print(f"  日志: {LOG.relative_to(REPO)}")
        return 0

    log("=" * 70)
    log("交接执行器启动（等 ③b vision_only 落盘）")
    t0 = time.time()
    while time.time() - t0 < 3 * 3600:
        if VISION_OUT.exists() and VISION_OUT.stat().st_size > 0:
            log(f"✅ vision_only 已落盘（{VISION_OUT.stat().st_size} B）")
            break
        time.sleep(60)
    else:
        log("⚠ 等待 vision_only 超时（3 h）→ 仍继续（不丢已有产物）")

    old = py_procs("_p20_serial_executor.py")
    log(f"旧执行器 PID: {old}")
    for pid in old:
        try:
            subprocess.run(["taskkill", "/PID", str(pid), "/F"],
                           capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=30)
            log(f"   已停 PID {pid}")
        except Exception as e:
            log(f"   停 PID {pid} 失败: {e}")
    time.sleep(10)

    left = py_procs("strict_freeze_control.py")
    if left:
        log(f"⚠ 仍有训练进程 {left} → 等其结束")
        t1 = time.time()
        while py_procs("strict_freeze_control.py") and time.time() - t1 < 3600:
            time.sleep(30)
    # 等 GPU 释放
    t2 = time.time()
    while gpu_mb() > 2000 and time.time() - t2 < 1800:
        log(f"   等 GPU 释放（当前 {gpu_mb()} MB）")
        time.sleep(60)

    log(f"▶ 启动新执行器（新队列：同秩对照 ×3 → A → COCO ×12）")
    with io.open(REPO / "outputs/_serial_executor2.log", "a", encoding="utf-8") as f:
        p = subprocess.Popen([PY, "tools/_p20_serial_executor.py", "--apply"],
                             stdout=f, stderr=subprocess.STDOUT, cwd=str(REPO),
                             start_new_session=True)
    log(f"   新执行器 PID {p.pid}")
    log("交接完成")
    log("=" * 70)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
