# -*- coding: utf-8 -*-
r"""读 `prospective_results.json`：`α_pred` 与 `α_obs` 的实际对照（2026-10-10）。

    python tools\_p87_read_prospective.py
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "outputs" / "theory" / "prospective" / "prospective_results.json"


def show(o, indent=2, depth=0):
    pad = " " * indent
    if isinstance(o, list):
        print(f"{pad}[list, {len(o)} 项]")
        for i, x in enumerate(o[:8]):
            print(f"{pad}  #{i}:")
            show(x, indent + 4, depth + 1)
    elif isinstance(o, dict):
        for k, v in o.items():
            if isinstance(v, (dict, list)):
                print(f"{pad}{k}:")
                show(v, indent + 2, depth + 1)
            else:
                s = str(v)
                print(f"{pad}{k} = {s[:90]}")
    else:
        print(f"{pad}{o}")


def main() -> int:
    d = json.loads(io.open(F, encoding="utf-8").read())
    print("=== 结构 ===")
    show(d)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
