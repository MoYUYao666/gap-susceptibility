# -*- coding: utf-8 -*-
r"""把剩余的笼统表述 "mean $R^2 > 0.96$" 统一为实测精确值（2026-10-02）。

背景：CLIP 侧 ODE 拟合（`beta_results.json` 的 `exponential_fit.r_squared`）实测
**LoRA 子集 n=6，mean 0.9855（≈0.986），range 0.9777–0.9965**；full_ft 组 mean 0.9223。
正文原先写 "mean $R^2 > 0.96$"，既笼统又把 full_ft 混入会掉到 0.9644。

    python tools\_pa_unify_r2_wording.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
S = REPO / "paper合" / "sections"

EDITS = [
    ("conclusion.tex",
     "The framework predicts gap trajectories with mean $R^2 > 0.96$, substantially outperforming",
     "The framework predicts gap trajectories at mean $R^2 = 0.986$ over the LoRA configurations "
     "(range $0.978$--$0.997$), substantially outperforming"),
    ("discussion.tex",
     "While the strong empirical agreement (mean $R^2 > 0.96$) validates this approximation",
     "While the strong empirical agreement (mean $R^2 = 0.986$ over the LoRA configurations) validates "
     "this approximation"),
    ("introduction.tex",
     "mean $R^2 > 0.96$",
     "mean $R^2 = 0.986$ over the LoRA configurations"),
    ("main_springer.tex",
     "mean $R^2 > 0.96$",
     "mean $R^2 = 0.986$ over the LoRA configurations"),
]


def main() -> int:
    apply = "--apply" in sys.argv
    n = 0
    for fname, old, new in EDITS:
        p = (REPO / "paper合" / fname) if fname.startswith("main_") else (S / fname)
        if not p.exists():
            print(f"  ⚠ 缺文件 {fname}")
            continue
        t = io.open(p, encoding="utf-8").read()
        c = t.count(old)
        if c >= 1:
            print(f"  ✅ {fname}: 命中 {c} 处")
            if apply:
                io.open(p, "w", encoding="utf-8", newline="").write(t.replace(old, new))
            n += 1
        else:
            # 退一步用通用模式
            c2 = t.count("mean $R^2 > 0.96$")
            print(f"  {'✅' if c2 else '⚠'} {fname}: 精确串未命中，通用串 {c2} 处")
            if apply and c2:
                io.open(p, "w", encoding="utf-8", newline="").write(
                    t.replace("mean $R^2 > 0.96$",
                              "mean $R^2 = 0.986$ over the LoRA configurations"))
                n += 1
    if apply:
        left = 0
        for f in list(S.glob("*.tex")) + [REPO / "paper合" / "main_springer.tex",
                                          REPO / "paper合" / "main_nc.tex"]:
            if f.exists():
                left += io.open(f, encoding="utf-8").read().count("mean $R^2 > 0.96$")
        print(f"\n  ✅ 已改 {n} 处；全文残留 'mean $R^2 > 0.96$': {left} 处")
    else:
        print(f"\n  {n} 处可改（预演，加 --apply 生效）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
