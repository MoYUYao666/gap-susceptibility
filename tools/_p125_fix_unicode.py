# -*- coding: utf-8 -*-
r"""修 natbib 报错与 Unicode 字符（2026-10-10）。

## 剩 2 类问题

| 问题 | 原因 | 修法 |
|---|---|---|
| `Bibliography not compatible with author-year citations` | natbib 要求**所有** `\bibitem` 都带 `[label]`（或像 thebibliography 期望的 APA 格式） | 检查是否**每条都有** `[Author, Year]`；缺者补齐 |
| `Unicode character ȩ (U+0229) not set up` | 作者名含非 ASCII（如 `Yüksekgönül`、`ȩ`） | 加 `\usepackage[utf8]{inputenc}` + **把罕用变音符转为 LaTeX 命令或 ASCII** |

    python tools\_p125_fix_unicode.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import re
import sys
import unicodedata
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MAIN = REPO / "paper_a1" / "main.tex"

# 常见需转 LaTeX 的字符（含罕见组合符）
TEX_MAP = {
    "ü": '\\"u', "ö": '\\"o', "ä": '\\"a', "é": "\\'e", "è": "\\`e",
    "á": "\\'a", "à": "\\`a", "í": "\\'i", "ó": "\\'o", "ú": "\\'u",
    "ç": "\\c{c}", "ñ": "\\~n", "å": "\\aa{}", "ø": "\\o{}",
    "Yüksekgönül": "Y{\\\"u}ksekg{\\\"o}n{\\\"u}l",
}


def to_ascii_safe(s: str) -> str:
    """把非 ASCII 转为安全形式：优先 LaTeX 命令，其次去音，最后 ASCII 近似。"""
    if s in TEX_MAP:
        return TEX_MAP[s]
    out = []
    for ch in s:
        if ch in TEX_MAP:
            out.append(TEX_MAP[ch])
        elif ord(ch) < 128:
            out.append(ch)
        else:
            # 去音
            d = "".join(c for c in unicodedata.normalize("NFKD", ch)
                        if not unicodedata.combining(c))
            out.append(d if d and ord(d[0]) < 128 else "")
    return "".join(out)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(MAIN, encoding="utf-8", errors="replace").read()

    # ① 每条 bibitem 是否都有 [label]
    items = re.findall(r"\\bibitem(\[[^\]]*\])?\{([^}]*)\}", t)
    no_label = [k for lab, k in items if not lab]
    print(f"=== bibitem 共 {len(items)} 条 ｜ 缺 [label]: {len(no_label)} {no_label[:8]}")

    # ② 找非 ASCII 字符
    i = t.find("\\begin{thebibliography}")
    j = t.find("\\end{thebibliography}")
    block = t[i:j] if i > 0 and j > i else ""
    bad = {}
    for ch in block:
        if ord(ch) > 127:
            bad.setdefault(ch, 0)
            bad[ch] += 1
    print(f"=== 书目块内非 ASCII 字符: {len(bad)} 种 ===")
    for ch, n in sorted(bad.items(), key=lambda x: -x[1])[:12]:
        print(f"   {ch!r} U+{ord(ch):04X} × {n}")

    # ③ 修：书目块内去音/转义
    if block:
        nb = to_ascii_safe(block)
        left = {c for c in nb if ord(c) > 127}
        print(f"=== 处理后仍非 ASCII: {len(left)} 种 {[f'{c} U+{ord(c):04X}' for c in list(left)[:8]]}")
        t = t[:i] + nb + t[j:]

    # ④ 加 inputenc（若缺）
    if "inputenc" not in t:
        t = t.replace("\\usepackage{amsmath,amssymb}",
                      "\\usepackage[utf8]{inputenc}\n\\usepackage{amsmath,amssymb}", 1)
        print("=== 已加 \\usepackage[utf8]{inputenc}")

    if not a.apply:
        print("\n  （预演）")
        return 0
    io.open(MAIN, "w", encoding="utf-8", newline="").write(t)
    print(f"\n  ✅ 已写 {MAIN.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
