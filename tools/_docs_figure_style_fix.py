# -*- coding: utf-8 -*-
r"""把 2026-10-06 的图例/配色/表格修复追加进 `docs/PAPERA_FIGURE_PROVENANCE.md`。

    python tools\_docs_figure_style_fix.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ADD = r"""

---

## 2026-10-06 追加：图例遮挡、配色统一、以及一处**真实表格溢出**

> 操作者指出："**表格溢出的部分**"、"**图片有的图例会挡住图片**"、"**图片的配色不高级**"。

### A. 表格溢出（**真越界**，已修）

我先前曾判断 `Overfull \hbox` 是"度量噪声"——**那次判断是错的**。
改用**像素法**（`tools/_measure_textblock.py`：把页面渲染成位图，量非白像素范围），
证明**确有三处真越界**：

| 表 | 原超出 | 修法 |
|---|---|---|
| `tab:position_strict` | **+97.9 pt** | 标签缩短（`CLIP B/32`）、`\footnotesize`、`\tabcolsep 4pt`、`@{}` 去边距 |
| `tab:phase2` | +20.9 pt | 同上 |
| `tab:generalization` | +20.9 pt | 同上 |

**修后实测**：右界范围 **476.6 ~ 478.1 pt**（版心右界 476.6）→ **无页越界**。
脚本：`tools/_fix_wide_tables.py`、`tools/_measure_textblock.py`。

### B. `fig4.png` 曾是**坏图**（已重做）

| 项 | 原图 | 现图 |
|---|---|---|
| 内容 | Adapter **β vs dim** | **跨方法比较**（图注声称的） |
| **图例** | **`False` / `True`**（布尔值直接当标签） | `LoRA` / `Adapter` |
| y 轴 | 到 **68** | ΔCG（−0.05 ~ +0.23） |
| 数据 | β 中位数 **0.50**、最大 **337** → **拟合失败值** | `outputs/analysis/adapter_common_baseline.json` + `outputs/strict_freeze` |

**新图**（`tools/_pa_rebuild_fig4_crossmethod.py`）：横向柱，LoRA 三臂
（−0.047 / −0.026 / +0.011）vs Adapter 两臂（+0.185 / +0.229），零线标出，图例置于轴外。
**这正是图注声称的模式**：LoRA 保对齐、Adapter 无一致的 text-only 优势。

### C. 配色统一为 **Okabe-Ito**（色盲友好国际标准）

定义在 **`tools/figure_style.py`**（含语义映射，保证同一概念跨图同色）：

| 语义 | 色值 |
|---|---|
| text-only / LoRA / 实测 | `#0072B2` 蓝 |
| both / Adapter / 预测对照 | `#D55E00` 朱红 |
| vision-only | `#009E73` 绿 |
| Frozen / 基准 | `#666666` 灰 |

**并加冗余编码**（线型 / 斜纹）——灰度打印或色觉异常读者仍可区分。
脚本：`tools/_pa_unify_figure_style.py`、`tools/_pa_apply_palette_to_overflow.py`、
`tools/_pa_fig1_semantic_colors.py`。

### D. 图例遮挡整改（逐张目视复核）

| 图 | 改动 |
|---|---|
| `fig4` | `lower right`（**压在柱上**）→ **轴外上方** |
| `fig12` | 轴内 → **轴下方**（数据柱从 0 起，轴内无空白） |
| `fig14` | `center right` → **左上** |
| `fig1` | 图例在空白区；**加线型冗余编码**（Full FT 点线 / text-only 实线 / both 虚线） |
| `fig10` / `fig2_v5_falsification` / `fig4_effective_rank` | 图例均在空白区，复核通过 |
"""


def main() -> int:
    apply = "--apply" in sys.argv
    p = REPO / "docs" / "PAPERA_FIGURE_PROVENANCE.md"
    t = io.open(p, encoding="utf-8").read()
    if "2026-10-06 追加：图例遮挡" in t:
        print("  已记录，跳过")
        return 0
    if not apply:
        print("  （预演）")
        return 0
    io.open(p, "w", encoding="utf-8", newline="").write(t.rstrip() + ADD)
    t2 = io.open(p, encoding="utf-8").read()
    for k in ("+97.9 pt", "False` / `True", "#0072B2", "轴外上方", "无页越界"):
        assert k in t2, f"断言失败：缺 {k}"
    print(f"  ✅ 已追加（{len(t2.splitlines())} 行）")

    # HANDOFF
    hp = REPO / "HANDOFF.md"
    h = io.open(hp, encoding="utf-8").read()
    ent = r"""> **🎨 2026-10-06 —— 表格溢出（真越界）+ 图例遮挡 + 配色统一**
>
> 操作者："先不着急投稿，先把表格溢出的部分修改好，同时图片有的图例会挡住图片，同时图片的配色不高级"。
>
> ### ① 表格溢出：**我先前判断错了**
>
> 我曾说那些 `Overfull \hbox` 是"LaTeX 对浮动体盒子的度量噪声"——**错**。
> 改用**像素法**（`tools/_measure_textblock.py`：渲染位图后量非白像素范围）证明**真有三处越界**：
>
> | 表 | 超出 | 修法 |
> |---|---|---|
> | `tab:position_strict` | **+97.9 pt** | 标签缩短 + `\footnotesize` + `\tabcolsep 4pt` + `@{}` |
> | `tab:phase2` | +20.9 pt | 同上 |
> | `tab:generalization` | +20.9 pt | 同上 |
>
> **修后**：右界 476.6 ~ 478.1 pt（版心右界 476.6）→ **无页越界**。
> **教训：判决"是否越界"必须用像素法，不能凭日志或目视印象。**
>
> ### ② `fig4.png` 是**坏图**，已重做
>
> | 项 | 原图 | 现图 |
> |---|---|---|
> | 内容 | Adapter β vs dim | **跨方法比较**（图注声称的） |
> | 图例 | **`False` / `True`**（布尔当标签） | `LoRA` / `Adapter` |
> | y 轴 | 到 68 | ΔCG（−0.05 ~ +0.23） |
> | 数据 | β 中位数 0.50、最大 **337**（**拟合失败值**） | 共同基准的 ΔCG |
>
> ### ③ 配色统一为 Okabe-Ito（`tools/figure_style.py`）+ 线型冗余编码
>
> 蓝 `#0072B2`（text-only/LoRA/实测）｜朱红 `#D55E00`（both/Adapter/预测）｜
> 绿 `#009E73`（vision-only）｜灰 `#666666`（Frozen/基准）。
>
> ### ④ 图例遮挡逐张整改并目视复核
>
> `fig4` 图例压在柱上 → 轴外上方；`fig12` → 轴下方；`fig14` → 左上；
> `fig1`/`fig10`/`fig2_v5`/`fig4_effective_rank` 复核通过。
>
> ### ⑤ 编译
>
> NC **45 页**、Springer **33 页**、0 错误、0 未定义引用；投稿包已重建。
>
> 详见 `docs/PAPERA_FIGURE_PROVENANCE.md`。
"""
    if "表格溢出（真越界）" not in h:
        anchor = "> **🗄️ 2026-10-06 —— ap3 归档进 `备选/`"
        i = h.find(anchor)
        if i > 0:
            io.open(hp, "w", encoding="utf-8", newline="").write(h[:i] + ent + h[i:])
            h2 = io.open(hp, encoding="utf-8").read()
            for k in ("+97.9 pt", "像素法", "Okabe-Ito", "布尔当标签"):
                assert k in h2, f"HANDOFF 断言失败：缺 {k}"
            print(f"  ✅ HANDOFF 已追加（{len(h2.splitlines())} 行）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
