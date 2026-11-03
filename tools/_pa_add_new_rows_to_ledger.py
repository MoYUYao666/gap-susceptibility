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

    python tools\_pa_add_new_rows_to_ledger.py [--apply]
"""
from __future__ import annotations

import ast
import glob
import io
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "tools" / "_claim_ledger.py"

ANCHOR = '''    # ── ② ODE 台账（逐 run 拟合）'''

ADD = '''    # ── ①b 表格新增两行（同秩对照，2026-10-08 加入 tab:position_strict）──
    def _one_run_cg(root: str, arm: str) -> float:
        fs = glob.glob(str(REPO / root / arm / "seed*" / "results.json"))
        assert fs, f"缺归档: {root}/{arm}"
        d = json.loads(io.open(sorted(fs)[0], encoding="utf-8").read())
        return d["final_gap"]["centroid_gap"] - d["initial_gap"]["centroid_gap"]

    def _one_run_r1(root: str, arm: str) -> float:
        fs = glob.glob(str(REPO / root / arm / "seed*" / "results.json"))
        d = json.loads(io.open(sorted(fs)[0], encoding="utf-8").read())
        return d["final_task_metrics"]["R@1"]

    for _root, _tag in (("outputs/strict_freeze_b32_r4", "CLIP B/32@r4"),
                        ("outputs/strict_freeze_b16/r4", "CLIP B/16@r4")):
        for _arm, _paper_cg, _paper_r1 in (("text_only", -0.0297, 0.625),
                                           ("both", -0.0186, 0.680),
                                           ("vision_only", +0.0124, 0.668)) \\
                if _root.endswith("b32_r4") else \\
                (("text_only", -0.0190, 0.642),
                 ("both", +0.0150, 0.696),
                 ("vision_only", +0.0433, 0.677)):
            claim(f"{_tag} {_arm} CGΔ", _paper_cg, _one_run_cg(_root, _arm),
                  f"{_root}/{_arm}/seed42/results.json", tol=0.0006)
            claim(f"{_tag} {_arm} R@1", _paper_r1, _one_run_r1(_root, _arm),
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
