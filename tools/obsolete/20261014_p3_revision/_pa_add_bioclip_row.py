# -*- coding: utf-8 -*-
r"""把 BioCLIP 行补进 `tab:position_strict`，使表格能支撑正文的"7 个配置"（2026-10-06）。

## 为什么必须补

`tools/_pa_add_patch_grouping.py` 已把正文改为：

> "across all **seven strict-freezing configurations** measured, every patch-32 backbone has the
> text-only arm at the smallest gap change and every patch-16 backbone has the both-position arm there,
> without exception."

但 `tab:position_strict` **只有 3 行**（CLIP、OpenCLIP、SigLIP）→ **正文超表所载**。

## BioCLIP 数据（rank 4，3 seeds）

| 臂 | ΔCG | R@1 |
|---|---|---|
| text_only | −0.3671 | ⚠ **未记录** |
| both | −0.4515 | ⚠ **未记录** |
| vision_only | −0.2927 | ⚠ **未记录** |

**诚实处理**：`_exp3_bioclip_strict.py` **没有记录 R@1**（只算了 ΔCG）。
故该行的 R@1 列写 **`---`** 并**在表注说明原因**——**绝不编造数字**。

## 表的结构调整

表头加一列 **rank**（因为 BioCLIP 只有 rank 4，而其余骨干是 rank 8），
并加一列/备注标明 patch 尺寸，使"按 patch 尺寸分组"在读表时即可见。

    python tools\_pa_add_bioclip_row.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "paper合" / "sections" / "empirical.tex"

OLD_CAP = ("The three adaptation positions under strict freezing, where the optimiser sees only the adapter\n"
           "matrices and the arms therefore differ solely in where those adapters sit. Each entry is $\\Delta$CG with\n"
           "$R@1$ beneath it, over five seeds at 5000 samples and 10 epochs with rank $8$ and $\\alpha=16$; negative\n"
           "$\\Delta$CG means the gap narrowed. The arms are ordered by $\\Delta$CG identically on both B/32 backbones,\n"
           "and on those two backbones that ordering is the reverse of the ordering by $R@1$; SigLIP orders them\n"
           "differently on both counts.}")

NEW_CAP = ("The three adaptation positions under strict freezing, where the optimiser sees only the adapter\n"
           "matrices and the arms therefore differ solely in where those adapters sit. Each entry is $\\Delta$CG with\n"
           "$R@1$ beneath it (bold marks the smallest $\\Delta$CG in the row), at 5000 samples and 10 epochs with\n"
           "$\\alpha=2r$; negative $\\Delta$CG means the gap narrowed. The patch column is what the ordering tracks:\n"
           "every patch-32 backbone puts text-only smallest and every patch-16 backbone puts both there. The arms\n"
           "are ordered by $\\Delta$CG identically on both B/32 backbones, and on those two backbones that ordering\n"
           "is the reverse of the ordering by $R@1$; SigLIP orders them differently on both counts. BioCLIP was\n"
           "measured at rank~$4$ over three seeds and its retrievals were not recorded, so those cells are left\n"
           "blank rather than estimated; its pre-training corpus is biological, so its absolute $\\Delta$CG is not\n"
           "comparable with the others and only its within-row ordering is used.}")

OLD_TBL = (r"\begin{tabular}{lccc}" "\n"
           r"\toprule" "\n"
           r"Backbone (pre-training) & Text-only & Both & Vision-only \\" "\n"
           r"\midrule" "\n"
           r"CLIP ViT-B/32 (WIT)        & $\mathbf{-0.0465}$ / $0.624$ & $-0.0258$ / $\mathbf{0.693}$ & $+0.0106$ / $0.680$ \\" "\n"
           r"OpenCLIP ViT-B/32 (LAION)  & $\mathbf{+0.0694}$ / $0.643$ & $+0.0881$ / $\mathbf{0.680}$ & $+0.0925$ / $0.672$ \\" "\n"
           r"SigLIP ViT-B/16            & $+0.0664$ / $0.432$ & $\mathbf{-0.0114}$ / $\mathbf{0.619}$ & $+0.0522$ / $0.341$ \\" "\n"
           r"\bottomrule")

NEW_TBL = (r"\begin{tabular}{llccc}" "\n"
           r"\toprule" "\n"
           r"Backbone & Patch & Text-only & Both & Vision-only \\" "\n"
           r"\midrule" "\n"
           r"CLIP ViT-B/32 (WIT)       & $32$ & $\mathbf{-0.0465}$ / $0.624$ & $-0.0258$ / $\mathbf{0.693}$ & $+0.0106$ / $0.680$ \\" "\n"
           r"OpenCLIP ViT-B/32 (LAION) & $32$ & $\mathbf{+0.0694}$ / $0.643$ & $+0.0881$ / $\mathbf{0.680}$ & $+0.0925$ / $0.672$ \\" "\n"
           r"\midrule" "\n"
           r"SigLIP ViT-B/16           & $16$ & $+0.0664$ / $0.432$ & $\mathbf{-0.0114}$ / $\mathbf{0.619}$ & $+0.0522$ / $0.341$ \\" "\n"
           r"BioCLIP ViT-B/16 (bio.)   & $16$ & $-0.3671$ / --- & $\mathbf{-0.4515}$ / --- & $-0.2927$ / --- \\" "\n"
           r"\bottomrule")


def main() -> int:
    apply = "--apply" in sys.argv
    t = io.open(F, encoding="utf-8").read()
    n = 0
    for old, new, why in ((OLD_CAP, NEW_CAP, "表注（补 patch 列说明 + BioCLIP 边界）"),
                          (OLD_TBL, NEW_TBL, "表体（加 Patch 列 + BioCLIP 行）")):
        if old in t:
            print(f"  ✅ {why}")
            if apply:
                t = t.replace(old, new, 1)
            n += 1
        else:
            print(f"  ⚠ {why}：未命中")
    if apply and n == 2:
        io.open(F, "w", encoding="utf-8", newline="").write(t)
        t2 = io.open(F, encoding="utf-8").read()
        for k in ("BioCLIP ViT-B/16 (bio.)", "$-0.4515$", "Patch", "not recorded", "not comparable"):
            assert k in t2, f"断言失败：缺 {k}"
        assert t2.count("---") >= 3, "BioCLIP 的 R@1 应留空"
        print("  ✅ 已改并断言通过（BioCLIP 行 R@1 留空，未编造）")
    else:
        print(f"\n  {n}/2 处（{'预演' if not apply else '部分失败'}）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
