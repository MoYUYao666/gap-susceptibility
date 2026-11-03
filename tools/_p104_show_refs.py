# -*- coding: utf-8 -*-
r"""展示 A1 参考文献的**现状**（供操作者看清第 1 步要改什么）（2026-10-10）。

    python tools\_p104_show_refs.py
"""
from __future__ import annotations

import io
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
M = REPO / "paper_a1" / "main.tex"


def main() -> int:
    t = io.open(M, encoding="utf-8", errors="replace").read()
    items = re.findall(
        r"\\bibitem(?:\[[^\]]*\])?\{([^}]*)\}\s*(.*?)(?=\\bibitem|\\end\{thebibliography\})",
        t, re.S)
    print(f"=== A1 文末参考文献（共 {len(items)} 条，示前 4 条）===")
    for k, b in items[:4]:
        print(f"  [{k}]")
        print("    " + " ".join(b.split())[:185])
        print()

    print("=== 正文引用（示 3 处）===")
    for m in list(re.finditer(r".{50}\\cite\{[^}]*\}.{50}", t))[:3]:
        print("  …" + " ".join(m.group(0).split())[:150] + "…")

    print("\n=== 它现在渲染成什么（数字制）===")
    print("  \\cite{liang2022} → 渲染为 “[1]”")
    print("  \\cite{radford2021,yi2025} → 渲染为 “[2, 3]”")

    print("\n=== Neural Networks 要求（APA 第 7 版，作者-年）===")
    print("  正文：\\citep{liang2022} → “(Liang et al., 2022)”")
    print("        \\citet{radford2021} → “Radford et al. (2021)”")
    print("  文末：按**字母序**排列，形如")
    print("        Liang, V. W., Zhang, Y., Kwon, Y., Yeung, S., & Zou, J. (2022).")
    print("        Mind the gap: Understanding the modality gap in multi-modal")
    print("        contrastive representation learning. In Advances in Neural")
    print("        Information Processing Systems (pp. 17612–17625).")
    print("        https://doi.org/10.52202/068431-1280")
    print("\n  → 差异：① [n] 数字 → (作者, 年)  ② 文末顺序：引用顺序 → 字母序")
    print("           ③ 作者写法 V.~W. Liang → Liang, V. W.  ④ 标题大小写与斜体")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
