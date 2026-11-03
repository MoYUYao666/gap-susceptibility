# -*- coding: utf-8 -*-
r"""追查 ODE 拟合优度的**完整分布**——正文只给了"median R² 0.97"，掩盖了低值。

## 为什么必须做

全稿数字审计发现 13 处 R² 记录，**范围 0.7167–0.9990**，只有 7/13 ≥ 0.96。
正文与摘要写的是"mean/median $R^2 > 0.96$"——**用中位数概括一个含 0.717 的分布，
是审稿人会追问的地方**。要么说明低值属于什么配置（可接受的边界），要么修正主张。

## 输出

1. 每条 R² 记录**来自哪个文件、哪个键**（可复核）；
2. 分布：min / 分位 / median / max；
3. **低值（<0.96）分别属于哪个配置**，判断它们是否本就不该计入"LoRA 配置"的表述。

    python tools\_pa_r2_distribution.py
"""
from __future__ import annotations

import io
import json
import statistics as st
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
KEYS = ("R2", "r2", "R^2")


def main() -> int:
    rows: list[tuple[str, str, float]] = []

    def walk(o, src: str, path: str = "") -> None:
        if isinstance(o, dict):
            for k, v in o.items():
                if k in KEYS and isinstance(v, (int, float)) and 0 <= v <= 1:
                    rows.append((src, (path + "/" + k).lstrip("/"), float(v)))
                elif isinstance(v, (dict, list)):
                    walk(v, src, path + "/" + str(k))
        elif isinstance(o, list):
            for i, v in enumerate(o):
                if isinstance(v, (dict, list)):
                    walk(v, src, path)

    for p in sorted((REPO / "outputs").rglob("*.json")):
        try:
            walk(json.loads(io.open(p, encoding="utf-8", errors="ignore").read()),
                 str(p.relative_to(REPO)))
        except Exception:
            continue

    if not rows:
        print("  未找到 R² 记录")
        return 1
    vals = sorted(x[2] for x in rows)
    print(f"=== R² 分布（{len(vals)} 条记录）===")
    print(f"  min {vals[0]:.4f} ｜ p25 {vals[len(vals)//4]:.4f} ｜ median {st.median(vals):.4f}"
          f" ｜ mean {st.mean(vals):.4f} ｜ max {vals[-1]:.4f}")
    print(f"  ≥0.96: {sum(1 for x in vals if x >= 0.96)}/{len(vals)}"
          f" ｜ <0.96: {sum(1 for x in vals if x < 0.96)}/{len(vals)}")
    print("\n=== 逐条（按值升序，低值优先）===")
    for src, key, v in sorted(rows, key=lambda x: x[2]):
        flag = "  ⚠" if v < 0.96 else "   "
        print(f"{flag} {v:.4f}  {src}")
        print(f"            key={key}")
    print("\n=== 低值（<0.96）所属文件汇总 ===")
    low = sorted({src for src, _, v in rows if v < 0.96})
    for s in low:
        print("  " + s)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
