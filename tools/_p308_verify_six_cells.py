# -*- coding: utf-8 -*-
r"""复核「六个数据集×backbone 单元」这句话在稿里是否存在（空白归一后）（2026-10-12）。

**教训**：稿里文本常**跨行**，字面 `in` 检查会漏 → 必须**先归一空白再查**。

    python tools\_p308_verify_six_cells.py
"""
from __future__ import annotations

import glob
import io
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

# 归一空白后应存在的关键短语（与 `_p290` 审计的判据一致）
NEEDLES = [
    "six dataset $\\times$ backbone cells",
    "mixed model with random dataset, backbone and configuration",
    "cluster-robust inference",
    "$\\beta=-0.95\\pm0.08$",
    "Adaptation Site and the Modality Gap",
    "Not of a Fragile Tower",
    "Retrieval protocol, and which rows we treat as informative",
    "six backbones",
    "which suggests pre-hoc configuration selection without training as a target",
]


def norm(t: str) -> str:
    return re.sub(r"\s+", " ", t)


def main() -> int:
    files = sorted(glob.glob(str(REPO / "paper合" / "sections" / "*.tex"))) + \
        sorted(glob.glob(str(REPO / "paper合" / "main*.tex")))
    print("=" * 96)
    print("归一空白后逐项复核")
    print("=" * 96)
    bad = 0
    for need in NEEDLES:
        hits = []
        for f in files:
            t = norm(io.open(f, encoding="utf-8", errors="replace").read())
            if need in t:
                hits.append(Path(f).name)
        flag = "✅" if hits else "🔴"
        if not hits:
            bad += 1
        print(f"  {flag} {need[:62]:<64} {hits if hits else '缺失'}")
    print()
    print(f"  {len(NEEDLES) - bad}/{len(NEEDLES)} 通过")
    return 0 if bad == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
