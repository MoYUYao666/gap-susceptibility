# -*- coding: utf-8 -*-
r"""把台账的 r4 行改为**3-seed 均值**断言（2026-10-10）。

## 现状（门禁失败根因）

台账 `NEW_ROWS` 用 `_fs[0]`（**第一个 seed**）与稿件值比对；
而表里（2026-10-10 起）是 **3-seed 均值** → 10 条失败。

## 改动

1. `NEW_ROWS` 的值改为 **3-seed 均值**；
2. 断言改为**对全目录 seed 取均值**；
3. 来源字段写明 `mean over 3 seeds`。

    python tools\_pa_ledger_3seed_fix.py [--apply]
"""
from __future__ import annotations

import ast
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "tools" / "_claim_ledger.py"

OLD_VALS = '''    NEW_ROWS = {
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
                  f"{_root}/{_arm}/seed42/results.json", tol=0.002)'''

NEW_VALS = '''    # 表值为 **3-seed 均值**（2026-10-10 起；此前误用单 seed，见表注）
    import statistics as _st
    NEW_ROWS = {
        "CLIP B/32@r4": ("outputs/strict_freeze_b32_r4",
                         {"text_only": (-0.0288, 0.621), "both": (-0.0188, 0.679),
                          "vision_only": (+0.0127, 0.670)}),
        "CLIP B/16@r4": ("outputs/strict_freeze_b16/r4",
                         {"text_only": (-0.0172, 0.651), "both": (+0.0107, 0.707),
                          "vision_only": (+0.0313, 0.686)}),
    }
    for _tag, (_root, _arms) in NEW_ROWS.items():
        for _arm, (_pcg, _pr1) in _arms.items():
            _fs = sorted(glob.glob(str(REPO / _root / _arm / "seed*" / "results.json")))
            assert _fs, f"缺归档: {_root}/{_arm}"
            _cgs, _r1s = [], []
            for _f in _fs:
                _d = json.loads(io.open(_f, encoding="utf-8").read())
                _cgs.append(_d["final_gap"]["centroid_gap"]
                            - _d["initial_gap"]["centroid_gap"])
                _r1s.append(_d["final_task_metrics"]["R@1"])
            _cg = _st.mean(_cgs)
            _r1 = _st.mean(_r1s)
            claim(f"{_tag} {_arm} CGΔ(3seed均值)", _pcg, _cg,
                  f"{_root}/{_arm}/*/results.json: mean over {len(_fs)} seeds", tol=0.0006)
            claim(f"{_tag} {_arm} R@1(3seed均值)", _pr1, _r1,
                  f"{_root}/{_arm}/*/results.json: mean over {len(_fs)} seeds", tol=0.002)'''


def main() -> int:
    apply = "--apply" in sys.argv
    t = io.open(F, encoding="utf-8").read()
    if "3seed均值" in t:
        print("  已改，跳过")
        return 0
    if t.count(OLD_VALS) != 1:
        print(f"  ❌ 锚点未唯一命中（{t.count(OLD_VALS)}）")
        return 1
    t = t.replace(OLD_VALS, NEW_VALS, 1)
    ast.parse(t)
    if not apply:
        print("  （预演）")
        return 0
    io.open(F, "w", encoding="utf-8", newline="").write(t)
    print("  ✅ 台账已改：r4 行按 **3-seed 均值**断言")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
