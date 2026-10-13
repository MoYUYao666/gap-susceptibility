# -*- coding: utf-8 -*-
r"""导出 Paper A 的标题/摘要/关键词，用于 scope 匹配判断（2026-10-07）。"""
from __future__ import annotations

import io
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
t = io.open(REPO / "paper合" / "main_nc.tex", encoding="utf-8").read()


def block(env: str) -> str:
    m = re.search(r"\\begin\{" + env + r"\}(.*?)\\end\{" + env + r"\}", t, re.S)
    return re.sub(r"\s+", " ", m.group(1)).strip() if m else "(未找到)"


print("=== 标题 ===")
m = re.search(r"\\title(?:\[[^\]]*\])?\{(.*?)\n\}", t, re.S)
print(re.sub(r"\s+", " ", m.group(1)).strip() if m else "(未找到)")

print("\n=== 摘要 ===")
print(block("abstract"))

print("\n=== 关键词 ===")
print(block("keyword").replace("\\sep", " ｜ "))

print("\n=== 摘要词数 ===")
ab = block("abstract")
print(f"  {len(re.sub(r'\\\\[a-zA-Z]+', ' ', ab).split())} 词")

print("\n=== 各节标题（看内容构成）===")
for m in re.finditer(r"\\section\{([^}]*)\}", t):
    print("  " + m.group(1))
for f in sorted((REPO / "paper合" / "sections").glob("*.tex")):
    s = io.open(f, encoding="utf-8").read()
    for m in re.finditer(r"\\section\{([^}]*)\}", s):
        print(f"  [{f.stem}] {m.group(1)}")
