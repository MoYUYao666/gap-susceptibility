# -*- coding: utf-8 -*-
r"""因 1e-7 结果更新 `discussion.tex` 的两处表述（2026-10-12）。

## 新数据（`pr_fullft_lr_sweep_ext.json`）

| lr | zero-shot | ΔCG |
|---|---|---|
| **1e-7** | **60.53%** | **−0.0061** |
| **1e-6** | **60.87 ± 0.21%** | **−0.0016** |

→ **两个都在 "lr ≤ 1e-6 不扩大间隙" 的区间内**，且 **1e-6 的 zero-shot 仍略高**
（60.87 vs 60.53，在 1e-6 的 sd 0.21 内）。所以：
- **"full fine-tuning is optimal at $10^{-6}$"** → 应改为 **"at the bottom of the range
  ($10^{-7}$--$10^{-6}$, indistinguishable within seed spread)"**
- **"full fine-tuning at $10^{-6}$"** 的对标处应注明 **1e-7 同样属于该区间**

    python tools\_p345_discussion_lowlr.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "paper合" / "sections" / "discussion.tex"

PAIRS = [
    (r"full fine-tuning is optimal at $10^{-6}$, LoRA at $10^{-5}$,",
     r"full fine-tuning is optimal at the bottom of the range "
     r"($10^{-7}$--$10^{-6}$, indistinguishable within its seed spread), LoRA at $10^{-5}$,"),
    (r"against $60.87\pm0.21\%$ and $-0.0016$ for full fine-tuning at $10^{-6}$",
     r"against $60.87\pm0.21\%$ and $-0.0016$ for full fine-tuning at $10^{-6}$ "
     r"($60.53\%$ and $-0.0061$ at $10^{-7}$)"),
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(F, encoding="utf-8", errors="replace").read()
    t2, total = t, 0
    for old, new in PAIRS:
        n = t2.count(old)
        print(f"  命中 {n} ｜ {old[:56]}…")
        if n:
            t2 = t2.replace(old, new)
            total += n
    if not a.apply:
        print("  （预演）")
        return 0
    if total:
        bak = F.with_suffix(".tex.bak_p345")
        if not bak.exists():
            shutil.copy2(F, bak)
        io.open(F, "w", encoding="utf-8", newline="").write(t2)
    print(f"\n  → 共改 {total} 处")
    t3 = io.open(F, encoding="utf-8", errors="replace").read()
    checks = {
        "含 bottom of the range": "bottom of the range" in t3,
        "含 1e-7 的对标值": "$60.53\\%$ and $-0.0061$ at $10^{-7}$" in t3,
    }
    ok = True
    for k, v in checks.items():
        print(f"  {'✅' if v else '🔴'} {k}")
        ok = ok and v
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
