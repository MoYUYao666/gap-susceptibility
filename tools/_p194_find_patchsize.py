# -*- coding: utf-8 -*-
r"""定位并修论文里的 patch-size 旧归因（2026-10-11）。

## 背景（B1 风险项）

`tools/_p64_check_rank_parity.py` 早已证明**patch size 不分离两组**（同秩对照下
CLIP B/16 与 B/32 排序相同）→ 表注与一段已改为"按预训练目标分组"。

**但另一段仍写** *"the ordering is a property not of vision-language adaptation in general
but of the **patch size** the encoder uses"* → **与表注自相矛盾**。

    python tools\_p194_find_patchsize.py [--apply]
"""
from __future__ import annotations

import argparse
import glob
import io
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "paper合" / "sections"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    print("=" * 84)
    print("所有含 'patch size' 的句子（逐条判是否旧归因）")
    print("=" * 84)
    for f in sorted(glob.glob(str(SRC / "*.tex"))) + \
            [str(REPO / "paper合" / "main_nc.tex")]:
        t = io.open(f, encoding="utf-8", errors="replace").read()
        for m in re.finditer(r"[^.]{0,320}patch size[^.]{0,320}\.", t, re.I):
            s = " ".join(m.group(0).split())
            old = bool(re.search(r"property\s+(not\s+of[^.]*?\s+)?of the patch size|"
                                 r"is a property of the patch size|"
                                 r"tracks the encoder's patch size", s, re.I))
            print(f"\n  {'🔴 旧归因' if old else '✅ 已修正'} [{Path(f).name}]")
            print(f"     {s[:330]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
