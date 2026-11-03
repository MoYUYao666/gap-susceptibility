# -*- coding: utf-8 -*-
r"""查清 `tab:position_strict` 的值到底是哪种口径（2026-10-09 我改表后门禁失败）（2026-10-10）。

## 现象

门禁报 10 条失败，例如：

```
CLIP B/32@r4 text_only CGΔ   稿件 -0.0297   实测(seed42) -0.027359
CLIP B/32@r4 both      CGΔ   稿件 -0.0186   实测(seed42) -0.019243
```

**怀疑**：我在 2026-10-09 补 seed 时**新跑了 seed42**，覆盖了原先的 seed42 结果；
而表里的值可能是**当时的某一份**（单 seed 或均值）。

## 本脚本

对每个 (骨干, 臂) 打印：**seed42 / seed123 / seed456 / 三 seed 均值**，
与**稿件表里的值**并排 → **判定表里用的是哪个口径**。

    python tools\_p89_table_caliber.py [--apply]
"""
from __future__ import annotations

import glob
import io
import json
import statistics as st
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "outputs" / "analysis" / "table_caliber.json"

# 稿件表里的值（从 `_claim_ledger.py` 的"稿件"列抄，2026-10-10）
PAPER = {
    ("outputs/strict_freeze_b32_r4", "text_only"): (-0.0297, 0.625),
    ("outputs/strict_freeze_b32_r4", "both"): (-0.0186, 0.680),
    ("outputs/strict_freeze_b32_r4", "vision_only"): (0.0124, 0.668),
    ("outputs/strict_freeze_b16/r4", "text_only"): (-0.0190, 0.642),
    ("outputs/strict_freeze_b16/r4", "both"): (0.0150, 0.696),
    ("outputs/strict_freeze_b16/r4", "vision_only"): (0.0433, 0.677),
}


def main() -> int:
    apply = "--apply" in sys.argv
    report = {}
    print("=== 三口径对照 vs 稿件 ===")
    for (root, arm), (pcg, pr1) in PAPER.items():
        rows = {}
        for f in sorted(glob.glob(str(REPO / root / arm / "seed*" / "results.json"))):
            d = json.loads(io.open(f, encoding="utf-8").read())
            seed = Path(f).parent.name
            cg = d["final_gap"]["centroid_gap"] - d["initial_gap"]["centroid_gap"]
            r1 = d["final_task_metrics"]["R@1"]
            rows[seed] = (cg, r1)
        cgs = [v[0] for v in rows.values()]
        r1s = [v[1] for v in rows.values()]
        mean_cg = st.mean(cgs) if cgs else float("nan")
        mean_r1 = st.mean(r1s) if r1s else float("nan")
        s42 = rows.get("seed42", (float("nan"),) * 2)
        print(f"\n  ── {root.split('/')[-1]} / {arm}")
        print(f"     稿件     CGΔ={pcg:+.4f}  R@1={pr1:.3f}")
        for seed in sorted(rows):
            print(f"     {seed:<9} CGΔ={rows[seed][0]:+.4f}  R@1={rows[seed][1]:.3f}")
        print(f"     **3seed均值** CGΔ={mean_cg:+.4f}  R@1={mean_r1:.3f}")
        # 判定表里用的是哪个
        def close(a, b):
            return abs(a - b) < 5e-4
        which = []
        if close(pcg, s42[0]):
            which.append("seed42")
        if close(pcg, mean_cg):
            which.append("3seed均值")
        print(f"     → 稿件 CGΔ 匹配: **{which or '都不匹配（需查历史）'}**")
        report[f"{root}/{arm}"] = {
            "paper": {"cg": pcg, "r1": pr1},
            "per_seed": {k: {"cg": v[0], "r1": v[1]} for k, v in rows.items()},
            "mean3": {"cg": mean_cg, "r1": mean_r1},
            "matches": which,
        }

    if apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps(report, ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
