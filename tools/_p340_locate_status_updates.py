# -*- coding: utf-8 -*-
r"""定位所有需要按「P1 已被 PR 拒稿 / Paper A 从未投稿」更新的文档位置（2026-10-12）。

## 依据（操作者 2026-10-12 明确澄清）

- **P1 = `paper/`，投的是 Pattern Recognition（`PR-D-26-10149`）→ 已拒稿。**
- **`paper合`（Paper A）还没有投过**（此前文档里"受 P1 审稿期伦理约束"的说法需更正）。

    python tools\_p340_locate_status_updates.py [--apply]
"""
from __future__ import annotations

import argparse
import glob
import io
import os
import re
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

# (标签, 正则)
PATTERNS = [
    ("P1 状态说在审/未出决定", r"Required Reviews Completed|仍为 \*\*Required|状态日期现显示"),
    ("P1 稿号+在审", r"PR-D-26-10149"),
    ("Paper A 受 P1 约束", r"受 P1 审稿期伦理约束|仍受 P1|依赖 P1 决定|P1 决定后"),
    ("Paper A 待投", r"paper合.{0,40}待投|待投.{0,40}paper合|(\*\*待投\*\*)"),
    ("ap3 依赖 P1 决定", r"P1 \*\*接收\*\*|P1 \*\*拒稿\*\*|红线解除"),
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    files = ["HANDOFF.md", "文件地图.md"] + \
        sorted(glob.glob(str(REPO / "docs" / "*.md")))
    for label, pat in PATTERNS:
        print("=" * 104)
        print(label)
        print("=" * 104)
        n = 0
        for f in files:
            p = Path(f)
            if not p.exists():
                continue
            try:
                t = io.open(p, encoding="utf-8", errors="replace").read()
            except Exception:
                continue
            for m in re.finditer(pat, t):
                n += 1
                if n > 8:
                    continue
                ln = t[:m.start()].count("\n") + 1
                seg = " ".join(t[max(0, m.start() - 190):m.start() + 210].split())
                mt = time.strftime("%m-%d %H:%M", time.localtime(os.path.getmtime(p)))
                print(f"  [{p.name}:{ln}] ({mt}) …{seg[:380]}…")
        print(f"  共 {n} 处\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
