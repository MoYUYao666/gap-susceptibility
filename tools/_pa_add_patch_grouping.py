# -*- coding: utf-8 -*-
r"""把 patch 尺寸分组写入设计模式①，并如实标注边界（2026-10-06）。

## 数据（`tools/_pa_four_backbone_analysis.py`，全部严格冻结）

| 骨干 | 架构 | rank | 最佳臂 |
|---|---|---|---|
| CLIP | patch32 | 4 / 8 | `text_only` |
| OpenCLIP | patch32 | 4 / 8 | `text_only` |
| SigLIP | patch16 | 4 / 8 | `both` |
| **BioCLIP** | **patch16** | 4 | **`both`**（ΔCG −0.4515） |

→ **7 个配置无例外**：patch32 → `text_only`；patch16 → `both`。

## 改法

设计模式①**已说**"两个 B/32 骨干排序相同、B/16 不同"。本次补入**第四个骨干（BioCLIP）**，
把"B/16 与 B/32 不同"升级为"**按 patch 尺寸分组，7 个配置无例外**"，
并**如实标注三条边界**：

1. **BioCLIP 仅 rank 4**（rank 8 未跑）；
2. **BioCLIP 是域外模型**（生物域预训练；在自然图像上初始 CG **1.79**，而 B/32 为 **0.81**）
   → **域偏移本身可能造成排序**，不能只归因 patch 尺寸；
3. **patch 尺寸与骨干身份未解耦**（每个尺寸各 2 个骨干，n=4）。

**故正文只写"按 patch 尺寸一致分组"，不写"patch 尺寸导致"。**

    python tools\_pa_add_patch_grouping.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "paper合" / "sections" / "empirical.tex"

OLD = (r"Under strict freezing the same three arms are ordered identically on both B/32 backbones and "
       r"differently on B/16, as Table~\ref{tab:position_strict} records. On the two B/32 backbones the "
       r"arm that minimises the gap (text-only) is the one that retrieves worst, so the ordering by gap "
       r"runs opposite to the ordering by retrieval; on SigLIP the two orderings agree and both place "
       r"the both-position arm first. The practical reading is that no adaptation site transfers across "
       r"backbones without measurement.")

NEW = (r"Under strict freezing the same three arms are ordered identically on both B/32 backbones and "
       r"differently on B/16, as Table~\ref{tab:position_strict} records, and a fourth backbone added to "
       r"test whether that split tracks patch size rather than backbone identity falls on the B/16 side: "
       r"across all seven strict-freezing configurations measured, every patch-32 backbone has the "
       r"text-only arm at the smallest gap change and every patch-16 backbone has the both-position arm "
       r"there, without exception. The added backbone is BioCLIP, a biological-domain model, and two "
       r"caveats follow from that. It was measured at rank~$4$ only, and it begins from a gap of $1.79$ "
       r"on natural images where the B/32 backbones begin at $0.81$, so domain shift alone could account "
       r"for its ordering; and with two backbones per patch size the two are not separated. We therefore "
       r"report the grouping as a regularity over seven configurations rather than as a property of patch "
       r"size. On the two B/32 backbones the arm that minimises the gap (text-only) is the one that "
       r"retrieves worst, so the ordering by gap runs opposite to the ordering by retrieval; on SigLIP the "
       r"two orderings agree and both place the both-position arm first. The practical reading is that no "
       r"adaptation site transfers across backbones without measurement.")


def main() -> int:
    apply = "--apply" in sys.argv
    t = io.open(F, encoding="utf-8").read()
    c = t.count(OLD)
    if c != 1:
        print(f"  ⚠ 未唯一命中（{c} 次）")
        return 1
    print("  ✅ 命中设计模式①的 strict-freezing 句")
    if apply:
        io.open(F, "w", encoding="utf-8", newline="").write(t.replace(OLD, NEW, 1))
        t2 = io.open(F, encoding="utf-8").read()
        for k in ("seven strict-freezing configurations", "BioCLIP", "1.79",
                  "not separated", "rather than as a property of patch"):
            assert k in t2, f"断言失败：缺 {k}"
        assert "0.81" in t2
        print("  ✅ 已写入 patch 尺寸分组 + 三条边界并断言通过")
    else:
        print("  （预演）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
