# -*- coding: utf-8 -*-
r"""等全部实验完成 → 自动重测 k（覆盖 r∈[1,64]）→ 打印汇总。

## 为什么这样组织

本次会话已被**电脑重启打断两次**，而长链（`_run_k_endpoints_then_tonight.py`）会整条丢失。
故拆成**幂等的小步**：实验用各自的命令跑（已完成的会跳过），本脚本只负责**收尾与汇总**：

1. 轮询四类产物直到齐全（或超时）；
2. 齐全后调用 `tools/_pa_remeasure_k.py --apply` 完成 k 的最终重测（含 r=1、64）；
3. 打印汇总（各批完成数 + k 值 + 覆盖区间）。

判据用**文件**而非进程（本机 `pwsh` 不在 Anaconda Python 的 PATH 上）。

    python tools\_monitor_and_finish.py
"""
from __future__ import annotations

import glob
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PY = r"D:\Anaconda\envs\pytorch\python.exe"

TARGETS = {
    "both r1（k 起点）": ("outputs/strict_freeze_rank/r1/both/seed*/results.json", 3),
    "both r64（k 终点）": ("outputs/strict_freeze_rank/r64/both/seed*/results.json", 3),
    "CLIP r1 text": ("outputs/strict_freeze_rank/r1/text_only/seed*/results.json", 3),
    "CLIP r64 text": ("outputs/strict_freeze_rank/r64/text_only/seed*/results.json", 3),
    "SigLIP r4": ("outputs/siglip_strict/*/s7_siglip_lora_r4_*/results.json", 10),
    "OpenCLIP r4": ("outputs/strict_freeze_openclip_rank/*/seed*/results.json", 10),
}


def counts() -> dict[str, int]:
    return {k: len(glob.glob(str(REPO / p))) for k, (p, _) in TARGETS.items()}


def main() -> int:
    t0 = time.time()
    while True:
        c = counts()
        line = "  ".join("%s=%d/%d" % (k, c[k], TARGETS[k][1]) for k in TARGETS)
        print("[%s] %d/%d  %s" % (time.strftime("%H:%M:%S"), sum(c.values()),
                                  sum(n for _, n in TARGETS.values()), line), flush=True)
        if all(c[k] >= TARGETS[k][1] for k in TARGETS):
            print("✅ 全部齐全", flush=True)
            break
        if time.time() - t0 > 12 * 3600:
            print("⚠ 超 12 小时，先做能做的汇总", flush=True)
            break
        time.sleep(180)

    print("\n" + "=" * 70 + "\n▶ 重测 k（覆盖 r∈[1,64]）\n" + "=" * 70, flush=True)
    r = subprocess.run([PY, str(REPO / "tools" / "_pa_remeasure_k.py"), "--apply"],
                       cwd=REPO, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    for l in (r.stdout or "").splitlines():
        if any(k in l for k in ("rank ", "均值", "斜率", "重测", "覆盖", "✅", "❌")):
            print("  " + l.strip()[:150], flush=True)
    if r.returncode != 0:
        for l in (r.stderr or "").strip().splitlines()[-4:]:
            print("  stderr: " + l[:150], flush=True)

    print("\n" + "=" * 70 + "\n▶ 最终进度\n" + "=" * 70, flush=True)
    for k, n in counts().items():
        print("  %-20s %d/%d" % (k, n, TARGETS[k][1]), flush=True)
    print("\n总耗时 %.1f 分钟" % ((time.time() - t0) / 60), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
