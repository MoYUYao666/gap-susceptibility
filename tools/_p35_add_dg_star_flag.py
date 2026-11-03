# -*- coding: utf-8 -*-
r"""给 `experiments/strict_freeze_control.py` 加 `--dg-star`（2026-10-08）。

## 为什么（操作者选 B：统一口径）

论文的 ODE 理论状态变量是 **`dg_star`**（配对均方距离），
而**此前 COCO 补跑没记它**（只有 `gap_history.json` 的 `centroid_gap`/`distribution_gap`）。

**关键发现**：`src/trainer.py:923` —— **`train()` 自己会写 `dg_star_history.json`**，
只需 `trainer.enable_dg_star_tracking()` 置位 `_record_dg_star`。
（`experiments/theory/v1_rank_sweep.py:134` 就是这么做的，归档的 96 个 `dg_star_history.json` 由此而来。）

## 改法

1. 加 CLI 开关 **`--dg-star`**（**默认关** → 不影响任何既有用法）；
2. 开启时在 `trainer.setup_model()` 之后调用 `enable_dg_star_tracking()`。

**成本**：每 epoch 多一次 500 样本的验证前向（很小），但换来与正文同口径的 `DG*` 轨迹。

    python tools\_p35_add_dg_star_flag.py [--apply]
"""
from __future__ import annotations

import ast
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "experiments" / "strict_freeze_control.py"

ARG_ANCHOR = '    ap.add_argument("--alpha-mult", type=int, default=2,'
ARG_ADD = ('''    ap.add_argument("--dg-star", action="store_true",
                    help="同时记录 DG* 逐 epoch 轨迹（写 dg_star_history.json）。"
                         "论文 ODE 的状态变量是 DG*，故需要与正文同口径时必须开启。")
''' + ARG_ANCHOR)

ENABLE_OLD = """    first = next(iter(val_loader))
    ranks_init = layer_effective_ranks(trainer.model, first, trainer.processor)"""
ENABLE_NEW = """    # 记录 DG* 逐 epoch 轨迹（论文 ODE 的状态变量；train() 会写 dg_star_history.json）
    if "--dg-star" in sys.argv:
        trainer.enable_dg_star_tracking()
        print("[dg-star] 已启用逐 epoch DG* 记录 → dg_star_history.json")

    first = next(iter(val_loader))
    ranks_init = layer_effective_ranks(trainer.model, first, trainer.processor)"""


def main() -> int:
    apply = "--apply" in sys.argv
    t = io.open(F, encoding="utf-8").read()
    if "--dg-star" in t:
        print("  已加，跳过")
        return 0
    for old, tag in ((ARG_ANCHOR, "CLI 锚点"), (ENABLE_OLD, "启用锚点")):
        if t.count(old) != 1:
            print(f"  ❌ {tag} 未唯一命中（{t.count(old)}）")
            return 1
    if not apply:
        print("  （预演）")
        return 0
    t = t.replace(ARG_ANCHOR, ARG_ADD, 1).replace(ENABLE_OLD, ENABLE_NEW, 1)
    ast.parse(t)
    io.open(F, "w", encoding="utf-8", newline="").write(t)
    t2 = io.open(F, encoding="utf-8").read()
    assert "--dg-star" in t2 and "enable_dg_star_tracking" in t2
    print("  ✅ 已加 --dg-star（默认关；开启后写 dg_star_history.json）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
