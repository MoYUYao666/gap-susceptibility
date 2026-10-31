# -*- coding: utf-8 -*-
r"""Paper A 整改 · 同步 fig9 图注（使其准确描述重建后的三格）。

旧图注（已改成半句）描述的是旧图的 (A) 2.6×；重建后图为三格：
  A 修正探针（5 seeds，σ=0/0.03/0.1）× 视/文
  B σ=0 对照（必须精确复现基线）
  C σ=0.1 的实测比值 vs 旧文声称的 2.6×

    python tools\_pa_fix_fig9_caption.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "paper合" / "sections" / "supplement.tex"

OLD = ("\\caption{Parameter noise sensitivity and effective rank tracking. (A) Parameter-noise probe; note "
       "that the corrected probe finds no stable ordering between encoders (see the withdrawn-evidence note "
       "in the main text), so this panel is retained for transparency only.")
NEW = ("\\caption{Parameter-noise probe, corrected design. (A) Retrieval degradation against noise scale for the "
       "vision and text encoders, five seeds each; the error bars overlap at every scale and their ordering is "
       "not stable, so no encoder is shown to be the more sensitive. (B) The $\\sigma{=}0$ control, which "
       "reproduces the baseline exactly in every run; this is what licenses the negative result in (A), since an "
       "earlier probe without image-set and augmentation control appeared to show vision-side degradation at "
       "$\\sigma{=}0$ where none can exist. (C) The measured vision-to-text ratio at $\\sigma{=}0.1$ ($0.76$), "
       "against the $2.6\\times$ claimed by that earlier probe; the claim is withdrawn and the line of evidence "
       "is not used.")


def main() -> int:
    apply = "--apply" in sys.argv
    t = io.open(F, encoding="utf-8").read()
    if OLD not in t:
        print("  ⚠ 未命中旧图注；当前 fig9 图注：")
        i = t.find("fig9_noise_sensitivity")
        j = t.find("\\caption{", i)
        print("    " + t[j:j + 260].replace("\n", " ") if j > 0 else "（未找到）")
        return 1
    print("  ✅ 命中旧图注，将替换为准确描述三格的新图注")
    if apply:
        io.open(F, "w", encoding="utf-8", newline="").write(t.replace(OLD, NEW, 1))
        t2 = io.open(F, encoding="utf-8").read()
        assert "corrected design" in t2 and "retained for transparency only" not in t2
        print("  ✅ 已改并断言通过")
    else:
        print("  （预演，加 --apply 生效）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
