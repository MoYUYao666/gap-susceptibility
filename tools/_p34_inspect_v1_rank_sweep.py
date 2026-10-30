# -*- coding: utf-8 -*-
r"""查 `experiments/theory/v1_rank_sweep.py` 的 CLI 与产出方式（2026-10-08）。

## 为什么

操作者选 B（统一口径）：需让 COCO 补跑同时记录 **`dg_star`**。
产出 `dg_star_history.json` 的脚本是 `v1_rank_sweep.py`，须先看它：
1. 支持哪些命令行参数（能否切 COCO / 严格冻结 / site / rank / seed）；
2. 如何写 `dg_star_history.json`（字段名与归档一致？）；
3. 是否严格冻结（归档的 `n_trainable=145M` 说明**不是**）。

**不改任何东西，只读。**

    python tools\_p34_inspect_v1_rank_sweep.py
"""
from __future__ import annotations

import io
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "experiments" / "theory" / "v1_rank_sweep.py"


def main() -> int:
    t = io.open(F, encoding="utf-8").read()
    L = t.splitlines()
    print(f"=== {F.relative_to(REPO)} ｜ {len(L)} 行 ===")
    print("\n--- CLI 参数 ---")
    for m in re.finditer(r'add_argument\((.*?)\)\n', t, re.S):
        s = " ".join(m.group(1).split())
        print("  " + s[:140])

    print("\n--- 关键设置（dataset / freeze / site / rank / seeds / epochs）---")
    for i, l in enumerate(L, 1):
        s = l.strip()
        if re.search(r'dataset|freeze|apply_to_|rank\s*=|seeds\s*=|epochs\s*=|max_samples\s*=', s) \
                and not s.startswith("#") and len(s) < 120:
            print(f"  L{i:>4}: {s}")

    print("\n--- dg_star_history.json 的写入方式 ---")
    for i, l in enumerate(L, 1):
        if "dg_star_history" in l or "json.dump" in l:
            print(f"  L{i:>4}: {l.strip()[:130]}")

    print("\n--- 是否启用 dg_star 追踪 ---")
    for i, l in enumerate(L, 1):
        if "dg_star" in l.lower() and "enable" in l.lower() or "_record_dg_star" in l:
            print(f"  L{i:>4}: {l.strip()[:130]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
