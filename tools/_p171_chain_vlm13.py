# -*- coding: utf-8 -*-
r"""接力驱动：**等批次修正队列跑完 → 自动启动 VLM 13-seed**（2026-10-10 晚）。

## 操作者指令

> **"所有的跑完之后 VLM 就跑 11-13 seed"**

## 做法

**轮询** `outputs/_batchfix.log` 的完成标记（"完成：成功 N ｜ 失败 M"），
出现后**再启动** `tools/_p156_vlm_bf16_seeds.py --apply`（已扩到 13 seed）。

**判据（以日志为准，不以 rc 为准）**——本次已吃过"rc=0 但没做事"的教训。

## 为什么要接力而非直接并发

**单卡铁律**：绝不并发两个 GPU 实验。批次队列要跑 ~13 h，VLM 13-seed 约 48 min，
必须**串行**。

    python tools\_p171_chain_vlm13.py [--apply]
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
QLOG = REPO / "outputs" / "_batchfix.log"
LOG = REPO / "outputs" / "_chain_vlm13.log"
DONE_MARK = "完成：成功"
POLL_SEC = 300


def log(m: str) -> None:
    line = f"[{time.strftime('%m-%d %H:%M:%S')}] {m}"
    print(line, flush=True)
    with io.open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    print(f"=== 接力：等 {QLOG.name} 出现「{DONE_MARK}」→ 启动 VLM 13-seed ===")
    print(f"  轮询间隔 {POLL_SEC}s")
    if not a.apply:
        print("  （预演）")
        return 0

    log("=" * 62)
    log("接力启动：等批次修正队列完成")
    waited = 0
    while True:
        if QLOG.exists():
            t = io.open(QLOG, encoding="utf-8", errors="replace").read()
            if DONE_MARK in t:
                last = [l for l in t.splitlines() if DONE_MARK in l]
                log(f"检测到队列完成：{last[-1].strip()[:90]}")
                break
        time.sleep(POLL_SEC)
        waited += POLL_SEC
        if waited % 3600 == 0:
            log(f"仍在等待（已 {waited // 3600} h）")

    # 再确认没有 strict_freeze 进程在跑（防并发）
    for _ in range(30):
        o = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | "
             "Where-Object { $_.CommandLine -match 'strict_freeze' } | "
             "Measure-Object | Select-Object -ExpandProperty Count"],
            capture_output=True, text=True, encoding="utf-8", errors="replace")
        n = (o.stdout or "0").strip()
        if n in ("0", ""):
            break
        log(f"仍有 {n} 个 strict_freeze 进程，等 60s")
        time.sleep(60)

    log("▶ 启动 VLM 13-seed")
    r = subprocess.run([PY, "-u", "tools/_p156_vlm_bf16_seeds.py", "--apply"],
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace", cwd=str(REPO))
    tail = (r.stdout or "").strip().splitlines()[-12:]
    for l in tail:
        log("   " + l.strip()[:110])
    log(f"VLM 13-seed 结束：rc={r.returncode}")
    log("=" * 62)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
