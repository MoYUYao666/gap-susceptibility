# -*- coding: utf-8 -*-
r"""补漏：上一轮未覆盖的 4 处旧值（2026-10-07）。

## 上一轮漏了什么

`_pa_align_ode_numbers.py` 的模式未覆盖：

| 文件 | 位置 | 现值 | 处置 |
|---|---|---|---|
| `discussion.tex:5` | "Why Gap Susceptibility Matters" | `mean R² = 0.986 (range 0.978–0.997)` | **改** |
| `validation.tex:73` | 三条 robust patterns 首条 | `mean R² = 0.985 over the LoRA 26 configurations` | **改 R²；配置数待核** |
| `validation.tex:4` | Phase 2 开头 | `162 experiments (81 per dataset)` | **改** |
| `supplement.tex:3` | 实验目录导言 | `further 162 ODE-fitting runs … 383 in total` | **改** |

**假警报（不动）**：`related_work.tex:7` 的 `R²=0.986` 是**他人工作**（Liu et al. 2026）的数值；
`162` 的两处命中在 **arXiv 编号 `2604.16256`** 里。

## ⚠️ 另有两项**不能动**（会需要归档支撑）

1. **`supplement.tex` 的 COCO 表（14 行）**：本地只有 **3 配置 × 3 seed**，
   正文为 **14 配置 × 5 seed + 5 + 5 = 81** → **无法复现**。**改数据表却无归档＝编造**，故不动，
   改在 limitation 中如实说明范围。
2. **`26 configurations`**：本地 LoRA 配置数按（数据集×位置×秩）计为 **18**；
   正文的 26 可能含未归档配置 → **待核**，本轮先只改 R²。

    python tools\_pa_align_ode_numbers2.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
P = REPO / "paper合" / "sections"

REPS = [
    (P / "discussion.tex", "block",
     "The answer, as Section~\\ref{sec:validation} shows, is affirmative for the LoRA configurations: "
     "mean $R^2 = 0.986$ (range $0.978$--$0.997$) across the CLIP runs tested.",
     "The answer, as Section~\\ref{sec:validation} shows, is affirmative for the LoRA configurations: "
     "mean $R^2 = 0.949$ (range $0.814$--$0.977$) across the archived CLIP runs, fitted one run at a time.",
     "discussion 0.986"),

    (P / "validation.tex", "block",
     "Third, the exponential form fits all trajectories with mean $R^2 = 0.985$ over the LoRA",
     "Third, the exponential form fits all trajectories with mean $R^2 = 0.949$ over the archived LoRA",
     "validation 0.985"),

    (P / "validation.tex", "block",
     "We fit the ODE on 162 experiments (81 per dataset) spanning CLIP LoRA over two datasets (Flickr30k, MS-COCO)",
     "We fit the ODE on the 55 archived LoRA runs (43 on Flickr30k, 6 on MS-COCO) spanning CLIP LoRA over two datasets (Flickr30k, MS-COCO)",
     "validation 162"),

    (P / "supplement.tex", "block",
     "a further 162 ODE-fitting runs are catalogued in Section~\\ref{sec:validation}, giving 383 in total.",
     "a further 55 ODE-fitting runs are archived for Section~\\ref{sec:validation} and analysed there, "
     "alongside a full-fine-tuning pilot and a bias-only BitFit control on a second architecture.",
     "supplement 162/383"),
]


def main() -> int:
    apply = "--apply" in sys.argv
    ok = miss = 0
    for path, _, old, new, why in REPS:
        t = io.open(path, encoding="utf-8").read()
        c = t.count(old)
        if c == 1:
            print(f"  ✅ {why}")
            if apply:
                io.open(path, "w", encoding="utf-8", newline="").write(t.replace(old, new, 1))
            ok += 1
        else:
            print(f"  ⚠ {why}：命中 {c}")
            if c == 0:
                i = t.find(old[:60])
                print(f"     实际: {t[max(0,i-40):i+160]!r}" if i > 0 else "     （前缀也未命中）")
            miss += 1
    print(f"\n  {ok}/{len(REPS)} 处" + ("（已写入）" if apply else "（预演）"))
    return 0 if miss == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
