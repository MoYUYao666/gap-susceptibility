# -*- coding: utf-8 -*-
r"""拆分后收尾：把旧合并图移入归档、更新图来源文档（2026-10-06）。

## 为什么

`fig8_weight_svd.png` 与 `fig9_noise_sensitivity.png` 已被拆成 6 张单面板图，
**LaTeX 不再引用**。留着会误导（看图录的人以为它还在用），故移入
`paper合/figures/_superseded/`（**不删，保留可回溯**）。

    python tools\_pa_split_cleanup.py [--apply]
"""
from __future__ import annotations

import io
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
FIGDIR = REPO / "paper合" / "figures"
ARCH = FIGDIR / "_superseded"

OLD = ["fig8_weight_svd.png", "fig8_weight_svd.pdf",
       "fig9_noise_sensitivity.png", "fig9_noise_sensitivity.pdf"]

ADD = r"""

---

## 2026-10-06 追加：附录 B 的 1×3 面板图**拆为单面板**（操作者建议）

> 操作者："**可以分成三个图片啊，没必要挤在一起**" —— **对**。

### 背景

`fig8` 与 `fig9` 是 **1×3 面板**，却挤在 **3.713 in 宽**的画布里 → **每面板仅 1.24 in 宽**，
标题/轴标签/图例必然重叠。这两张图因此一度**完全不可读**。

### 拆分结果

| 原图 | 拆成 | 内容 |
|---|---|---|
| `fig8_weight_svd` | **`fig8a_rank_delta`** | 严格冻结下视觉/文本侧**有效秩变化** |
| | **`fig8b_budget`** | **可训参数预算**（严格 vs 旧协议，log 轴） |
| | **`fig8c_vision_untouched`** | **收到更新的视觉张量数**（对照冻结总数） |
| `fig9_noise_sensitivity` | **`fig9a_noise_sweep`** | 修正探针：按 σ 分组的 R@1 变化 |
| | **`fig9b_sigma0_control`** | **σ=0 对照**（必须精确为 0） |
| | **`fig9c_ratio`** | 测得比值 **0.76×** vs 旧文声称的 **2.6×** |

每张 **3.710 × 2.670 in**，占版心宽 `0.78\textwidth`，**单张仅占版心高 31%** → 一页绰绰有余。

### 同时修正 `fig8` 原图注的**两处错误**

| 错误 | 实际 |
|---|---|
| 写 "**(A) … (B--D) …**"（**四个**面板） | 只有 **A/B/C 三个** |
| 描述为 "Mean $\|\Delta W\|_F$ per encoder … **SVD of weight updates**" | 实际画的是**有效秩变化、可训预算、视觉张量数**——**完全不符** |

拆开后各图注**逐张如实描述**，不再有面板字母错配。

### 旧的合并图

`fig8_weight_svd.*` 与 `fig9_noise_sensitivity.*` **已移入 `paper合/figures/_superseded/`**
（不删，保留可回溯），因为 LaTeX 不再引用、留着会误导。
"""


def main() -> int:
    apply = "--apply" in sys.argv
    ARCH.mkdir(exist_ok=True)
    moved = []
    for f in OLD:
        p = FIGDIR / f
        if p.exists():
            moved.append(f)
            if apply:
                shutil.move(str(p), str(ARCH / f))
    print(f"  移入 _superseded/：{len(moved)} 个 {moved}")

    if apply:
        # 核对：LaTeX 不再引用它们
        sup = io.open(REPO / "paper合" / "sections" / "supplement.tex", encoding="utf-8").read()
        for f in ("fig8_weight_svd", "fig9_noise_sensitivity"):
            assert f not in sup, f"LaTeX 仍引用 {f}"
        print("  ✅ LaTeX 已不引用旧合并图")

        # 图来源文档
        dp = REPO / "docs" / "PAPERA_FIGURE_PROVENANCE.md"
        t = io.open(dp, encoding="utf-8").read()
        if "附录 B 的 1×3 面板图" not in t:
            io.open(dp, "w", encoding="utf-8", newline="").write(t.rstrip() + ADD)
            t2 = io.open(dp, encoding="utf-8").read()
            for k in ("fig8a_rank_delta", "fig9c_ratio", "0.76", "B--D", "_superseded"):
                assert k in t2, f"断言失败：缺 {k}"
            print(f"  ✅ 图来源文档已追加（{len(t2.splitlines())} 行）")

        # 当前图的清单
        cur = sorted(p.name for p in FIGDIR.glob("*.png"))
        print(f"\n  paper合/figures/ 现有 {len(cur)} 张 PNG")
    else:
        print("  （预演，加 --apply）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
