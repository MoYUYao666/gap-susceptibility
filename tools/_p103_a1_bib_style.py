# -*- coding: utf-8 -*-
r"""核 A1 的 `\bibitem` 样式与关键词分隔符（判 APA 转换工作量）（2026-10-10）。

    python tools\_p103_a1_bib_style.py
"""
from __future__ import annotations

import io
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
M = REPO / "paper_a1" / "main.tex"


def main() -> int:
    t = io.open(M, encoding="utf-8", errors="replace").read()

    print("=== ① \\bibitem 逐条（前 6 条）===")
    items = re.findall(r"\\bibitem(?:\[[^\]]*\])?\{([^}]*)\}\s*(.*?)(?=\\bibitem|\\end\{thebibliography\})",
                       t, re.S)
    print(f"  共 {len(items)} 条")
    for key, body in items[:6]:
        print(f"   [{key}] {' '.join(body.split())[:180]}")

    print("\n=== ② 是否已是作者-年（APA 特征）===")
    apa_like = 0
    for key, body in items:
        s = " ".join(body.split())
        # APA: "Author, A. B., & Author, C. (2024). Title. Journal, 1(2), 3-4."
        if re.search(r"\(\d{4}[a-z]?\)\.", s) and re.search(r"\b[A-Z][a-z]+, [A-Z]\.", s):
            apa_like += 1
    print(f"  含'(年).' 且含缩写名: {apa_like}/{len(items)}")
    print(f"  判定: {'⚠️ 部分像 APA，需逐条核' if 0 < apa_like < len(items) else ('✅ 已像 APA' if apa_like == len(items) else '❌ 不是 APA（需整体重排）')}")

    print("\n=== ③ 关键词分隔符 ===")
    m = re.search(r"\\keywords\{(.*?)\}", t, re.S)
    if m:
        kw = m.group(1)
        print(f"  分隔符用 \\sep: {'\\sep' in kw}")
        n = kw.count("\\sep") + 1
        print(f"  关键词数: {n}")

    print("\n=== ④ 正文引用命令（数字制特征）===")
    for cmd in ("\\cite{", "\\citep{", "\\citet{"):
        n = t.count(cmd)
        if n:
            print(f"  {cmd} {n} 次")
    print("  注：`\\cite` 在 natbib 默认（数字）下输出 [1]；APA 需 `\\citep`/`\\citet`（作者-年）")

    print("\n=== ⑤ 结论 ===")
    if apa_like == len(items):
        print("  ✅ 参考文献已是 APA 格式 → 只需把 `\\cite` 改为 `\\citep`/`\\citet`（`\\usepackage[authoryear]{natbib}`）")
    else:
        print("  ⚠️ 参考文献**不是** APA → 需按 APA 第 7 版重排（13 条，工作量小）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
