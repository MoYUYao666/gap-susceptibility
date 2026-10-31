# -*- coding: utf-8 -*-
r"""核实：严格冻结对照的 run 是否被计入论文的实验目录（2026-10-05）。

## 背景

`paper合/sections/supplement.tex` 的 `tab:full_experiments` 列出 **13 类、合计 117 个**实验，
但**没有"严格冻结对照"这一类**。而本稿的核心主张（适配位置效应）**正是靠严格冻结才能成立**
（legacy 约定下 text-only 臂实际训练约 1.45 亿参数，未隔离适配位置）。

若这些 run 未被计数，则论文**少报了自己的实验量**，更重要的是**把最强证据放在了目录之外**。

## 本脚本盘点的严格冻结 run

| 目录 | 内容 |
|---|---|
| `outputs/strict_freeze/` | CLIP r8 三臂（text_only / both / vision_only） |
| `outputs/strict_freeze_rank/r{1,4,16,32,64}/` | CLIP rank sweep |
| `outputs/strict_freeze_openclip/` | OpenCLIP r8 三臂 |
| `outputs/strict_freeze_openclip_rank/r4/` | OpenCLIP r4 两臂 |
| `outputs/siglip_strict/*/s4_siglip_lora_{text_only,both}` | SigLIP r8 两臂 |
| `outputs/siglip_strict/*/s6_siglip_lora_vision_only` | SigLIP r8 vision_only |
| `outputs/siglip_strict/*/s7_siglip_lora_r4_*` | SigLIP r4 两臂 |

    python tools\_count_strictfreeze_runs.py
"""
from __future__ import annotations

import glob
import json
import statistics as st
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

GROUPS = [
    ("CLIP r8 三臂", "outputs/strict_freeze/*/seed*/results.json"),
    ("CLIP rank sweep r1/4/16/32/64", "outputs/strict_freeze_rank/r*/*/seed*/results.json"),
    ("OpenCLIP r8 三臂", "outputs/strict_freeze_openclip/*/seed*/results.json"),
    ("OpenCLIP r4 两臂", "outputs/strict_freeze_openclip_rank/r4/*/seed*/results.json"),
    ("SigLIP r8 text_only/both", "outputs/siglip_strict/*/s4_siglip_lora_*/results.json"),
    ("SigLIP r8 vision_only", "outputs/siglip_strict/*/s6_siglip_lora_vision_only/results.json"),
    ("SigLIP r4 两臂", "outputs/siglip_strict/*/s7_siglip_lora_r4_*/results.json"),
    ("BioCLIP r4 三臂", "outputs/strict_freeze_bioclip/run_log.txt"),
]


def main() -> int:
    total = 0
    by_backbone: dict[str, int] = defaultdict(int)
    print("=== 严格冻结对照 run 盘点 ===")
    for name, pat in GROUPS:
        files = sorted(glob.glob(str(REPO / pat)))
        n = len(files)
        total += n
        if "CLIP" in name and "Open" not in name:
            by_backbone["CLIP ViT-B/32"] += n
        elif "OpenCLIP" in name:
            by_backbone["OpenCLIP ViT-B/32"] += n
        elif "SigLIP" in name:
            by_backbone["SigLIP ViT-B/16"] += n
        # 抽一个可训参数作配置核验
        ntr = ""
        if files:
            try:
                d = json.loads(Path(files[0]).read_text(encoding="utf-8", errors="ignore"))
                ntr = f"  可训={d.get('n_trainable_params')}"
            except Exception:
                pass
        print(f"  {name:<34} {n:>3} 个 run{ntr}")

    print(f"\n  合计 **{total}** 个严格冻结 run")
    print("  按骨干：")
    for k, v in sorted(by_backbone.items(), key=lambda x: -x[1]):
        print(f"    {k:<22} {v}")

    print("\n=== 与论文计数对照 ===")
    print("  论文 `tab:full_experiments`（附录 A）：13 类、合计 **117**（**不含严格冻结对照**）")
    print("  论文另称：162 个 ODE 拟合、278 个实验（117 + 162 - 1？）")
    print(f"  → 严格冻结对照 **{total}** 个 run **未出现在任何计数中**")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
