# -*- coding: utf-8 -*-
r"""精确化最后两处笼统的 R² 表述（2026-10-02）。

## 两处

1. `conclusion.tex` 之外的 **`discussion.tex:5`**：
   > "mean $R^2 > 0.96$ across all CLIP LoRA configurations tested (**and $0.943$ on the OpenCLIP
   > BitFit runs**)."

   措辞把 0.943 作为附注并列，读者会误以为也达标。**0.943 < 0.96**，应明确标出。

2. **摘要（`main_nc.tex` / `main_springer.tex`）**：`mean $R^2 > 0.96$` → 精确值。

## 实测口径（`tools/_pa_clip_ode_r2.py`）

- CLIP LoRA 子集：n=6，mean **0.9855 ≈ 0.986**，range 0.9777–0.9965
- CLIP full_ft 组：n=3，mean 0.9223

    python tools\_pa_fix_last_r2.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PA = REPO / "paper合"

EDITS = [
    (PA / "sections" / "discussion.tex",
     "affirmative: mean $R^2 > 0.96$ across all CLIP LoRA configurations tested (and $0.943$ on the "
     "OpenCLIP BitFit runs).",
     "affirmative for the LoRA configurations: mean $R^2 = 0.986$ (range $0.978$--$0.997$) across the CLIP "
     "runs tested. The OpenCLIP BitFit runs sit below that band at $0.943$, and the CLIP "
     "full-fine-tuning pilot below both, at $0.922$; both are reported in Section~\\ref{sec:validation}."),
    (PA / "main_nc.tex",
     "predicts the full gap trajectory at mean $R^2 > 0.96$ across all tested LoRA configurations",
     "predicts the full gap trajectory at mean $R^2 = 0.986$ across the tested LoRA configurations"),
    (PA / "main_springer.tex",
     "predicts the full gap trajectory at mean $R^2 > 0.96$ across all tested LoRA configurations",
     "predicts the full gap trajectory at mean $R^2 = 0.986$ across the tested LoRA configurations"),
]


def main() -> int:
    apply = "--apply" in sys.argv
    n = 0
    for p, old, new in EDITS:
        if not p.exists():
            print(f"  ⚠ 缺 {p.name}")
            continue
        t = io.open(p, encoding="utf-8").read()
        c = t.count(old)
        if c == 1:
            print(f"  ✅ {p.name}")
            if apply:
                io.open(p, "w", encoding="utf-8", newline="").write(t.replace(old, new, 1))
            n += 1
        else:
            print(f"  ⚠ {p.name}: 命中 {c} 次，跳过")
    if apply:
        left = 0
        for f in list((PA / "sections").glob("*.tex")) + [PA / "main_nc.tex", PA / "main_springer.tex"]:
            left += io.open(f, encoding="utf-8").read().count("mean $R^2 > 0.96$")
        print(f"\n  ✅ 已改 {n} 处；全文残留: {left} 处")
        assert left == 0, "仍有笼统表述"
    else:
        print(f"\n  {n} 处可改（预演）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
