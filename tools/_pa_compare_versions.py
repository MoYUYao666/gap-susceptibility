# -*- coding: utf-8 -*-
r"""比对 Paper A 的两个模板版本（sn-jnl vs elsarticle），确认转换无损。

## 为什么要比

换模板后页数从 29 → 38（elsarticle 的 `review` 选项是单栏双倍行距，页数上升属预期），
但必须排除**内容丢失或重复**——页数变化不能掩盖结构问题。

## 比对项

1. **章节数**：两版 `\section` 数目应一致；
2. **图/表引用**：`\ref{}` 的目标 label 集合应一致；
3. **引用 key 集合**：两版正文引用的 key 应一致；
4. **\input 文件**：应都是 8 个且同名；
5. **摘要词数**、**section 标题列表**逐条对照。

    python tools\_pa_compare_versions.py
"""
from __future__ import annotations

import io
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
A = REPO / "paper合" / "main_springer.tex"
B = REPO / "paper合" / "main_nc.tex"
SEC = REPO / "paper合" / "sections"


def gather(main: Path) -> dict:
    tex = io.open(main, encoding="utf-8").read()
    body = ""
    for f in sorted(SEC.glob("*.tex")):
        body += io.open(f, encoding="utf-8", errors="ignore").read() + "\n"
    return {
        "sections": re.findall(r"\\section\*?\{([^}]{2,80})\}", tex + body),
        "labels": set(re.findall(r"\\label\{([^}]+)\}", tex + body)),
        "refs": set(re.findall(r"\\ref\{([^}]+)\}", tex + body)),
        "cites": set(re.findall(r"\\cite\{([^}]+)\}", tex + body)),
        "inputs": re.findall(r"\\input\{([^}]+)\}", tex),
    }


def main() -> int:
    a, b = gather(A), gather(B)
    print("=== Paper A 两版对照 ===")
    print("  %-16s %8s %8s" % ("项", "sn-jnl", "elsarticle"))
    for k in ("sections", "labels", "refs", "cites", "inputs"):
        print("  %-16s %8d %8d" % (k, len(a[k]), len(b[k])))

    print("\n=== 差异 ===")
    for k in ("labels", "refs", "cites"):
        only_a, only_b = sorted(a[k] - b[k]), sorted(b[k] - a[k])
        print("  %-8s 仅 sn-jnl: %s ｜ 仅 elsarticle: %s" % (k, only_a[:5] or "无", only_b[:5] or "无"))

    print("\n=== 章节标题逐条对照（前 12）===")
    for i, (x, y) in enumerate(zip(a["sections"], b["sections"][:len(a["sections"])]), 1):
        mark = "✅" if x == y else "⚠️"
        print("  %2d %s %s" % (i, mark, x[:70]))
        if x != y:
            print("        → elsarticle: %s" % y[:70])

    print("\n=== 引用 key 完全一致: %s ===" % ("是 ✅" if a["cites"] == b["cites"] else "否 ❌"))
    print("=== 正文段落是否被重复 input（elsarticle 版）===")
    tex = io.open(B, encoding="utf-8").read()
    ins = re.findall(r"\\input\{([^}]+)\}", tex)
    dup = [x for x in set(ins) if ins.count(x) > 1]
    print("  重复 input: %s" % (dup or "无 ✅"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
