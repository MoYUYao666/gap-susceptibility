# -*- coding: utf-8 -*-
r"""记录 B-3/B-4（切矢量 + 清理）到图来源文档（2026-10-06）。

    python tools\_docs_vector_switch.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ADD = r"""

---

## 2026-10-06 追加：切矢量 PDF + 清理目录（B-3 / B-4）

### B-4：`\includegraphics` 由 `.png` 改为 `.pdf`（**矢量**）

16 张图全部已有 PDF 矢量版 → LaTeX 改用 `.pdf`，**任意缩放不糊**，期刊排版也偏好矢量。

**关键前提**：`fig1` / `fig3` 当时**缺 PDF**——因为它们的保存语句是
`fig.savefig(...)` 而非共享的 `save()`（后者才同时写 PNG+PDF）。已改为 `save()`。

**验证**：
- 编译 **0 错误**；
- `pdffonts` 确认图内字体仍嵌入；
- `pdfimages` 显示稿件 PDF 内仅剩 **4 个极小的 1-bit 位图对象**（299 ppi、约 1 KB），
  **线条 / 文字 / 坐标轴均为矢量**。

### B-3：下线图归档

| 类别 | 数量 | 处置 |
|---|---|---|
| 正文未引用的 PNG | **15** | → `figures/_superseded/` |
| 从未被引用的 SVG（8 月遗留） | **7** | → `figures/_superseded/` |

**`figures/` 现在是精确的「16 张图 × (PDF + PNG)」**，无多余文件。

### 顺带修掉打包脚本的**两个累积型缺陷**

| # | 缺陷 | 后果 |
|---|---|---|
| ① | `copytree(dirs_exist_ok=True)` **把 `_superseded/` 也打进投稿包** | 包里混入下线图 |
| ② | `srcdir` **未先清空**，而 `copytree` **只增不删** → 历次构建的旧图**累积** | zip 里多出 **33 个已下线 PNG**，虚增约 2 MB |

**修后**：`latex_source.zip` **5.4 MB → 1.1 MB**，包内 `figures/` 恰为 **32 个文件**
（16 张图的 PDF + PNG），**不含 `_superseded/`**。

> **教训**：这两个缺陷都是「**只增不删**」造成的——与正文里反复出现的
> 「只追加不核对」是同一类。**凡有累积的目录，构建前必须清空。**
"""


def main() -> int:
    apply = "--apply" in sys.argv
    p = REPO / "docs" / "PAPERA_FIGURE_PROVENANCE.md"
    t = io.open(p, encoding="utf-8").read()
    if "切矢量 PDF + 清理目录" in t:
        print("  已记录，跳过")
        return 0
    if not apply:
        print("  （预演）")
        return 0
    io.open(p, "w", encoding="utf-8", newline="").write(t.rstrip() + ADD)
    t2 = io.open(p, encoding="utf-8").read()
    for k in ("矢量", "_superseded", "5.4 MB → 1.1 MB", "只增不删", "16 张图 × (PDF + PNG)"):
        assert k in t2, f"断言失败：缺 {k}"
    print(f"  ✅ 已追加（{len(t2.splitlines())} 行）")

    hp = REPO / "HANDOFF.md"
    h = io.open(hp, encoding="utf-8").read()
    ent = r"""> **📐 2026-10-06 —— 图切矢量 PDF + 清理下线图 + 修打包脚本的累积缺陷（B-3 / B-4）**
>
> ### B-4：`\includegraphics` 由 `.png` → **`.pdf`（矢量）**
>
> 16 张图全部改用矢量 PDF（**任意缩放不糊**，期刊更偏好）。
>
> **前提修复**：`fig1` / `fig3` 当时**缺 PDF**——它们的保存语句是 `fig.savefig(...)`，
> 而非共享的 `save()`（后者才同时写 PNG+PDF）。已改为 `save()` 并重出。
>
> **验证**：编译 0 错误 ｜ `pdffonts` 确认图内字体嵌入 ｜
> `pdfimages` 显示稿件内仅剩 **4 个极小 1-bit 位图**（299 ppi、约 1 KB），
> **线条/文字/坐标轴均为矢量**。
>
> ### B-3：下线图归档（**只移不删**）
>
> | 类别 | 数量 |
> |---|---|
> | 正文未引用的 PNG | **15** |
> | 从未引用的 SVG（8 月遗留） | **7** |
>
> → `figures/_superseded/`。**`figures/` 现在精确等于「16 张图 × (PDF+PNG)」**。
>
> ### 顺带修掉打包脚本的**两个累积型缺陷**
>
> | # | 缺陷 | 后果 |
> |---|---|---|
> | ① | `copytree(dirs_exist_ok=True)` 把 `_superseded/` 也打进包 | 包里混入下线图 |
> | ② | `srcdir` **未先清空** + copytree **只增不删** | zip 里累积 **33 个已下线 PNG**，虚增 ~2 MB |
>
> **`latex_source.zip`：5.4 MB → 1.1 MB**，包内 `figures/` 恰 **32 文件**，不含 `_superseded/`。
>
> **教训**：两个缺陷都是「**只增不删**」——与正文反复出现的「只追加不核对」同类。
> **凡有累积的目录，构建前必须清空。**
"""
    if "图切矢量 PDF" not in h:
        anchor = "> **🔤 2026-10-06 —— 图字体改 Times New Roman"
        i = h.find(anchor)
        if i > 0:
            io.open(hp, "w", encoding="utf-8", newline="").write(h[:i] + ent + h[i:])
            h2 = io.open(hp, encoding="utf-8").read()
            for k in ("矢量", "5.4 MB → 1.1 MB", "只增不删"):
                assert k in h2, f"HANDOFF 断言失败：缺 {k}"
            print(f"  ✅ HANDOFF 已追加（{len(h2.splitlines())} 行）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
