# -*- coding: utf-8 -*-
r"""修 `_p79` 的配对 bug：**按参数名配对**，不按列表位置（2026-10-09）。

## 故障

```
ip = dot(D, L) → RuntimeError（张量维度不匹配）
```
**原因**：我对 `gL` 与 `gD` **各自**按侧过滤，但两者的张量**顺序/集合未必一致**
→ `zip` 错位 → 维度不匹配。

**正确做法**：**按参数名取交集**，逐名配对。

    python tools\_p80_fix_inner_pairing.py [--apply]
"""
from __future__ import annotations

import ast
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "tools" / "_p79_true_inner_product.py"

OLD = '''            def sel(g, side):
                if side == "v":
                    return [x for n, x in g.items()
                            if x is not None and "vision_model" in n]
                return [x for n, x in g.items()
                        if x is not None and "text_model" in n]

            def dot(a, b):
                return float(sum(torch.dot(x, y) for x, y in zip(a, b)))

            def nrm(a):
                return float(sum(torch.dot(x, x) for x in a)) ** 0.5

            for side, k in (("v", "v"), ("t", "t")):
                L, D = sel(gL, side), sel(gD, side)
                if not L or not D:
                    continue
                ip = dot(D, L)
                nl, nd = nrm(L), nrm(D)'''

NEW = '''            def side_names(side):
                """该侧的参数名（**按名配对**，不按列表位置——否则 zip 会错位）。"""
                key = "vision_model" if side == "v" else "text_model"
                return [n for n in gL if key in n]

            def dot_names(names, ga, gb):
                return float(sum(torch.dot(ga[n], gb[n]) for n in names
                                 if ga.get(n) is not None and gb.get(n) is not None))

            def nrm_names(names, g):
                return float(sum(torch.dot(g[n], g[n]) for n in names
                                 if g.get(n) is not None)) ** 0.5

            for side, k in (("v", "v"), ("t", "t")):
                names = side_names(side)
                if not names:
                    continue
                ip = dot_names(names, gD, gL)
                nl, nd = nrm_names(names, gL), nrm_names(names, gD)'''


def main() -> int:
    apply = "--apply" in sys.argv
    t = io.open(F, encoding="utf-8").read()
    if "按名配对" in t:
        print("  已修，跳过")
        return 0
    if t.count(OLD) != 1:
        print(f"  ❌ 锚点未唯一命中（{t.count(OLD)}）")
        return 1
    t = t.replace(OLD, NEW, 1)
    ast.parse(t)
    if not apply:
        print("  （预演）")
        return 0
    io.open(F, "w", encoding="utf-8", newline="").write(t)
    t2 = io.open(F, encoding="utf-8").read()
    assert "按名配对" in t2 and "dot_names" in t2
    print("  ✅ 已改为按参数名配对（消除 zip 错位）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
