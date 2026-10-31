# -*- coding: utf-8 -*-
r"""等待今晚实验全部完成，然后打印汇总（供后台长跑监控用）。

判据（不查进程，改查文件——本机 pwsh 不在 Anaconda Python 的 PATH 上）：
- SigLIP r4：10 个结果（2 tag × 5 seeds）
- OpenCLIP r4：10 个
- CLIP r1/r64：各 3 个，共 6 个
每 120 秒查一次；达到目标后再等 180 秒确认无新写入，以防收尾阶段误判。

    python tools\_wait_tonight.py
"""
from __future__ import annotations

import glob
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
TARGETS = {
    "SigLIP r4": ("outputs/siglip_strict/*/s7_siglip_lora_r4_*/results.json", 10),
    "OpenCLIP r4": ("outputs/strict_freeze_openclip_rank/*/seed*/results.json", 10),
    "CLIP r1": ("outputs/strict_freeze_rank/r1/*/seed*/results.json", 3),
    "CLIP r64": ("outputs/strict_freeze_rank/r64/*/seed*/results.json", 3),
}


def counts() -> dict[str, int]:
    return {k: len(glob.glob(str(REPO / p))) for k, (p, _) in TARGETS.items()}


def openclip_running() -> bool:
    """探测是否还有实验 python 进程（用 tasklist 而非 pwsh，避开 PATH 问题）。"""
    try:
        r = subprocess.run(["tasklist", "/FI", "IMAGENAME eq python.exe", "/FO", "CSV"],
                           capture_output=True, text=True, timeout=30)
        return r.stdout.count("python.exe") > 0
    except Exception:
        return True


def main() -> int:
    t0 = time.time()
    goal = {k: n for k, (_, n) in TARGETS.items()}
    while True:
        c = counts()
        done = sum(c[k] for k in c)
        total = sum(goal.values())
        print("[%s] %d/%d  %s" % (time.strftime("%H:%M:%S"), done, total,
                                  "  ".join("%s=%d/%d" % (k, c[k], goal[k]) for k in TARGETS)),
              flush=True)
        if all(c[k] >= goal[k] for k in TARGETS):
            print("目标达成，等 180s 确认收尾...", flush=True)
            time.sleep(180)
            c2 = counts()
            if all(c2[k] >= goal[k] for k in TARGETS):
                print("✅ 全部完成（%d/%d）" % (sum(c2.values()), total), flush=True)
                break
        if time.time() - t0 > 10 * 3600:
            print("⚠ 超 10 小时，退出", flush=True)
            return 1
        time.sleep(120)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
