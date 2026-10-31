# -*- coding: utf-8 -*-
r"""审计：现有梯度类数据能支持哪些验证（2026-10-07）。

用于回答操作者「还有什么实验可以跑，非常有帮助的」——**先摸清已有数据能做什么**，
避免提议已经做到的实验，也避免提议拿不到数据的实验。

    python tools\_audit_gradient_data.py
"""
from __future__ import annotations

import io
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
FILES = [
    "outputs/theory/gradflow_identity/identity_check.json",
    "outputs/theory/encoder_side/encoder_side.json",
]


def walk(o, pre="  ", depth=0, maxd=3):
    if depth > maxd:
        return
    if isinstance(o, dict):
        for k, v in list(o.items())[:10]:
            if isinstance(v, (dict, list)):
                print(f"{pre}{k}:")
                walk(v, pre + "  ", depth + 1, maxd)
            else:
                print(f"{pre}{k:<30} {str(v)[:80]}")
    elif isinstance(o, list):
        print(f"{pre}[list n={len(o)}] 首项: {json.dumps(o[0])[:130] if o else ''}")


for rel in FILES:
    p = REPO / rel
    print("=" * 96)
    print(f"  {rel}")
    print("=" * 96)
    if not p.exists():
        print("  ❌ 不存在")
        continue
    walk(json.loads(io.open(p, encoding="utf-8").read()))
    print()
