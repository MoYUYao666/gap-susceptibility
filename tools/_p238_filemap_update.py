# -*- coding: utf-8 -*-
r"""更新 `文件地图.md`：A1 新标题与页数、Paper A 状态（2026-10-12）。

## 改什么

| 行 | 旧 | 新 |
|---|---|---|
| A1 标题 | *The Modality Gap Is Not a Universal Health Metric: Order Preservation Governs Zero-Shot Robustness* | *Order Preservation **Tracks Zero-Shot Accuracy** under Classification Fine-Tuning: Why the Modality Gap Is Not a Universal Health Metric* |
| A1 页数 | `—` | **42** |
| A1 摘要词数 | 245 | **249** |
| Paper A 页数 | 55 | **56**（与实测一致） |

    python tools\_docs_filemap_update.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "文件地图.md"

OLD_A1 = ("| `paper_a1/` | **A1** | The Modality Gap Is Not a Universal Health Metric: "
          "Order Preservation Governs Zero-Shot Robustness | elsarticle | — |")
NEW_A1 = ("| `paper_a1/` | **A1** | Order Preservation Tracks Zero-Shot Accuracy under "
          "Classification Fine-Tuning: Why the Modality Gap Is Not a Universal Health Metric "
          "| elsarticle | **42** |")

OLD_NOTE = ("合规改造已完成（摘要 245 词/关键词 5/highlights 5 条/**56 条文献转 APA**）；"
            "**待操作者点链接确认转投**")
NEW_NOTE = ("合规改造已完成（摘要 **249** 词/关键词 5/highlights 5 条/**56 条文献转 APA**）；"
            "**2026-10-12 重定位**：标题去掉 \"Zero-Overhead Monitor\"（"
            "**补做 100 检查点组内检验 + 监控决策实验**后确认 —— 组内 τ 跟踪良好"
            "（n=30 Fisher **+0.840**），但**决策价值不成立**（τ 达峰与「固定停 ep1」逐位相同）；"
            "主张改为「tracks / diagnostic」）；**待操作者点链接确认转投**")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(F, encoding="utf-8", errors="replace").read()
    n1, n2 = t.count(OLD_A1), t.count(OLD_NOTE)
    print(f"  === 锚点：A1 行 {n1} ｜ 备注 {n2} ===")
    if n1 != 1 or n2 != 1:
        for i, ln in enumerate(t.splitlines(), 1):
            if "paper_a1/" in ln or "245 词" in ln:
                print(f"  L{i}: {ln[:150]}")
        return 1
    t = t.replace(OLD_A1, NEW_A1, 1).replace(OLD_NOTE, NEW_NOTE, 1)
    if not a.apply:
        print("  （预演）")
        return 0
    bak = F.with_suffix(".md.bak_p238")
    if not bak.exists():
        shutil.copy2(F, bak)
    io.open(F, "w", encoding="utf-8", newline="").write(t)
    t2 = io.open(F, encoding="utf-8", errors="replace").read()
    ok = ("Order Preservation Tracks Zero-Shot Accuracy" in t2
          and "Zero-Overhead Monitor" not in t2
          and "+0.840" in t2)
    print(f"  {'✅ 文件地图已更新' if ok else '🔴 更新失败'}")
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
