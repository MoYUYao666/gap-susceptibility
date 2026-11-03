# -*- coding: utf-8 -*-
r"""诊断：为什么 phase2 表体与泛化表的多行块没命中（2026-10-07）。"""
from __future__ import annotations

import io
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
t = io.open(REPO / "paper合" / "sections" / "validation.tex", encoding="utf-8").read()
lines = t.splitlines()

print("=== phase2 表体（L49-70）逐行 repr ===")
for i in range(48, 70):
    if i < len(lines):
        print(f"  {i+1:>3}: {lines[i]!r}")

print("\n=== 跨数据集表（L99-106）逐行 repr ===")
for i in range(98, 107):
    if i < len(lines):
        print(f"  {i+1:>3}: {lines[i]!r}")
