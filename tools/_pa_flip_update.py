# -*- coding: utf-8 -*-
r"""更新"数据集翻转"段的 COCO text_only 数字（batch 128 重跑后）（2026-10-11）。

## 数字变化（COCO text_only，batch 64 → 128）

| 秩 | 旧（batch 64） | 新（batch 128，n=5） |
|---|---|---|
| r2 | $-0.0488$ | **$-0.0247\pm0.0015$** |
| r4 | $-0.0414$ | $-0.0414\pm0.0015$ |
| r8 | $-0.0944$ | **$-0.0690\pm0.0025$** |
| r32 | $-0.1315$ | **$-0.1153\pm0.0017$** |
| r64 | $-0.1396$ | **$-0.1359\pm0.0033$** |

**`both` 侧未变**（本来就是 batch 128）：r2 $-0.0563$、r4 $-0.0886$、r16 $-0.1527$、r32 $-0.1562$、r64 $-0.1531$。

    python tools\_pa_flip_update.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "paper合" / "sections" / "validation.tex"

OLD = (r"""The MS-COCO
text-only arm improves monotonically with rank over the range we ran ($-0.0488$ at rank $2$,
$-0.0944$ at $8$, $-0.1315$ at $32$ and $-0.1396$ at $64$, three seeds each), so the reversal
is not an artefact of a single rank.""")

NEW = (r"""The MS-COCO
text-only arm improves monotonically with rank over the range we ran ($-0.0247$ at rank $2$,
$-0.0690$ at $8$, $-0.1153$ at $32$ and $-0.1359$ at $64$, five seeds each at batch $128$), so
the reversal is not an artefact of a single rank, and both arms of that comparison use the same
batch size.""")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(F, encoding="utf-8", errors="replace").read()
    n = t.count(OLD)
    print(f"=== 锚点命中 {n} ===")
    if n == 0:
        i = t.find("improves monotonically with rank")
        if i > 0:
            print("  实际文本:")
            print("   " + repr(t[max(0, i - 320):i + 400]))
        return 1
    t2 = t.replace(OLD, NEW, 1)
    if not a.apply:
        print("  （预演）")
        return 0
    bak = F.with_suffix(".tex.bak_flip2")
    if not bak.exists():
        io.open(bak, "w", encoding="utf-8", newline="").write(
            io.open(F, encoding="utf-8").read())
    io.open(F, "w", encoding="utf-8", newline="").write(t2)
    t3 = io.open(F, encoding="utf-8", errors="replace").read()
    for k in (r"$-0.0247$ at rank $2$", r"$-0.1359$ at $64$", "five seeds each at batch $128$"):
        assert k in t3, f"断言失败：缺 {k}"
    for k in (r"$-0.0488$", r"$-0.1396$"):
        assert k not in t3, f"旧数字仍在: {k}"
    print("  ✅ validation.tex 的翻转段已更新为 batch-128 数字")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
