# -*- coding: utf-8 -*-
r"""查归档训练用的**学习率调度器**（2026-10-08 04:10）。

## 为什么关键

梯度流恒等式 `d(DG*)/dt = −η⟨∇_θ DG*, ∇_θ L⟩` **假定 η 近似恒定**。
若训练用 **cosine 衰减**（η 从 1e-4 降到 ~1e-7），**恒等式不成立** →
由此得到的 α̂ = −η̄·mean(inner) **系统性偏小**（实测偏小 30–70 倍）。

**归档的 DG\* 降幅 0.165（630 步）vs 我的 0.014（780 步）——差 12 倍，而两者"内积均值"相近（1.3 量级）**
→ **差异几乎必然在 η**（调度器或基准 lr）。

## 查什么

1. `src/config.py` 的 `TrainConfig` 默认 lr / scheduler；
2. `src/trainer.py` 里调度器如何构造与步进；
3. 归档 `results.json` 是否记录 lr。

    python tools\_diag_lr_schedule.py
"""
from __future__ import annotations

import glob
import io
import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def main() -> int:
    print("=== 1) TrainConfig 默认值 ===")
    t = io.open(REPO / "src/config.py", encoding="utf-8").read()
    i = t.find("class TrainConfig")
    if i < 0:
        print("  未找到 TrainConfig")
    else:
        j = t.find("\nclass ", i + 1)
        seg = t[i:j if j > 0 else len(t)]
        for ln in seg.splitlines():
            s = ln.strip()
            if any(k in s for k in ("learning_rate", "lr", "scheduler", "warmup", "num_epochs",
                                    "batch_size")) and "=" in s and not s.startswith("#"):
                print("   " + s[:110])

    print("\n=== 2) trainer 里的调度器构造 ===")
    tr = io.open(REPO / "src/trainer.py", encoding="utf-8").read()
    for m in re.finditer(r".*(?:scheduler|CosineAnnealing|StepLR|OneCycle|LambdaLR|get_scheduler).*",
                         tr):
        s = m.group(0).strip()
        if not s.startswith("#") and len(s) < 130:
            print("   " + s)

    print("\n=== 3) 归档 results.json 是否记录 lr ===")
    for f in sorted(glob.glob("outputs/theory/v1_trajectory/v1_both_r8/seed*/results.json"))[:1]:
        d = json.loads(io.open(f, encoding="utf-8").read())
        hits = [k for k in d if re.search(r"lr|learn|sched", k, re.I)]
        print(f"  {f.replace(chr(92), '/')}")
        print(f"  含 lr/sched 的键: {hits if hits else '（无）'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
