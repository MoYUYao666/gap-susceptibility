# -*- coding: utf-8 -*-
r"""删除 `.tex` 里**行尾的字面 `\n`**（2026-10-12）。

## 现状（实测，非推测）

`experiments.tex` 里还有 **2 处**形如：

```
...rather than pooling them.\n<真换行>
```

即**一个反斜杠 + 字母 n + 真换行**（Python repr 显示为 `'them.\\n\n\\textbf'`）。
LaTeX 把它当成未定义命令 `\n` → 2 个编译错误。

## 做法

逐字符扫描：若遇到 `\` 后跟 `n`，且**再往后（跳过空格/制表符）就是行尾**，
则**删除这个 `\n`**（真换行保留）。

    python tools\_p435_strip_literal_newline.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
EX = REPO / "paper3" / "paper_ieee" / "sections" / "experiments.tex"


def strip_line_end_literal_n(text: str):
    out = []
    i = 0
    n = len(text)
    hits = 0
    while i < n:
        if text[i] == "\\" and i + 1 < n and text[i + 1] == "n":
            j = i + 2
            while j < n and text[j] in " \t":
                j += 1
            # 行尾（\n 或 \r）或文件末尾
            if j >= n or text[j] in "\r\n":
                hits += 1
                i += 2
                continue
        out.append(text[i])
        i += 1
    return "".join(out), hits


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(EX, encoding="utf-8", newline="").read()
    before = t.count("\\n")
    t2, hits = strip_line_end_literal_n(t)
    after = t2.count("\\n")
    print(f"  扫描前字面 '\\n' 计数 = {before} ｜ 行尾命中 = {hits} ｜ 处理后剩余 = {after}")
    if hits == 0:
        print("  ✅ 无需处理（可能已修）")
        return 0
    if not a.apply:
        print("  （预演）")
        return 0
    bak = EX.with_suffix(".tex.bak_p435")
    if not bak.exists():
        shutil.copy2(EX, bak)
    io.open(EX, "w", encoding="utf-8", newline="").write(t2)
    t3 = io.open(EX, encoding="utf-8", newline="").read()
    print(f"  ✅ 已写；剩余字面 '\\n' = {t3.count(chr(92) + 'n')}")
    for probe in ("rather than pooling them.", "localised one."):
        i = t3.find(probe)
        if i >= 0:
            print(f"  核对 {probe!r} → {t3[i:i+34]!r}")
    return 0 if t3.count("\\n") == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
