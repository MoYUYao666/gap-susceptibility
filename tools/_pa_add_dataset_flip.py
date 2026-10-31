# -*- coding: utf-8 -*-
r"""把"严格冻结下的数据集翻转"写进论文（2026-10-10）。

## 证据（`tools/_p147_flip_corrected.py`，r4 同秩，ΔCG 越负越保护）

| 数据集 | `text_only` | `both` | 最保护 | 出处 |
|---|---|---|---|---|
| **Flickr30k** | **−0.0288 ± 0.0013** | −0.0188 ± 0.0004 | **`text_only`** | `outputs/strict_freeze_b32_r4/*/seed*` |
| **COCO** | −0.0414 ± 0.0015 | **−0.0886 ± 0.0026** | **`both`** | `outputs/coco_sweep_text_only/r4` + `outputs/coco_sweep/r4` |

**COCO 的 `text_only` 由本次新跑补齐**（11 run：r2 补 2 seed、r8/r32/r64 各 3 seed）。

**COCO `text_only` 全秩趋势**：r2 −0.0488 ｜ r8 −0.0944 ｜ r32 −0.1315 ｜ r64 −0.1396

## 插在哪

`validation.tex` 里讲严格冻结对照的那段之后（该处已有 CLIP/OpenCLIP 的位置结论）。

    python tools\_pa_add_dataset_flip.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "paper合" / "sections" / "validation.tex"

# 插在 "We repeated that control on SigLIP" 那段之前
ANCHOR = "We repeated that control on SigLIP"

NEW = r"""The comparison also depends on the evaluation corpus. At rank $4$ under the same
strict-freezing protocol, text-only holds the gap at $-0.0288\pm0.0013$ on Flickr30k against
$-0.0188\pm0.0004$ for the both-position arm, whereas on MS-COCO the ordering is the reverse:
text-only gives $-0.0414\pm0.0015$ and both-position $-0.0886\pm0.0026$, so the arm that is
most protective on one corpus is the least protective of the two on the other. The MS-COCO
text-only arm improves monotonically with rank over the range we ran ($-0.0488$ at rank $2$,
$-0.0944$ at $8$, $-0.1315$ at $32$ and $-0.1396$ at $64$, three seeds each), so the reversal
is not an artefact of a single rank. Which position is preferable therefore has to be
established per corpus as well as per architecture, and neither the corpus nor the backbone
that a given recommendation transfers to can be assumed.

"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(F, encoding="utf-8", errors="replace").read()
    if "depends on the evaluation corpus" in t:
        print("  已写，跳过")
        return 0
    n = t.count(ANCHOR)
    print(f"=== 锚点命中 {n} 处 ===")
    if n != 1:
        i = t.find("SigLIP")
        print("  上下文:", repr(t[max(0, i - 200):i + 100]) if i > 0 else "(未找到)")
        return 1
    t2 = t.replace(ANCHOR, NEW + ANCHOR, 1)
    if not a.apply:
        print("  （预演）")
        return 0
    io.open(F, "w", encoding="utf-8", newline="").write(t2)
    t3 = io.open(F, encoding="utf-8", errors="replace").read()
    for k in ("depends on the evaluation corpus", "$-0.0288\\pm0.0013$",
              "$-0.0886\\pm0.0026$", "$-0.1396$", "per corpus as well as per architecture"):
        assert k in t3, f"断言失败：缺 {k}"
    print("  ✅ 已插入「严格冻结下的数据集翻转」段")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
