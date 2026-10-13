# -*- coding: utf-8 -*-
r"""按**期刊标准口径**复核 A1 摘要词数（数学式算 1–2 词）（2026-10-10）。

多数期刊统计摘要词数时，**公式按整体计**（不是每个符号一个词）。
本脚本给三种口径，供判断是否需要继续压缩。

    python tools\_p97_a1_abstract_wc.py
"""
from __future__ import annotations

import io
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "paper_a1" / "main.tex"


def main() -> int:
    t = io.open(F, encoding="utf-8", errors="replace").read()
    m = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", t, re.S)
    if not m:
        print("  ❌ 未找到 abstract")
        return 1
    body = m.group(1)

    # ① 字面：去命令但保留数学记号
    a = re.sub(r"\\[a-zA-Z]+\{[^}]*\}", " ", body)
    a = len(a.split())

    # ② 标准：每个 $...$ 与 \emph{} 内容算其内部词数，命令删除
    b = re.sub(r"\\[a-zA-Z]+", " ", body)          # 删所有命令
    b = re.sub(r"[{}$\\]", " ", b)                 # 删括号与美元
    b = len(b.split())

    # ③ 最严：数学式整体算 1 词
    c = re.sub(r"\$[^$]*\$", " MATH ", body)
    c = re.sub(r"\\[a-zA-Z]+", " ", c)
    c = re.sub(r"[{}\\$]", " ", c)
    c = len(c.split())

    print("=== 摘要词数（三种口径）===")
    print(f"  ① 字面（数学记号逐符号计） : **{a}**")
    print(f"  ② 标准（删 LaTeX 命令）    : **{b}**")
    print(f"  ③ 最严（数学式整体算 1 词）: **{c}**")
    print("\n  目标刊限制：ESWA / KBS / CVIU / Neurocomputing / IVC = **250 词**")
    for tag, v in (("①", a), ("②", b), ("③", c)):
        print(f"  {tag} {v} 词 → {'✅ 达标' if v <= 250 else f'❌ 超 {v-250}'}")
    print("\n=== 摘要全文（纯文本预览）===")
    prev = re.sub(r"\\[a-zA-Z]+\{[^}]*\}", lambda x: x.group(0), body)
    prev = re.sub(r"\\emph\{([^}]*)\}", r"\1", prev)
    prev = " ".join(prev.split())
    print(" ", prev[:2000])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
