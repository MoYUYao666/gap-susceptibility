# -*- coding: utf-8 -*-
r"""修正 `k` 的复算脚本与结论（2026-10-04）。

## 实测结果（both 臂，严格冻结，3 seeds 平均，覆盖 r∈[1,64]）

| rank | $\|g_v\|$ |
|---|---|
| 1 | 13.037 |
| 4 | 12.754 |
| 8 | 13.369 |
| 16 | 13.127 |
| 32 | 14.093 |
| 64 | 13.815 |

**局部斜率正负交替**（−0.20 / +0.89 / −0.35 / +1.39 / −0.40）→ **不存在可辨的线性趋势**。

## 三条结论

1. **"平坦"成立且裕度极大**：$\|g_v\|$ 极差 10%，而 $\sqrt r$ 预测应变化 **8 倍（800%）**。
2. **论文的 $k = 0.043$ 无法复现**：线性拟合给出 0.257（且该数字**无意义**，见第 3 点）。
3. **不应报斜率**：曲线无单调趋势，任何"斜率"都是噪声的净残差。**正确的陈述是**实测区间
   （12.75–14.09）与"$\sqrt r$ 预测 8 倍"的对比——这正是 ERS 要表达的意思，且不依赖拟合。

## 脚本 bug

`tools/_pa_remeasure_k.py` 结尾的 caveat 是**硬编码** "covers ranks [...] only; paper claims r in [1,64]"，
但加入 r1/r64 后该提示仍写"缺 1 与 64" → 会误导读结论的人。本脚本改为**动态生成**。

    python tools\_fix_k_remeasure.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "tools" / "_pa_remeasure_k.py"

OLD = '''    print("  ⚠ 覆盖范围: r ∈ %s，**不含** 1 与 64" % [r for r, _ in rows])'''
NEW = '''    missing = [r for r in (1, 2, 4, 8, 16, 32, 64) if r not in [x for x, _ in rows]]
    print("  覆盖范围: r ∈ %s" % [r for r, _ in rows])
    if missing:
        print("  ⚠ 未覆盖: %s（论文称 r∈[1,64]）" % missing)
    else:
        print("  ✅ 已覆盖论文声称的区间 r∈[1,64]")
    vals = [v for _, v in rows]
    spread = 100.0 * (max(vals) - min(vals)) / (sum(vals) / len(vals))
    print("  ‖g_v‖ 区间 %.4f–%.4f（极差 %.1f%%）｜ 若按 sqrt(r)，r 由 %d→%d 应变化 %.1f 倍"
          % (min(vals), max(vals), spread, min(r for r, _ in rows), max(r for r, _ in rows),
             (max(r for r, _ in rows) / min(r for r, _ in rows)) ** 0.5))
    print("  ⚠ 注意：若局部斜率正负交替，则『斜率』本身无意义——应报区间与 sqrt(r) 的对比，而非斜率")'''


def main() -> int:
    apply = "--apply" in sys.argv
    t = io.open(F, encoding="utf-8").read()
    if NEW.split("\n")[0].strip() in t:
        print("  已修，跳过")
        return 0
    c = t.count(OLD)
    if c != 1:
        print(f"  ⚠ 未唯一命中（{c} 次）")
        return 1
    print("  ✅ 命中硬编码 caveat")
    if apply:
        io.open(F, "w", encoding="utf-8", newline="").write(t.replace(OLD, NEW, 1))
        t2 = io.open(F, encoding="utf-8").read()
        assert "局部斜率正负交替" in t2 and "未覆盖" in t2
        print("  ✅ 已改为动态生成并断言通过")
    else:
        print("  （预演）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
