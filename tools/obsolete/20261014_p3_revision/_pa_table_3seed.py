# -*- coding: utf-8 -*-
r"""把 `tab:position_strict` 的两个 `r4` 行从**单 seed**换为**3-seed 均值**，并改表注（2026-10-10）。

## 为什么

表注说 *"The $\dagger$ rows are **single-seed** runs … whereas the archived rows are **five-seed** means"*。
**但我现在每个 r4 都有 3 个 seed** → **用均值更稳健**，且表注可如实写"r4 为 3-seed 均值"。

## 实测（`tools/_p89_table_caliber.py`）

| (骨干,臂) | 稿件（=seed42） | **3-seed 均值** |
|---|---|---|
| B/32 r4 text_only | −0.0297 / 0.625 | **−0.0288 / 0.621** |
| B/32 r4 both | −0.0186 / 0.680 | **−0.0188 / 0.679** |
| B/32 r4 vision_only | +0.0124 / 0.668 | **+0.0127 / 0.670** |
| B/16 r4 text_only | −0.0190 / 0.642 | **−0.0172 / 0.651** |
| B/16 r4 both | +0.0150 / 0.696 | **+0.0107 / 0.707** |
| B/16 r4 vision_only | +0.0433 / 0.677 | **+0.0313 / 0.686** |

**粗体（每行最小 CGΔ）需随之移动**：B/16 `both` 行原本粗体在 text_only（−0.0190），
换均值后 text_only（−0.0172）仍最小 → 粗体位置不变。

    python tools\_pa_table_3seed.py [--apply]
"""
from __future__ import annotations

import glob
import io
import json
import statistics as st
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "paper合" / "sections" / "empirical.tex"

OLD_B32 = (r"CLIP B/32$^\dagger$ (WIT) & 32 & $\mathbf{-0.0297}$ / $0.625$ & "
           r"$-0.0186$ / $\mathbf{0.680}$ & $+0.0124$ / $0.668$ \\")
OLD_B16 = (r"CLIP B/16$^\dagger$ (WIT) & 16 & $\mathbf{-0.0190}$ / $0.642$ & "
           r"$+0.0150$ / $\mathbf{0.696}$ & $+0.0433$ / $0.677$ \\")

OLD_CAP = (r"The $\dagger$ rows are single-seed runs under the same protocol, whereas the "
           r"archived rows are five-seed means; on CLIP B/32 the seed-to-seed standard "
           r"deviation is $0.003$, so the gaps those single runs separate are several times "
           r"that spread.")


def means(root, arm, pat="seed*"):
    xs_cg, xs_r1 = [], []
    for f in sorted(glob.glob(str(REPO / root / arm / pat / "results.json"))):
        d = json.loads(io.open(f, encoding="utf-8").read())
        xs_cg.append(d["final_gap"]["centroid_gap"] - d["initial_gap"]["centroid_gap"])
        xs_r1.append(d["final_task_metrics"]["R@1"])
    return (st.mean(xs_cg), st.mean(xs_r1), len(xs_cg)) if xs_cg else (float("nan"),) * 3


def fmt_row(label, patch, vals):
    """vals = [(cg, r1), ...] 对应 text_only / both / vision_only"""
    cells = []
    min_i = min(range(len(vals)), key=lambda i: vals[i][0])
    for i, (cg, r1, _n) in enumerate(vals):
        c = f"${cg:+.4f}$"
        r = f"${r1:.3f}$"
        if i == min_i:
            c = f"$\\mathbf{{{cg:+.4f}}}$"
        cells.append(f"{c} / {r}")
    return f"{label} & {patch} & " + " & ".join(cells) + r" \\"


def main() -> int:
    apply = "--apply" in sys.argv
    print("=== 计算 3-seed 均值 ===")
    b32 = [means("outputs/strict_freeze_b32_r4", a) for a in
           ("text_only", "both", "vision_only")]
    b16 = [means("outputs/strict_freeze_b16/r4", a) for a in
           ("text_only", "both", "vision_only")]
    for tag, v in (("B/32 r4", b32), ("B/16 r4", b16)):
        for arm, (cg, r1, n) in zip(("text_only", "both", "vision_only"), v):
            print(f"  {tag} {arm:<12} CGΔ={cg:+.4f}  R@1={r1:.3f}  (n={n})")
    assert all(v[2] == 3 for v in b32 + b16), "有 r4 配置不是 3 seed"

    new32 = fmt_row(r"CLIP B/32$^\dagger$ (WIT)", 32, b32)
    new16 = fmt_row(r"CLIP B/16$^\dagger$ (WIT)", 16, b16)
    print(f"\n  新 B/32 行: {new32}")
    print(f"  新 B/16 行: {new16}")

    new_cap = (r"The $\dagger$ rows are three-seed means under the same protocol, as are the "
               r"archived rows, which use five seeds; on CLIP B/32 the seed-to-seed standard "
               r"deviation is $0.001$--$0.002$, so the gaps between arms are several times "
               r"that spread.")

    t = io.open(F, encoding="utf-8").read()
    if OLD_B32 not in t and OLD_B16 not in t:
        print("  两个表行都已改，跳过")
        return 0
    _pairs = [(OLD_B32, new32, "B/32 行"), (OLD_B16, new16, "B/16 行")]
    if OLD_CAP in t:
        _pairs.append((OLD_CAP, new_cap, "表注"))
    for old, new, tag in _pairs:
        if t.count(old) != 1:
            print(f"  ❌ {tag} 锚点未唯一命中（{t.count(old)}）")
            return 1
        t = t.replace(old, new, 1)
    if not apply:
        print("  （预演）")
        return 0
    io.open(F, "w", encoding="utf-8", newline="").write(t)
    t2 = io.open(F, encoding="utf-8").read()
    for k in ("three-seed means", "-0.0288", "+0.0107", "+0.0313"):
        assert k in t2, f"断言失败：缺 {k}"
    print("  ✅ empirical.tex：两个 r4 行改 3-seed 均值，表注同步更新")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
