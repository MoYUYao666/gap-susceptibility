# -*- coding: utf-8 -*-
r"""等 OpenCLIP 严格冻结跑完后，串行执行补充实验（避免 GPU 争用）。

## 为什么需要

单一 GPU（RTX 4060 Laptop 8 GB）。两批实验并行会争显存与算力，也可能 OOM。
先前用"结果文件数 >= 15"判断 OpenCLIP 完成——**不可靠**（每个 seed 完成就写一个文件，
中途就可能达到阈值）。本脚本改为**按进程判断**：OpenCLIP 的父进程消失才算跑完。

    python tools\_chain_extra_experiments.py [--apply]
"""
from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PY = r"D:\Anaconda\envs\pytorch\python.exe"
OPENCLIP_MARK = "strict_freeze_control.py --model models/openclip"


OPENCLIP_DIR = REPO / "outputs" / "strict_freeze_openclip"
EXPECTED = 15  # 3 臂 × 5 seeds
QUIET_SEC = 180  # 最近这么长时间内没有新文件写入，视为已结束


def openclip_running() -> bool:
    """OpenCLIP 是否仍在跑。

    **不查进程**（`pwsh` 不在 Anaconda Python 的 PATH 上，先前实测 subprocess 调用失败），
    改为**文件判断**：
      1) 结果文件数 < 15 → 仍在跑；
      2) 已满 15 但最近 QUIET_SEC 内仍有文件被写入 → 仍在跑（收尾阶段）。
    """
    files = list(OPENCLIP_DIR.rglob("results.json")) if OPENCLIP_DIR.exists() else []
    if len(files) < EXPECTED:
        return True
    newest = max(f.stat().st_mtime for f in files)
    return (time.time() - newest) < QUIET_SEC


def main() -> int:
    apply = "--apply" in sys.argv
    if not apply:
        print("  将等待 OpenCLIP 完成后，串行执行 tools/_run_extra_experiments.py --apply")
        print("  （预演，加 --apply 生效）")
        return 0

    print("等待 OpenCLIP 严格冻结完成（按进程判断，每 60s 查一次）...")
    t0 = time.time()
    while openclip_running():
        if time.time() - t0 > 6 * 3600:
            print("  ⚠ 等待超 6 小时，放弃")
            return 1
        time.sleep(60)
    print(f"  ✅ OpenCLIP 已结束（等待 {(time.time()-t0)/60:.1f} 分钟），开始补充实验")

    n = len(list((REPO / "outputs" / "strict_freeze_openclip").rglob("results.json"))) \
        if (REPO / "outputs" / "strict_freeze_openclip").exists() else 0
    print(f"  OpenCLIP 产出 {n} 个 results.json")

    r = subprocess.run([PY, str(REPO / "tools" / "_run_extra_experiments.py"), "--apply"],
                       cwd=REPO, text=True, encoding="utf-8", errors="replace")
    return r.returncode


if __name__ == "__main__":
    raise SystemExit(main())
