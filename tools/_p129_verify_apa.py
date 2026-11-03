# -*- coding: utf-8 -*-
r"""核对 APA 转换的结果（2026-10-10）。

    python tools\_p129_verify_apa.py [--apply]
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
    t = io.open(MAIN, encoding="utf-8", errors="replace").read()

    print("=== ① 文档类与引用包 ===")
    m = re.search(r"\\documentclass\[([^\]]*)\]\{([^}]*)\}", t)
    print(f"  {m.group(0) if m else '?'}")
    print(f"  natbib 显式加载: {'有' if 'usepackage' in t and 'natbib' in t.split('documentclass')[1][:600] else '无（由 elsarticle 提供）'}")

    print("\n=== ② 引用命令计数 ===")
    for cmd in ("\\citep{", "\\citet{", "\\cite{"):
        print(f"  {cmd:<10} {t.count(cmd)}")

    print("\n=== ③ 书目块 ===")
    i = t.find("\\begin{thebibliography}")
    j = t.find("\\end{thebibliography}")
    block = t[i:j]
    items = re.findall(r"\\bibitem\[([^\]]*)\]\{([^}]*)\}", block)
    no_lab = re.findall(r"\\bibitem\{", block)
    print(f"  条目数: {len(items)} ｜ 缺 label: {len(no_lab)}")
    print(f"  非 ASCII 字符: {len({c for c in block if ord(c) > 127})} 种")

    print("\n=== ④ 字母序检查（前 12 条 label）===")
    labels = [lb for lb, _ in items]
    for lb in labels[:12]:
        print(f"   {lb}")
    fams = [lb.split(",")[0].strip() for lb in labels]
    import unicodedata
    key = lambda s: "".join(c for c in unicodedata.normalize("NFKD", s)
                            if not unicodedata.combining(c)).lower()
    ok = all(key(fams[k]) <= key(fams[k + 1]) for k in range(len(fams) - 1))
    print(f"  字母序正确: {'✅' if ok else '❌'}")
    if not ok:
        for k in range(len(fams) - 1):
            if key(fams[k]) > key(fams[k + 1]):
                print(f"    错位: {fams[k]} > {fams[k+1]}")

    print("\n=== ⑤ 无作者条（应标 Anon.）===")
    for lb, k in items:
        if lb.startswith("Anon"):
            print(f"   {lb} → {k}")

    print("\n=== ⑥ 正文引用渲染检查（抽查 3 处上下文）===")
    for m in list(re.finditer(r".{70}\\citep\{[^}]*\}.{40}", t))[:3]:
        print("   …" + " ".join(m.group(0).split())[:150] + "…")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
