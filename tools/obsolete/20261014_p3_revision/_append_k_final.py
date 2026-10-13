# -*- coding: utf-8 -*-
r"""把 k 的最终结论追加进 `docs/K043_INVESTIGATION.md`（覆盖 r∈[1,64] 后）。

    python tools\_append_k_final.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ADD = r"""

---

## 最终结论（2026-10-04，覆盖 $r\in[1,64]$）

both 臂 6 个 rank 的 checkpoint 齐备后重测（严格冻结，3 seeds 平均）：

| rank | $\|g_v\|$ |
|---|---|
| 1 | 13.037 |
| 4 | 12.754 |
| 8 | 13.369 |
| 16 | 13.127 |
| 32 | 14.093 |
| 64 | 13.815 |

### 三条结论

1. **「平坦」成立，且裕度极大**：$\|g_v\|$ 极差 **10%**（12.75–14.09），
   而若按 $\|g_v\|\propto\sqrt r$，$r$ 由 1 到 64 应变化 **8 倍（800%）**。
   实测变化比预测小约 **80 倍** —— **Effective Rank Saturation 的核心主张为真**。
2. **论文的 $k = 0.043$ 无法复现**：线性拟合给出 **0.257**。
3. **但斜率本身不应报**：相邻区间的局部斜率为 **−0.20 / +0.89 / −0.35 / +1.39 / −0.40**，
   **正负交替** → **不存在可辨的线性趋势**，任何「斜率」都只是噪声的净残差。
   **正确的陈述是**实测区间（12.75–14.09）与「$\sqrt r$ 预测 8 倍」的对比——这正是 ERS 的含义，
   且**不依赖拟合**。

### 因此正文应改为

| 原 | 建议 |
|---|---|
| "$\|g_v\|$ is flat across $r\in[1,64]$, with slope $k=0.043$" | "$\|g_v\|$ varies by only 10% across $r\in[1,64]$ (12.75--14.09), where $\|g_v\|\propto\sqrt r$ would predict an eightfold change" |

**理由**：报一个来自无趋势曲线的斜率，是把噪声当信号；报区间与预测的对比则直接、可复核、且更有说服力。

### 数据来源

`outputs/analysis/k_remeasured_both.json`（脚本 `tools/_pa_remeasure_k.py`，可重跑，3 seeds/rank）。
"""


def main() -> int:
    apply = "--apply" in sys.argv
    p = REPO / "docs" / "K043_INVESTIGATION.md"
    t = io.open(p, encoding="utf-8").read()
    if "最终结论（2026-10-04" in t:
        print("  已含最终结论，跳过")
        return 0
    if apply:
        io.open(p, "w", encoding="utf-8", newline="").write(t.rstrip() + ADD)
        t2 = io.open(p, encoding="utf-8").read()
        for k in ("0.257", "正负交替", "13.037", "不应报"):
            assert k in t2, f"断言失败：缺 {k}"
        print(f"  ✅ 已追加（{len(t2.splitlines())} 行）")
    else:
        print("  （预演）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
