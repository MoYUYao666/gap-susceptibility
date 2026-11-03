# -*- coding: utf-8 -*-
r"""队列 2：等 ③b（CLIP B/16）结束 → **重跑 α（`max_samples=5000`）**（2026-10-07）。

## 为什么要重跑

`tools/_p2_alpha_from_gradients.py` 首跑用 **`max_samples=2000`**，
DG\* 轨迹跨度仅 **0.0102**（归档同口径为 **0.1538**，**差 15 倍**）→ **R²_fit 低至 0.023**
→ "拟合的 α"基本是噪声 → **本轮测不出"α 能否由梯度预测"**。

**操作者指示"可以把没有的补上，重跑"** → 用**与归档同口径的 `max_samples=5000`** 重跑。

## 成本

| 项 | 值 |
|---|---|
| 每 run | 5000 样本 ÷ batch 64 ≈ **79 步/epoch** × 10 epoch × 2 次反向 |
| 单 run 实测（2000 样本） | ≈ 25 min → 5000 样本 ≈ **60 min** |
| seeds | **2**（42, 123）—— 判据只需"跨轨迹相关性"，2 条即可看出方向 |
| **合计** | **≈ 2 h** |

**判据（与首跑一致，事先写明）**：corr(α̂, α_fit) > 0.7 且 中位相对误差 < 35% 且 比值 ∈ [0.5, 2]。

    python tools\_p11_alpha_rerun_driver.py [--apply]
"""
from __future__ import annotations

import io
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PY = r"D:\Anaconda\envs\pytorch\python.exe"
LOG = REPO / "outputs" / "_alpha_rerun_driver.log"
B16_RES = REPO / "outputs" / "strict_freeze_b16" / "r4"
ALPHA_OUT = REPO / "outputs" / "theory" / "alpha_from_gradients" / "alpha_from_gradients.json"


def log(msg: str) -> None:
    line = f"[{time.strftime('%H:%M:%S')}] {msg}"
    print(line, flush=True)
    with io.open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def wait_for_b16(timeout_s: int = 2 * 3600) -> bool:
    """等 ③b 三臂各出 results.json。"""
    t0 = time.time()
    while time.time() - t0 < timeout_s:
        arms = list(B16_RES.glob("*/seed*/results.json")) if B16_RES.exists() else []
        if len(arms) >= 3:
            log(f"✅ ③b 完成（{len(arms)} 个 results.json）")
            return True
        time.sleep(60)
    log(f"⚠ ③b 等待超时（{timeout_s//60} min），继续 α 重跑（GPU 可能仍被占）")
    return False


def main() -> int:
    apply = "--apply" in sys.argv
    if not apply:
        print("  队列 2：等 ③b → α 重跑（max_samples=5000, seeds 42/123）")
        print(f"  日志: {LOG}")
        return 0
    log("=" * 66)
    log("队列 2 启动：等 ③b → α 重跑")
    wait_for_b16()

    # 备份首跑结果（保留证据，不覆盖）
    if ALPHA_OUT.exists():
        bak = ALPHA_OUT.with_name("alpha_from_gradients_maxsamp2000.json")
        if not bak.exists():
            io.open(bak, "w", encoding="utf-8", newline="").write(
                io.open(ALPHA_OUT, encoding="utf-8").read())
            log(f"  已备份首跑结果 → {bak.name}")

    log("▶ 启动 α 重跑（max_samples=5000, seeds 42,123, epochs 10, arms both）")
    cmd = [PY, "tools/_p2_alpha_from_gradients.py", "--apply",
           "--arms", "both", "--seeds", "42,123", "--epochs", "10", "--maxsamples", "5000"]
    log("   " + " ".join(cmd))
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=4 * 3600, cwd=str(REPO))
        log(f"   α 重跑结束 rc={r.returncode}")
        for ln in (r.stdout or "").splitlines()[-14:]:
            log("   | " + ln[:170])
        if r.returncode != 0:
            for ln in (r.stderr or "").splitlines()[-6:]:
                log("   ! " + ln[:170])
    except subprocess.TimeoutExpired:
        log("   ⚠ α 重跑超时（4 h）")
    log("队列 2 结束")
    log("=" * 66)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
