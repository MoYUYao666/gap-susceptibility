# -*- coding: utf-8 -*-
r"""补测 $k$ 的端点 + 继续跑今晚那批实验（2026-10-03 夜）。

## 为什么补测

`tools/_pa_remeasure_k.py` 已用 **both 臂**测出 $k = 0.0491$（论文称 0.043）——**来源终于明确**。
但**只覆盖 $r\in[4,32]$**，而论文称 $r\in[1,64]$。故补 **rank 1 与 rank 64 的 both 臂**。

## 步骤

1. **训练** both 臂 rank 1 与 rank 64（各 3 seeds，严格冻结）→ `outputs/strict_freeze_rank/{r1,r64}/both/`
2. **重测 k**（`tools/_pa_remeasure_k.py`，自动纳入新 checkpoint）→ 覆盖 $r\in[1,64]$
3. **继续跑**今晚原定的那批（`tools/_run_tonight_6.py`：SigLIP/OpenCLIP r4 + CLIP r1/r64 text_only）

**顺序**：先补测（小、快、直接服务待办），再跑大批。

    python tools\_run_k_endpoints_then_tonight.py            # 预演
    python tools\_run_k_endpoints_then_tonight.py --apply    # 执行
"""
from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PY = r"D:\Anaconda\envs\pytorch\python.exe"
SEEDS3 = ["42", "123", "456"]


def run(cmd: list[str], label: str, keep_keys: tuple[str, ...]) -> int:
    print("\n%s\n▶ %s\n%s" % ("=" * 70, label, "=" * 70), flush=True)
    r = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    for l in (r.stdout or "").splitlines():
        if any(k in l for k in keep_keys):
            print("  " + l.strip()[:150], flush=True)
    if r.returncode != 0:
        print("  ⚠ 退出码 %d" % r.returncode)
        for l in (r.stderr or "").strip().splitlines()[-4:]:
            print("    stderr: " + l[:140])
    return r.returncode


def main() -> int:
    apply = "--apply" in sys.argv
    steps = [
        ("both 臂 rank 1（补 k 起点）", [PY, "experiments/strict_freeze_control.py", "--rank", "1",
                                        "--tags", "both", "--skip-frozen", "--epochs", "10",
                                        "--max-samples", "5000", "--batch-size", "128",
                                        "--out-dir", "outputs/strict_freeze_rank/r1",
                                        "--seeds", *SEEDS3]),
        ("both 臂 rank 64（补 k 终点）", [PY, "experiments/strict_freeze_control.py", "--rank", "64",
                                         "--tags", "both", "--skip-frozen", "--epochs", "10",
                                         "--max-samples", "5000", "--batch-size", "128",
                                         "--out-dir", "outputs/strict_freeze_rank/r64",
                                         "--seeds", *SEEDS3]),
        ("重测 k（覆盖 r∈[1,64]）", [PY, "tools/_pa_remeasure_k.py", "--apply"]),
    ]
    print("步骤：")
    for name, _cmd in steps:
        print("  • %s" % name)
    print("  • 继续跑今晚那批（tools/_run_tonight_6.py --apply）")
    if not apply:
        print("\n（预演，加 --apply 执行）")
        return 0

    t0 = time.time()
    for name, cmd in steps:
        run(cmd, name, ("strict]", "done]", "rank ", "均值", "斜率", "✅", "❌", "total "))

    print("\n%s\n▶ 继续跑今晚那批\n%s" % ("=" * 70, "=" * 70), flush=True)
    r = subprocess.run([PY, "tools/_run_tonight_6.py", "--apply"], cwd=REPO, text=True,
                       encoding="utf-8", errors="replace")
    print("\n总耗时 %.1f 分钟" % ((time.time() - t0) / 60))
    return r.returncode


if __name__ == "__main__":
    raise SystemExit(main())
