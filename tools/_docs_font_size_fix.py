# -*- coding: utf-8 -*-
r"""记录字体/尺寸统一（2026-10-06，操作者要求）。

    python tools\_docs_font_size_fix.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ADD = r"""

---

## 2026-10-06 追加：字体统一为 Times New Roman，尺寸精确对齐

> 操作者："**图片啥的文字也要 times new roman，然后大小你要调整好**"

### 问题（实测）

| 项 | 现状 | 应为 |
|---|---|---|
| **字体** | matplotlib 默认 **DejaVu Sans**（`pdffonts` 实测） | **Times New Roman**（与正文一致） |
| **尺寸** | 各图在**任意画布**画出、LaTeX 再缩放，且**倍率各不相同**（`fig8` ×0.28、`fig10` ×0.48、`fig1` ×0.75） | **按最终尺寸出图，1.00×** |

**→ 同一张稿子里图的字号相差 3 倍**——这正是"大小没调整好"的表现。

### 修法

1. **`tools/figure_style.py`** 统一配置：
   - `font.family = serif` + Times 系列；`mathtext.fontset = stix`（与 Times 同源）；
   - 字号按**最终尺寸**定：刻度/轴标签 **9 pt**、图例 **8 pt**（均 ≥6 pt）；
   - `savefig.bbox = None` + `constrained_layout`——**避免 tight bbox 按内容外扩**
     （实测 `fig8` 曾因此偏大 1.46×，反而要 LaTeX 再缩 0.68×）。
2. **按 LaTeX 里的实际宽度出图**（`\textwidth = 342.7 pt = 4.760 in`，像素法实测）：
   `0.88\textwidth → 4.189 in`、`0.78\textwidth → 3.713 in`；
3. **同时导出 PDF 矢量版**（供后续把 LaTeX 从 PNG 切到矢量）。

### 结果（实测）

**尺寸**：12/12 图**缩放全部 1.00×**（目标与实际差 ≤0.003 in）

**字体**：`pdffonts` 实测全部为 **TimesNewRomanPSMT**
（数学符号为 STIXGeneral，与 Times 同源）

### 踩坑记录（同一类作用域错误连犯三次）

| # | 错误 | 原因 |
|---|---|---|
| ① | `NameError: figsize_full` | 共享样式在 `main()` 内 import，但绘图在**模块级函数**里 |
| ② | `NameError: sys` | 把 `sys.path.insert` 插到了 `import sys` **之前** |
| ③ | 图仍是 DejaVu | `apply_style()` 在重写 import 块时**被删掉**（4 个脚本从未调用） |

**对策**：
- import 全部提到**模块层**并**固定顺序**；
- 加 **import 冒烟测试**（`_pa_fix_import_order.py`）；
- 字体用 **`pdffonts` 实测**验证——**不靠"我设了就应该生效"**。
"""


def main() -> int:
    apply = "--apply" in sys.argv
    p = REPO / "docs" / "PAPERA_FIGURE_PROVENANCE.md"
    t = io.open(p, encoding="utf-8").read()
    if "字体统一为 Times New Roman" in t:
        print("  已记录，跳过")
        return 0
    if not apply:
        print("  （预演）")
        return 0
    io.open(p, "w", encoding="utf-8", newline="").write(t.rstrip() + ADD)
    t2 = io.open(p, encoding="utf-8").read()
    for k in ("TimesNewRomanPSMT", "1.00×", "stix", "pdffonts", "作用域错误连犯三次"):
        assert k in t2, f"断言失败：缺 {k}"
    print(f"  ✅ 已追加（{len(t2.splitlines())} 行）")

    hp = REPO / "HANDOFF.md"
    h = io.open(hp, encoding="utf-8").read()
    ent = r"""> **🔤 2026-10-06 —— 图字体改 Times New Roman + 尺寸精确对齐（操作者要求）**
>
> 操作者："**图片啥的文字也要 times new roman，然后大小你要调整好**"。
>
> ### 问题（实测，非推测）
>
> | 项 | 现状 | 应为 |
> |---|---|---|
> | **字体** | matplotlib 默认 **DejaVu Sans**（`pdffonts` 实测确认） | **Times New Roman**（与 `elsarticle` 正文一致） |
> | **尺寸** | 各图在**任意画布**下画、LaTeX 再缩放，**倍率各异**（`fig8` ×0.28、`fig10` ×0.48、`fig1` ×0.75） | **按最终尺寸出图，1.00×** |
>
> **→ 同一稿子里图的字号差 3 倍**，这正是"大小没调整好"。
>
> ### 修法
>
> - `tools/figure_style.py`：Times 系列 + `mathtext.fontset=stix`；
>   字号按最终尺寸定（刻度/轴标签 9 pt、图例 8 pt，均 ≥6 pt）；
>   **`savefig.bbox=None` + `constrained_layout`**——tight bbox 会按内容外扩（实测 fig8 因此偏大 1.46×）；
> - 按 LaTeX 实际宽度出图（`\textwidth = 342.7 pt = 4.760 in`，像素法实测）：
>   **0.88 → 4.189 in**、**0.78 → 3.713 in**；
> - 同时导出 **PDF 矢量版**。
>
> ### 结果（实测）
>
> - **尺寸：12/12 图缩放全部 1.00×**（差 ≤0.003 in）
> - **字体：`pdffonts` 实测全部 `TimesNewRomanPSMT`**（数学为 STIXGeneral，与 Times 同源）
> - 编译：NC **45 页** / Springer **33 页**、0 错误、0 未定义引用；**像素法复核无页越界**；投稿包已重建
>
> ### ⚠️ 同一类作用域错误**连犯三次**（记录以示警觉）
>
> | # | 错误 | 原因 |
> |---|---|---|
> | ① | `NameError: figsize_full` | 样式在 `main()` 内 import，绘图却在**模块级函数**里 |
> | ② | `NameError: sys` | 把 `sys.path.insert` 插到 `import sys` **之前** |
> | ③ | 图仍是 DejaVu | `apply_style()` 在重写 import 块时**被删掉**（4 个脚本从未调用） |
>
> **对策**：import 提到模块层并固定顺序；加 **import 冒烟测试**；
> **字体用 `pdffonts` 实测**——不靠"我设了就应该生效"。
"""
    if "图字体改 Times New Roman" not in h:
        anchor = "> **🎨 2026-10-06 —— 表格溢出"
        i = h.find(anchor)
        if i > 0:
            io.open(hp, "w", encoding="utf-8", newline="").write(h[:i] + ent + h[i:])
            h2 = io.open(hp, encoding="utf-8").read()
            for k in ("TimesNewRomanPSMT", "1.00×", "连犯三次", "pdffonts"):
                assert k in h2, f"HANDOFF 断言失败：缺 {k}"
            print(f"  ✅ HANDOFF 已追加（{len(h2.splitlines())} 行）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
