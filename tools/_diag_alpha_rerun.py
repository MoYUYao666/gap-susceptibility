# -*- coding: utf-8 -*-
r"""查 α 重跑（PID 46628）的实时进度（2026-10-08 02:42）。

## 问题

队列 2 的驱动用 `subprocess.run(capture_output=True)` 启动 α 重跑 → **stdout 被捕获在内存里，
不落盘** → **跑到哪一步无从得知**（这是驱动的监控缺陷）。

## 本脚本怎么推断进度

| 证据 | 说明 |
|---|---|
| `alpha_from_gradients.json` 的 **mtime/大小** | 结束时会重写该文件 |
| `alpha_from_gradients_maxsamp2000.json` | 首跑备份**已存在**（01:51:53 写入）说明已进入重跑 |
| 进程 CPU/WS/启动时间 | 是否仍在推进 |
| `_alpha_rerun_driver.log` | 驱动结束时才会追加子进程输出 |

**判据**：`alpha_from_gradients.json` 的 mtime **晚于**备份文件的 mtime → 重跑已完成。

    python tools\_diag_alpha_rerun.py
"""
from __future__ import annotations

import io
import json
import subprocess
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CUR = REPO / "outputs/theory/alpha_from_gradients/alpha_from_gradients.json"
BAK = REPO / "outputs/theory/alpha_from_gradients/alpha_from_gradients_maxsamp2000.json"
DRV = REPO / "outputs/_alpha_rerun_driver.log"


def ts(p: Path) -> str:
    return datetime.fromtimestamp(p.stat().st_mtime).strftime("%H:%M:%S") if p.exists() else "—"


def main() -> int:
    print("=== 文件时间戳 ===")
    for p in (CUR, BAK, DRV):
        sz = p.stat().st_size if p.exists() else 0
        print(f"  {p.name:<46} {ts(p)}  {sz:>8} B")

    print("\n=== 重跑是否完成 ===")
    if CUR.exists() and BAK.exists():
        done = CUR.stat().st_mtime > BAK.stat().st_mtime
        print(f"  结果文件 mtime {'晚于' if done else '早于/等于'} 备份 → "
              f"{'✅ 重跑已完成' if done else '⏳ 仍在跑（或未写入）'}")
        if done:
            d = json.loads(io.open(CUR, encoding="utf-8").read())
            print(f"  max_samples={d.get('max_samples')} ｜ epochs={d.get('epochs')} "
                  f"｜ seeds={d.get('seeds')}")
            print(f"  corr={d.get('corr')} 中位相对误差={d.get('median_rel_err')} "
                  f"比值中位={d.get('median_ratio')} passed={d.get('passed')}")
            print(f"  轨迹拟合 R² 均值={d.get('r2_fit_mean')}")
            for r in d.get("records", []):
                y = r.get("traj", [])
                span = (max(y) - min(y)) if y else float("nan")
                print(f"    seed {r.get('seed')}: DG* 跨度 {span:.4f} ｜ R²_fit {r.get('R2_fit'):.3f} "
                      f"｜ α_fit {r.get('alpha_fit'):+.5f} ｜ α̂ {r.get('alpha_hat'):+.6f}")
    else:
        print("  缺文件，无法判定")

    print("\n=== 进程状态 ===")
    r = subprocess.run(["wmic", "process", "where", "name='python.exe'",
                        "get", "ProcessId,CreationDate,WorkingSetSize"],
                       capture_output=True, text=True)
    for ln in (r.stdout or "").splitlines():
        if ln.strip() and "ProcessId" not in ln:
            print("  " + ln.strip()[:100])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
