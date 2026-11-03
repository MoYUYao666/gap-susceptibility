# -*- coding: utf-8 -*-
r"""修两个**真实溢出**的表格（2026-10-06）。

## 实测（像素法，`tools/_measure_textblock.py`）

版心：左 133.9 pt ｜ 右 476.6 pt ｜ **宽 342.7 pt**。越界页：

| 页 | 右界 | 超出 | 元素 |
|---|---|---|---|
| **12** | 574.6 pt | **+97.9** | `tab:position_strict`（**我加了 Patch 列 + BioCLIP 行**所致） |
| **37** | 497.5 pt | **+20.9** | `tab:phase2`（`Config / α / β / R²`） |

**注**：先前我曾判断这些 `Overfull` 是"度量噪声"——**那次判断是错的**。像素法证明确有两页越界。

## 收窄手段（不加新宏包，`booktabs` 已在）

1. **缩短单元格文字**（`CLIP ViT-B/32 (WIT)` → `CLIP B/32 (WIT)`）；
2. **表内用 `\small` / `\footnotesize`**；
3. **`\setlength{\tabcolsep}{4pt}`** 收紧列距；
4. `tab:position_strict` 保留 Patch 列（正文引用它），但把 `$32$`/`$16$` 写得更紧凑。

    python tools\_fix_wide_tables.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
EMP = REPO / "paper合" / "sections" / "empirical.tex"
SUP = REPO / "paper合" / "sections" / "supplement.tex"

# ── ① tab:position_strict
OLD_TAB = (r"\begin{tabular}{llccc}" "\n"
           r"\toprule" "\n"
           r"Backbone & Patch & Text-only & Both & Vision-only \\" "\n"
           r"\midrule" "\n"
           r"CLIP ViT-B/32 (WIT)       & $32$ & $\mathbf{-0.0465}$ / $0.624$ & $-0.0258$ / $\mathbf{0.693}$ & $+0.0106$ / $0.680$ \\" "\n"
           r"OpenCLIP ViT-B/32 (LAION) & $32$ & $\mathbf{+0.0694}$ / $0.643$ & $+0.0881$ / $\mathbf{0.680}$ & $+0.0925$ / $0.672$ \\" "\n"
           r"\midrule" "\n"
           r"SigLIP ViT-B/16           & $16$ & $+0.0664$ / $0.432$ & $\mathbf{-0.0114}$ / $\mathbf{0.619}$ & $+0.0522$ / $0.341$ \\" "\n"
           r"BioCLIP ViT-B/16 (bio.)   & $16$ & $-0.3671$ / --- & $\mathbf{-0.4515}$ / --- & $-0.2927$ / --- \\" "\n"
           r"\bottomrule")

NEW_TAB = (r"\setlength{\tabcolsep}{4pt}" "\n"
           r"\footnotesize" "\n"
           r"\begin{tabular}{@{}llccc@{}}" "\n"
           r"\toprule" "\n"
           r"Backbone & Pat. & Text-only & Both & Vision-only \\" "\n"
           r"\midrule" "\n"
           r"CLIP B/32 (WIT)      & 32 & $\mathbf{-0.0465}$ / $0.624$ & $-0.0258$ / $\mathbf{0.693}$ & $+0.0106$ / $0.680$ \\" "\n"
           r"OpenCLIP B/32 (LAION)& 32 & $\mathbf{+0.0694}$ / $0.643$ & $+0.0881$ / $\mathbf{0.680}$ & $+0.0925$ / $0.672$ \\" "\n"
           r"\midrule" "\n"
           r"SigLIP B/16          & 16 & $+0.0664$ / $0.432$ & $\mathbf{-0.0114}$ / $\mathbf{0.619}$ & $+0.0522$ / $0.341$ \\" "\n"
           r"BioCLIP B/16 (bio.)  & 16 & $-0.3671$ / --- & $\mathbf{-0.4515}$ / --- & $-0.2927$ / --- \\" "\n"
           r"\bottomrule")

OLD_END = r"\end{tabular}" "\n" r"\end{table}"

# ── ② tab:phase2（附录，宽表）
OLD_P2_OPEN = r"\begin{tabular}{lccc}"
NEW_P2_OPEN = (r"\setlength{\tabcolsep}{4pt}" "\n"
               r"\footnotesize" "\n"
               r"\begin{tabular}{@{}lccc@{}}")


def main() -> int:
    apply = "--apply" in sys.argv
    emp = io.open(EMP, encoding="utf-8").read()
    sup = io.open(SUP, encoding="utf-8").read()
    n = 0

    if OLD_TAB in emp:
        print("  ✅ empirical.tex：命中 tab:position_strict")
        if apply:
            emp = emp.replace(OLD_TAB, NEW_TAB, 1)
        n += 1
    else:
        print("  ⚠ empirical.tex：tab:position_strict 未命中")

    # tab:phase2：只改它的 tabular 开头（用 label 定位，避免误改其他表）
    key = "tab:phase2"
    if key in sup:
        i = sup.find(key)
        j = sup.rfind(OLD_P2_OPEN, 0, i)
        if j > 0:
            print("  ✅ supplement.tex：命中 tab:phase2 的 tabular 开头")
            if apply:
                sup = sup[:j] + NEW_P2_OPEN + sup[j + len(OLD_P2_OPEN):]
            n += 1
        else:
            print("  ⚠ supplement.tex：tab:phase2 的表头未匹配")
    else:
        print("  ⚠ supplement.tex：无 tab:phase2")

    if apply and n:
        io.open(EMP, "w", encoding="utf-8", newline="").write(emp)
        io.open(SUP, "w", encoding="utf-8", newline="").write(sup)
        e2 = io.open(EMP, encoding="utf-8").read()
        s2 = io.open(SUP, encoding="utf-8").read()
        assert r"\setlength{\tabcolsep}{4pt}" in e2, "empirical 未改"
        assert "CLIP B/32 (WIT)" in e2 and "ViT-B/32 (WIT)" not in e2, "标签未缩短"
        assert r"\setlength{\tabcolsep}{4pt}" in s2, "supplement 未改"
        # 括号列宽 @{} 与 \footnotesize 成对出现
        assert e2.count(r"\footnotesize") >= 1 and s2.count(r"\footnotesize") >= 1
        print(f"  ✅ 已改 {n} 个表并断言通过")
    else:
        print(f"\n  {n}/2 处（{'预演' if not apply else '部分失败'}）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
