# -*- coding: utf-8 -*-
r"""改掉 `supplement.tex` 里另一处旧主张（`least effective option … $11\%$`）（2026-10-10）。

## 位置

`sec:vlm` 之后、讲"best site 不迁移"的那一段（**不是**我上一轮改的协议段与表）。

## 改法

沿用 3-seed bf16 数字；并**去掉"best site 不迁移"的断言**（因为 `both` vs `text_only`
在 3 seed 下**不显著**，不能说"哪一个最好"，只能说"**分不出来**"）。

    python tools\_pa_vlm_para2.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "paper合" / "sections" / "supplement.tex"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(F, encoding="utf-8", errors="replace").read()

    i = t.find("least effective option")
    print("=== 上下文（前后 700 字符）===")
    print(repr(t[max(0, i - 420):i + 420]))
    print()
    print("=== 可读版 ===")
    print(" ".join(t[max(0, i - 420):i + 420].split()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
