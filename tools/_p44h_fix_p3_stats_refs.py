#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""_p44h_fix_p3_stats_refs.py -- renumber the trailing §3 subsections of
docs/P3_STATS.md after the device-reproducibility section was inserted, and fix
stale cross-references. Idempotent: re-running changes nothing."""
import io
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, "docs", "P3_STATS.md")

t = io.open(P, encoding="utf-8").read()
before = t

RENUM = [
    ("### 3.5 归档里两个 LLaVA 批次符号相反", "### 3.8 归档里两个 LLaVA 批次符号相反"),
    ("### 3.6 R3.18 的替换措辞", "### 3.9 R3.18 的替换措辞"),
    ("### 3.7 姊妹项目的 loader 抽样缺陷", "### 3.10 姊妹项目的 loader 抽样缺陷"),
]
for a, b in RENUM:
    if a in t:
        t = t.replace(a, b)

# cross-reference fixes
t = t.replace("（§3.6）", "（§3.2）")
t = t.replace("见 §3.3）", "见 §3.4）")
t = t.replace("（§3.5）", "（§3.8）")
t = t.replace("§3.2/§3.5", "§3.4/§3.5")
t = t.replace("§3.4 的替换措辞", "§3.9 的替换措辞")

if t != before:
    io.open(P, "w", encoding="utf-8", newline="").write(t)
    print("updated", P)
else:
    print("no change needed (already fixed)")

# report current numbering for verification
for i, line in enumerate(io.open(P, encoding="utf-8").read().split("\n"), 1):
    if re.match(r"^#{2,3} ", line):
        print("%4d  %s" % (i, line))
