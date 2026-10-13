# -*- coding: utf-8 -*-
r"""云端：启动下载/实验，并轮询状态（2026-10-09）。

    $env:CLOUD_PW='...'; python tools\_cloud_run.py --start-models
    $env:CLOUD_PW='...'; python tools\_cloud_run.py --status
    $env:CLOUD_PW='...'; python tools\_cloud_run.py --start-seeds
    $env:CLOUD_PW='...'; python tools\_cloud_run.py --tail models
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools"))
PY = "/root/miniconda3/bin/python"
WORK = "/root/autodl-tmp/work"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--start-models", action="store_true")
    ap.add_argument("--start-seeds", action="store_true")
    ap.add_argument("--start-gamma", action="store_true")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--tail")
    ap.add_argument("--watch", type=int, default=0, help="轮询秒数")
    a = ap.parse_args()

    from _cloud_ssh import client, run

    c = client()

    def status():
        print("=== 状态 ===")
        run(c, f"du -sh {WORK}/models 2>/dev/null; ls {WORK}/models 2>/dev/null")
        run(c, f"ls {WORK}/models/*/[mp]*.safetensors {WORK}/models/*/pytorch_model.bin "
               f"2>/dev/null | head -6")
        print("  ── 进程 ──")
        run(c, "pgrep -fa '_cloud_models|_p56_add|strict_freeze' | head -4")
        run(c, f"df -h / | tail -1")

    try:
        if a.start_models:
            run(c, "pkill -f _cloud_models; sleep 2; echo killed")
            run(c, f"cd {WORK} && nohup {PY} tools/_cloud_models_fast.py "
                   f"> outputs_models.log 2>&1 & echo started")
        if a.start_seeds:
            run(c, f"cd {WORK} && nohup {PY} tools/_p56_add_seeds.py --apply "
                   f"> outputs_seeds.log 2>&1 & echo started")
        if a.start_gamma:
            run(c, f"cd {WORK} && nohup {PY} tools/_p58_gamma_clip.py --apply "
                   f"> outputs_gamma.log 2>&1 & echo started")
        if a.tail:
            run(c, f"cd {WORK} && tail -20 outputs_{a.tail}.log 2>&1")
        if a.status or a.watch:
            status()
        if a.watch:
            for i in range(a.watch // 30):
                time.sleep(30)
                print(f"\n  ── 第 {i+1} 次轮询 ──")
                run(c, f"du -sh {WORK}/models 2>/dev/null | cut -f1")
                run(c, f"tail -2 {WORK}/outputs_models.log 2>/dev/null")
    finally:
        c.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
