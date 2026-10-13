# -*- coding: utf-8 -*-
r"""把新加入表格的数字加进**可复现门禁台账**（2026-10-08）。

## 为什么

论文 `tab:position_strict` 新增两行（`CLIP B/32† @ r4`、`CLIP B/16† @ r4`），
**每个数字都必须指名来源**（唯一原则）。

## 新增主张（6 个 CGΔ + 6 个 R@1）

| 行 | 来源 |
|---|---|
| `CLIP B/32 @ r4` 三臂 | `outputs/strict_freeze_b32_r4/{arm}/seed42/results.json` |
| `CLIP B/16 @ r4` 三臂 | `outputs/strict_freeze_b16/r4/{arm}/seed42/results.json` |

    python tools\_pa_add_new_rows_to_ledger2.py [--apply]
"""
from __future__ import annotations

import ast
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "tools" / "_claim_ledger.py"

ANCHOR = "    # ── ② ODE 台账（逐 run 拟合）"

ADD = '''    # ── ①b 表格新增两行（同秩对照，2026-10-08 加入 tab:position_strict）──
    NEW_ROWS = {
        "CLIP B/32@r4": ("outputs/strict_freeze_b32_r4",
                         {"text_only": (-0.0297, 0.625), "both": (-0.0186, 0.680),
                          "vision_only": (+0.0124, 0.668)}),
        "CLIP B/16@r4": ("outputs/strict_freeze_b16/r4",
                         {"text_only": (-0.0190, 0.642), "both": (+0.0150, 0.696),
                          "vision_only": (+0.0433, 0.677)}),
    }
    for _tag, (_root, _arms) in NEW_ROWS.items():
        for _arm, (_pcg, _pr1) in _arms.items():
            _fs = sorted(glob.glob(str(REPO / _root / _arm / "seed*" / "results.json")))
            assert _fs, f"缺归档: {_root}/{_arm}"
            _d = json.loads(io.open(_fs[0], encoding="utf-8").read())
            _cg = _d["final_gap"]["centroid_gap"] - _d["initial_gap"]["centroid_gap"]
            _r1 = _d["final_task_metrics"]["R@1"]
            claim(f"{_tag} {_arm} CGΔ", _pcg, _cg,
                  f"{_root}/{_arm}/seed42/results.json", tol=0.0006)
            claim(f"{_tag} {_arm} R@1", _pr1, _r1,
                  f"{_root}/{_arm}/seed42/results.json", tol=0.002)

''' + ANCHOR


def main() -> int:
    apply = "--apply" in sys.argv
    t = io.open(F, encoding="utf-8").read()
    if "表格新增两行（同秩对照" in t:
        print("  已加，跳过")
        return 0
    if t.count(ANCHOR) != 1:
        print(f"  ❌ 锚点未唯一命中（{t.count(ANCHOR)}）")
        return 1
    if not apply:
        print("  （预演）")
        return 0
    t = t.replace(ANCHOR, ADD, 1)
    ast.parse(t)
    io.open(F, "w", encoding="utf-8", newline="").write(t)
    print("  ✅ 已加 12 条主张（6 CGΔ + 6 R@1）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
