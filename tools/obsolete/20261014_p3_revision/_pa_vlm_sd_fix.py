# -*- coding: utf-8 -*-
r"""修 VLM `both` 的 sd 写法：`5.3` → `5.4`（2026-10-11）。

## 依据（`tools/_p181_vlm_exact.py`，从原始 per-seed 重算）

$$SD_{both} = 5.351741 \rightarrow \text{1 位小数} = 5.4$$

论文写了 `5.3`（错）。`text_only`（8.3）与 `vision_only`（8.8）均正确。

    python tools\_pa_vlm_sd_fix.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
FILES = [REPO / "paper合" / "sections" / "supplement.tex",
         REPO / "paper合" / "sections" / "discussion.tex"]
OLD = r"87.9\pm5.3"
NEW = r"87.9\pm5.4"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    total = 0
    for f in FILES:
        t = io.open(f, encoding="utf-8", errors="replace").read()
        n = t.count(OLD)
        print(f"  {f.name}: 命中 {n} 处 `{OLD}`")
        if n and a.apply:
            t = t.replace(OLD, NEW)
            io.open(f, "w", encoding="utf-8", newline="").write(t)
            total += n
    if not a.apply:
        print("  （预演）")
        return 0
    print(f"  → 共改 {total} 处")
    for f in FILES:
        t = io.open(f, encoding="utf-8", errors="replace").read()
        left = t.count(OLD)
        right = t.count(NEW)
        print(f"  复核 {f.name}: 旧 {left} ｜ 新 {right}")
        assert left == 0, "旧写法仍在"
    print("  ✅ 已修")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
