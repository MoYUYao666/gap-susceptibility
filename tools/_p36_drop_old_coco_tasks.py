# -*- coding: utf-8 -*-
r"""从队列里**移除旧 COCO 任务**（无 `dg_star`，已被 COCO-DG* 版取代，2026-10-08）。

## 背景

操作者选 B（统一口径）→ COCO 须带 `DG*` 重跑（12 配置 × 3 seed = 36 run，写入 `outputs/coco_sweep_dgstar/`）。

旧任务（写 `outputs/coco_sweep/`）**已完成 31/36**，剩余 5 个：
- **其数据仍保留**（不删目录），作对照用；
- 但它们**没有 `dg_star`** → 对论文的表无用 → **不该再占用 ~3.5 h GPU**。

## 改法

删掉 `build_queue()` 里生成旧 COCO 任务的那个 for 循环。

    python tools\_p36_drop_old_coco_tasks.py [--apply]
"""
from __future__ import annotations

import ast
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "tools" / "_p20_serial_executor.py"

OLD = '''    for site in ("both", "text_only"):
        for rk in (4, 16, 64, 1, 2, 32):
            out = REPO / f"outputs/coco_sweep/r{rk}/{site}/seed42/results.json"
            q.append((f"COCO {site} r={rk}",
                      [PY, "experiments/strict_freeze_control.py",
                       "--dataset", "coco", "--data-dir", ".",
                       "--out-dir", f"outputs/coco_sweep/r{rk}", "--name", f"coco_{site}_r{rk}_",
                       "--rank", str(rk), "--alpha-mult", "2", "--tags", site,
                       "--seeds", *"42 123 456".split(), "--epochs", "10", "--max-samples", "5000",
                       "--batch-size", "128", "--skip-frozen"], out, 3 * 3600))
'''

NEW = '''    # 旧口径 COCO 任务（写 outputs/coco_sweep/，**无 dg_star**）已由下方 COCO-DG* 取代。
    # 现有 31/36 的产物**保留在盘上作对照**，但不再排队（它们对论文的表无用）。
'''


def main() -> int:
    apply = "--apply" in sys.argv
    t = io.open(F, encoding="utf-8").read()
    if "已由下方 COCO-DG* 取代" in t:
        print("  已改，跳过")
        return 0
    if t.count(OLD) != 1:
        print(f"  ❌ 未唯一命中（{t.count(OLD)}）")
        return 1
    if not apply:
        print("  （预演）")
        return 0
    t = t.replace(OLD, NEW, 1)
    ast.parse(t)
    io.open(F, "w", encoding="utf-8", newline="").write(t)
    t2 = io.open(F, encoding="utf-8").read()
    assert "已由下方 COCO-DG* 取代" in t2
    assert 'outputs/coco_sweep/r{rk}' not in t2, "旧任务仍在"
    print("  ✅ 旧 COCO 任务已从队列移除（产物保留在盘上）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
