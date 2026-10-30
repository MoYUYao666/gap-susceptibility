# -*- coding: utf-8 -*-
r"""改掉 `siglip_experiments.py` 里"间隙降=✅ / 间隙升=❌"的误导判据（2026-10-04）。

## 问题

`siglip_experiments.py:454`：

```python
marker = "✅" if delta < 0 else ("⚠️" if delta == 0 else "❌")
```

它把**间隙增大标记为失败**，即默认"降间隙是目标"。而本项目的核心发现恰恰是
**"降间隙 ≠ 提检索"**——OpenCLIP 上 both 臂的间隙**更大**、检索却**更强**。

操作者看到 `❌ s7_siglip_lora_r4_text_only` 时合理地产生了疑问，说明该判据**确实会误导**。

## 改法

改为**中性报告**：方向箭头（↓ / = / ↑）+ 检索值 + 明确标注 "run completed"，
**不作好坏判断**。

    python tools\_fix_siglip_marker.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "experiments" / "siglip_experiments.py"

OLD = '            marker = "\u2705" if delta < 0 else ("\u26a0\ufe0f" if delta == 0 else "\u274c")\n' \
      '            print(f"   {marker} {name:<40s} CG \u0394={delta:+.4f}  R@1={r1}")\n'

NEW = ('            # \u4e0d\u8981\u7528\u201c\u95f4\u9699\u964d=\u597d\u201d\u5f53\u6210\u8d25\u5224\u636e\uff1a\u672c\u9879\u76ee\u7684\u6838\u5fc3\u53d1\u73b0\u6b63\u662f\u201c\u964d\u95f4\u9699 \u2260 \u63d0\u68c0\u7d22\u201d\n'
       '            # \uff08OpenCLIP \u4e0a both \u81c2\u7684\u95f4\u9699\u66f4\u5927\u3001\u68c0\u7d22\u5374\u66f4\u5f3a\uff09\u3002\u8fd9\u91cc\u53ea\u4e2d\u6027\u62a5\u544a\u65b9\u5411\u4e0e\u68c0\u7d22\u3002\n'
       '            arrow = "\u2193" if delta < 0 else ("=" if delta == 0 else "\u2191")\n'
       '            print(f"   [gap {arrow}] {name:<40s} CG \u0394={delta:+.4f}  R@1={r1}  (run completed)")\n')


def main() -> int:
    apply = "--apply" in sys.argv
    t = io.open(F, encoding="utf-8").read()
    if "[gap " in t:
        print("  已改，跳过")
        return 0
    c = t.count(OLD)
    if c != 1:
        print(f"  ⚠ 未唯一命中（{c} 次）—— 打印实际行以便修正：")
        for i, l in enumerate(t.splitlines(), 1):
            if "marker" in l or ("CG" in l and "print" in l):
                print(f"     L{i}: {l!r}")
        return 1
    print("  ✅ 命中判据行")
    if apply:
        io.open(F, "w", encoding="utf-8", newline="").write(t.replace(OLD, NEW, 1))
        t2 = io.open(F, encoding="utf-8").read()
        assert "[gap " in t2 and "run completed" in t2
        assert "if delta < 0 else" in t2  # 箭头逻辑保留
        print("  ✅ 已改为中性报告并断言通过")
    else:
        print("  （预演）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
