# -*- coding: utf-8 -*-
r"""检查补 seed 后各骨干的**排序是否稳定**（风险 #1 判据，2026-10-08）。

## 预写判据（`tools/_p56_add_seeds.py` 里已声明）

补 seed 后，**每个骨干的"最保护臂"不得改变**；
且给出跨 seed 的 `sd`，与已记录的 CLIP B/32 @ r8（sd≈0.003）对比。
**若某骨干排序在新 seed 下翻转 → 必须如实报告并降级该结论。**

    python tools\_p59_seed_stability.py [--apply]
"""
from __future__ import annotations

import glob
import io
import json
import statistics as st
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "outputs" / "analysis" / "seed_stability.json"

CONFIGS = [
    ("CLIP B/32 @ r8 (归档)", "outputs/strict_freeze"),
    ("CLIP B/32 @ r4", "outputs/strict_freeze_b32_r4"),
    ("CLIP B/16 @ r4", "outputs/strict_freeze_b16/r4"),
    ("OpenCLIP @ r4", "outputs/strict_freeze_oclip/r4"),
]
ARMS = ("text_only", "both", "vision_only")


def cg(f: Path):
    try:
        d = json.loads(io.open(f, encoding="utf-8").read())
    except Exception:
        return None
    g = d.get("initial_gap", {}).get("centroid_gap")
    h = d.get("final_gap", {}).get("centroid_gap")
    return (h - g) if (g is not None and h is not None) else None


def main() -> int:
    apply = "--apply" in sys.argv
    print("=== 补 seed 后的排序稳定性（风险 #1 判据）===")
    report = {}
    for label, root in CONFIGS:
        print(f"\n  ── {label} ──")
        vals = {}
        for arm in ARMS:
            fs = sorted(glob.glob(str(REPO / root / arm / "seed*" / "results.json")))
            xs = [v for v in (cg(Path(f)) for f in fs) if v is not None]
            if xs:
                vals[arm] = {"n": len(xs), "mean": st.mean(xs),
                             "sd": st.stdev(xs) if len(xs) > 1 else None,
                             "vals": [round(v, 4) for v in xs]}
        if not vals:
            print("     （无数据）")
            continue
        for arm in ARMS:
            if arm in vals:
                v = vals[arm]
                sd = f"± {v['sd']:.4f}" if v["sd"] is not None else "（单 seed）"
                print(f"     {arm:<12} {v['mean']:+.4f} {sd:<12} n={v['n']}  {v['vals']}")
        best = min(vals, key=lambda a: vals[a]["mean"])
        print(f"     → 最保护臂 = **{best}**")
        report[label] = {"arms": vals, "most_protective": best}

    print("\n=== 判定 ===")
    # 与"补 seed 前"的最优臂比较（补 seed 前全部记录为 text_only）
    prior = {"CLIP B/32 @ r8 (归档)": "text_only", "CLIP B/32 @ r4": "text_only",
             "CLIP B/16 @ r4": "text_only", "OpenCLIP @ r4": "text_only"}
    flip = []
    for label, r in report.items():
        if label in prior:
            same = r["most_protective"] == prior[label]
            if not same:
                flip.append(label)
            print(f"  {label:<26} 补 seed 前={prior[label]:<12} 补 seed 后={r['most_protective']:<12} "
                  f"{'✅ 未翻转' if same else '❌ **翻转**'}")
    if flip:
        print(f"\n  ⚠️ **以下骨干的排序发生翻转，须如实报告并降级结论**：{flip}")
    else:
        print("\n  ✅ 所有已补足 seed 的骨干排序**均未翻转**")

    if apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(
            {"report": report, "flipped": flip,
             "criterion": "最保护臂不得因补 seed 而改变"}, ensure_ascii=False, indent=1))
        print(f"  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
