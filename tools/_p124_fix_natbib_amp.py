# -*- coding: utf-8 -*-
r"""修 natbib 冲突 + `&` 未转义（2026-10-10）。

## 两个错（我上一版引入的）

| 错 | 原因 | 修法 |
|---|---|---|
| **Option clash for package natbib** | **`elsarticle` 已自行加载 natbib（数字制）**，我又 `\usepackage[authoryear]{natbib}` | **把 `authoryear` 作为文档类选项**：`\documentclass[review,authoryear]{elsarticle}`，**删掉我加的 `\usepackage`** |
| **52 处 "Misplaced alignment tab character &"** | APA 里作者分隔的 `&` 未转义成 `\&` | 书目块内 `, & ` → `, \& ` |

    python tools\_p124_fix_natbib_amp.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MAIN = REPO / "paper_a1" / "main.tex"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(MAIN, encoding="utf-8", errors="replace").read()

    # ① 删掉我加的 natbib 行
    t2 = re.sub(r"\\usepackage\[[^\]]*\]\{natbib\}\n?", "", t)
    removed = len(t) - len(t2)
    t = t2

    # ② 文档类加 authoryear
    t2 = re.sub(r"\\documentclass\[([^\]]*)\]\{elsarticle\}",
                lambda m: ("\\documentclass[" + m.group(1) + ",authoryear]{elsarticle}"
                           if "authoryear" not in m.group(1) else m.group(0)), t, count=1)
    cls_changed = t2 != t
    t = t2

    # ③ 书目块内转义 &
    i = t.find("\\begin{thebibliography}")
    j = t.find("\\end{thebibliography}")
    assert i > 0 and j > i, "未找到书目块"
    block = t[i:j]
    nb = re.sub(r"(?<!\\), & ", r", \\& ", block)      # ", & X" → ", \& X"
    nb = re.sub(r"(?<!\\), \\& ", r", \\& ", nb)        # 幂等
    n_amp = block.count(", & ") - nb.count(", \\& ")
    n_amp = block.count("&") - nb.count("&") + block.count("&") - nb.count("&")
    t = t[:i] + nb + t[j:]

    print("=== 改动 ===")
    print(f"  删掉 natbib usepackage: {'✅' if removed else '（本就没有）'}")
    print(f"  文档类加 authoryear:    {'✅' if cls_changed else '（已有）'}")
    print(f"  书目块 & 转义:          {block.count('&')} 个 & → "
          f"{nb.count('&')} 个（新增 \\& = {nb.count(chr(92)+'&') - block.count(chr(92)+'&')}）")
    m = re.search(r"\\documentclass(\[[^\]]*\])?\{[^}]*\}", t)
    print(f"  现在的文档类: {m.group(0)}")

    if not a.apply:
        print("\n  （预演）")
        return 0
    io.open(MAIN, "w", encoding="utf-8", newline="").write(t)
    print(f"\n  ✅ 已写 {MAIN.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
