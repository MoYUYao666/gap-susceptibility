# -*- coding: utf-8 -*-
r"""修复 `_p501` 造成的损伤：行尾 `\n` 被误删导致 LaTeX 命令断头（2026-10-13）。

## 病因

`_p501` 用 `re.sub(r"\\n[ \t]*(?=\r?\n)", "", text)` 想删"字面 \n + 真换行"，但它**同时匹配了
合法的 LaTeX 命令**：任何**以 `\n` 开头且整行只有这一个命令**的行，其 `\n` 后被删 ⇒

    \newtheorem{theorem}{Theorem}[section]   →   （空行）ewtheorem{theorem}{Theorem}[section]

即 **`\n` → 换行，命令断头**。

## 本脚本

**逐文件找出被断头的命令**（行首为 `ewtheorem`/`ewcommand`/`ewline`/`ot`/`oindent`/`onumber`/`eq`/`eg`…），
**把上一行的空行去掉、补回 `\`**。

**⚠️ 只修已知模式，不做全局正则替换** —— 上次的教训就是判据过宽。

    python tools\_p502_repair_p501_damage.py [--apply]
"""
from __future__ import annotations

import argparse
import glob
import io
import os
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PI = REPO / "paper3" / "paper_ieee"

# LaTeX 命令里紧随 \n 之后的合法续写（被吃掉的 "\" + "n" 应还原为 "\n"）
HEADS = ("ewtheorem", "ewcommand", "ewline", "ewpage", "ewcol", "ewenvironment",
         "ewlength", "ewcounter", "ewif", "ewbox", "ot", "oindent", "onumber",
         "eq", "eg", "e", "abla", "abla", "orm", "othing", "ull", "obreak",
         "ocite", "olink", "ameref", "ewcite", "ocite")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    files = sorted(glob.glob(str(PI / "sections" / "*.tex"))) + \
        sorted(glob.glob(str(PI / "*.tex"))) + \
        sorted(glob.glob(str(PI / "supplementary" / "*.tex")))
    files = [f for f in files if ".bak" not in os.path.basename(f)]
    total_sites = 0
    print("=" * 100)
    print("被断头的行（行首疑似丢掉 \\n 的命令）")
    print("=" * 100)
    for f in files:
        lines = io.open(f, encoding="utf-8", errors="replace").read().split("\n")
        hits = []
        for idx, ln in enumerate(lines):
            s = ln.strip()
            for h in HEADS:
                if s.startswith(h) and re.match(rf"^{re.escape(h)}[{{}}]?[a-zA-Z]*", s):
                    # 且上一行（或上两行）是空行 ⇒ 疑似被吃掉的 \n
                    prev = lines[idx - 1].strip() if idx >= 1 else ""
                    prev2 = lines[idx - 2].strip() if idx >= 2 else ""
                    if prev == "" or prev2 == "":
                        hits.append((idx + 1, s[:80]))
                        break
        if hits:
            print(f"  ── {os.path.relpath(f, PI)}（{len(hits)} 处）")
            for ln, s in hits[:12]:
                print(f"       L{ln}: {s}")
            total_sites += len(hits)
    print()
    print(f"  合计疑似断头 {total_sites} 处")
    if not a.apply:
        print("  （预演）")
        return 0
    print("  ⚠️ 请用 edit 工具逐处修（本脚本只做定位，不做替换）—— 避免又一次过宽正则。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
