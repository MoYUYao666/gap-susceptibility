# -*- coding: utf-8 -*-
r"""给执行器加"**已有同任务在跑则等它**"检测（2026-10-08 03:00）。

## 为什么

α 重跑（PID 46628）**已在跑**（旧的 α 驱动启动的）。执行器接手后：
- 判据显示 α"待跑"（结果文件仍是首跑）→ 执行器会**等 GPU 空再跑一遍** → **重复劳动 2 h**，
  而且第一次跑完的结果会被第二次**覆盖**（虽同参数，但浪费时间）。

## 修法

启动任务前，**按命令行精确匹配**当前是否有**同类实验进程**在跑：
- 有 → **不算失败，也不重复启动**，而是**轮询等它结束**（等它写出完成标志）；
- 无 → 正常启动。

**匹配用命令行**（`Get-CimInstance Win32_Process`），**不按 CPU/启动时间筛**——那是先前误杀驱动的错法。

    python tools\_p20_skip_running.py [--apply]
"""
from __future__ import annotations

import ast
import io
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "tools" / "_p20_serial_executor.py"

HELPER = '''

def running_pids(pattern: str) -> list[int]:
    """按**命令行内容**找正在跑的 python 进程（不按 CPU/启动时间筛）。"""
    try:
        r = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "Get-CimInstance Win32_Process -Filter \\"Name='python.exe'\\" | "
             "ForEach-Object { \\"$($_.ProcessId)|$($_.CommandLine)\\" }"],
            capture_output=True, text=True, timeout=40)
    except Exception:
        return []
    out = []
    for ln in (r.stdout or "").splitlines():
        if "|" not in ln:
            continue
        pid, cl = ln.split("|", 1)
        if pattern in cl:
            try:
                out.append(int(pid.strip()))
            except ValueError:
                pass
    return out

'''

OLD = '''    finished, why = task_done(done)
    if finished:
        log(f"⏭ {name} 已完成（{why}）→ 跳过")
        return "skipped"
    if done.exists():
        log(f"   {name}: 输出存在但{why} → **需重跑**")'''

NEW = '''    finished, why = task_done(done)
    if finished:
        log(f"⏭ {name} 已完成（{why}）→ 跳过")
        return "skipped"
    if done.exists():
        log(f"   {name}: 输出存在但{why} → **需重跑**")

    # **已有同任务在跑**（例如旧的驱动启动的 α 重跑）→ 不重复启动，等它结束。
    # 判据用命令行里出现的**首个 python 脚本名**，避免误匹配。
    marker = next((a for a in cmd if a.endswith(".py")), "")
    if marker:
        pids = running_pids(marker.replace("\\\\", "/"))
        if pids:
            log(f"⏳ {name}: 已有同任务在跑（PID {pids}）→ 等它结束，不重复启动")
            t0 = time.time()
            while running_pids(marker.replace("\\\\", "/")):
                if time.time() - t0 > timeout:
                    log(f"⚠ {name}: 等已有任务超时（{timeout//3600} h）")
                    return "waited_timeout"
                time.sleep(60)
            log(f"✅ {name}: 已有任务已结束 → 复查完成判据")
            fin2, why2 = task_done(done)
            if fin2:
                log(f"⏭ {name} 现已完成（{why2}）→ 跳过")
                return "skipped"
            log(f"   {name}: 已有任务结束但{why2} → 本执行器启动")'''


def main() -> int:
    apply = "--apply" in sys.argv
    t = io.open(F, encoding="utf-8").read()
    if "已有同任务在跑" in t:
        print("  已加，跳过")
        return 0
    if t.count(OLD) != 1:
        print(f"  ❌ 未唯一命中（{t.count(OLD)}）")
        return 1
    t = t.replace(OLD, NEW, 1)
    anchor = "def gpu_used_mb() -> int:"
    i = t.find(anchor)
    j = t.find("\ndef ", i + 1)
    t = t[:j] + HELPER + t[j:]
    ast.parse(t)
    if not apply:
        print("  （预演）")
        return 0
    io.open(F, "w", encoding="utf-8", newline="").write(t)
    t2 = io.open(F, encoding="utf-8").read()
    assert "def running_pids(" in t2 and "已有同任务在跑" in t2
    print("  ✅ 已加：启动前检测同任务进程，有则等它结束（不重复启动）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
