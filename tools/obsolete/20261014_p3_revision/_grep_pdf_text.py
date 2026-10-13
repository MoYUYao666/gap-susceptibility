# -*- coding: utf-8 -*-
r"""在已下载的论文全文文本里，显示指定字符串的上下文（用于逐格核对表格数值）。

用法：
    python tools/_grep_pdf_text.py <txt文件> "87.3" ["85.9" ...]
"""
from __future__ import annotations

import re
import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) < 3:
        print(__doc__)
        return 1
    path, needles = Path(sys.argv[1]), sys.argv[2:]
    if not path.exists():
        print(f"找不到 {path}")
        return 1
    text = path.read_text(encoding="utf-8", errors="ignore")
    lines = text.splitlines()
    print(f"文件: {path.name}（{len(text)} 字符 / {len(lines)} 行）\n")

    for n in needles:
        idxs = [i for i, l in enumerate(lines) if n in l]
        print(f"=== 「{n}」出现在 {len(idxs)} 行 ===")
        for i in idxs[:6]:
            lo, hi = max(0, i - 2), min(len(lines), i + 3)
            print(f"  --- 第 {i+1} 行附近 ---")
            for j in range(lo, hi):
                marker = ">>" if j == i else "  "
                s = re.sub(r"\s+", " ", lines[j]).strip()
                if s:
                    print(f"  {marker} {s[:150]}")
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
