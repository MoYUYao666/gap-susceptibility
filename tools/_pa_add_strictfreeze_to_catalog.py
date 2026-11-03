# -*- coding: utf-8 -*-
r"""把严格冻结对照（95 个 run）计入实验目录与全文计数（2026-10-05）。

## 问题（操作者提出："实验数量有变化呀"）

`tab:full_experiments` 列 **13 类、117 个**（Part I），另称 162 个 ODE 拟合、278 个总计 ——
**但本稿最强的证据（适配位置效应）所依赖的严格冻结对照，95 个 run，完全不在计数里**。

`tools/_count_strictfreeze_runs.py` 盘点：

| 组 | run 数 |
|---|---|
| CLIP r8 三臂 | 15 |
| CLIP rank sweep r1/4/16/32/64 | 30 |
| OpenCLIP r8 三臂 | 15 |
| OpenCLIP r4 两臂 | 10 |
| SigLIP r8 text_only/both | 10 |
| SigLIP r8 vision_only | 5 |
| SigLIP r4 两臂 | 10 |
| **合计** | **95**（CLIP 45 / OpenCLIP 25 / SigLIP 25） |

## 改法

1. **附录目录表**：新增一行 "XIV. Strict-freezing controls" = 95，并把 Total 改为 **374**；
2. **附录正文**：说明 117 是 Part I 的机理实验，另有 95 个严格冻结对照；
3. **正文各处的 117 / 278**：改为"117 机理实验 + 95 严格冻结对照"与总数 **374**。

## 纪律

每个数字都由 `tools/_count_strictfreeze_runs.py` 从 `outputs/` 实测得出，非估计。

    python tools\_pa_add_strictfreeze_to_catalog.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SEC = REPO / "paper合" / "sections"

N_SF = 95
N_PART1 = 117
N_ODE = 162
N_TOTAL = N_PART1 + N_ODE + N_SF      # 374

EDITS = [
    # ① 目录表：新增一行 + 改 Total
    #    踩坑记录：表行在文件里**无缩进**；我曾写成两个空格前缀，导致命中 0 次却误以为是反斜杠问题。
    #    （反斜杠本身是对的：Python 非 raw 字符串里 `\\` = 文件中的一个反斜杠。）
    (SEC / "supplement.tex",
     "XIII. Zero-Shot Generalization and SigLIP & 8 \\\\\n"
     "\\midrule\n"
     "\\textbf{Total} & \\textbf{117} \\\\",
     "XIII. Zero-Shot Generalization and SigLIP & 8 \\\\\n"
     "XIV. Strict-Freezing Controls (three backbones, $r\\in[1,64]$) & 95 \\\\\n"
     "\\midrule\n"
     "\\textbf{Total} & \\textbf{374} \\\\"),    # ② 附录正文首句
    (SEC / "supplement.tex",
     "Table~\\ref{tab:full_experiments} lists all 117 experiments from Part~I.",
     "Table~\\ref{tab:full_experiments} lists all 374 experiments reported in this paper: 117 mechanism "
     "experiments from Part~I, 162 ODE-fitting runs, and 95 strict-freezing controls. The last group is "
     "the one on which the adaptation-position findings rest, since only under strict freezing do the "
     "arms differ solely in where the adapters sit."),
    # ③ 表注
    (SEC / "supplement.tex",
     "The per-run rows, configurations and metrics of all 117 experiments are released with the analysis ",
     "The per-run rows, configurations and metrics of all 374 experiments are released with the analysis "),
]

# 正文计数（separate，逐个精确替换）
COUNT_EDITS = [
    (SEC / "empirical.tex",
     "These experiments, spanning 117 experiments, establish the regularities",
     "These experiments, 117 under the earlier convention and 95 under strict freezing, establish the "
     "regularities"),
    (SEC / "empirical.tex",
     "The complete experiment catalog (117 experiments) is provided in Appendix~A.",
     "The complete experiment catalog (374 experiments) is provided in Appendix~A."),
    (SEC / "conclusion.tex",
     "spanning 278 experiments across five model architectures, three PEFT methods, and two retrieval datasets",
     "spanning 374 experiments across five model architectures, three PEFT methods, and two retrieval "
     "datasets"),
    (SEC / "conclusion.tex",
     "a systematic empirical characterization of modality gap evolution under PEFT (117 experiments)",
     "a systematic empirical characterization of modality gap evolution under PEFT, covering 117 mechanism "
     "experiments and 95 strict-freezing controls"),
    (SEC / "introduction.tex",
     "This paper examines that suggestion across 117 experiments on five architectures",
     "This paper examines that suggestion across 374 experiments on five architectures"),
    (SEC / "introduction.tex",
     "spanning 117 experiments across two PEFT methods, five architectures, and two datasets",
     "spanning 374 experiments across two PEFT methods, five architectures, and two datasets"),
    (SEC / "validation.tex",
     "validated by 278 experiments spanning three PEFT methods (LoRA, Adapter, BitFit) and two datasets",
     "validated by 374 experiments spanning three PEFT methods (LoRA, Adapter, BitFit) and two datasets"),
]


def main() -> int:
    apply = "--apply" in sys.argv
    print(f"  将把计数从 117/278 改为 {N_TOTAL}（117 机理 + 162 ODE + {N_SF} 严格冻结）\n")
    n = 0
    for p, old, new in EDITS + COUNT_EDITS:
        t = io.open(p, encoding="utf-8").read()
        c = t.count(old)
        if c == 1:
            print(f"  ✅ {p.name}: {old[:52]}…")
            if apply:
                io.open(p, "w", encoding="utf-8", newline="").write(t.replace(old, new, 1))
            n += 1
        else:
            print(f"  ⚠ {p.name}: 命中 {c} 次 — {old[:52]}…")
    if apply:
        left = 0
        for f in list(SEC.glob("*.tex")) + [REPO / "paper合" / "main_nc.tex"]:
            s = io.open(f, encoding="utf-8").read()
            left += s.count("117 experiments") + s.count("278 experiments")
        print(f"\n  {'✅' if left == 0 else '⚠'} 残留 '117/278 experiments': {left} 处")
    print(f"  {n}/{len(EDITS + COUNT_EDITS)} 处{'已改' if apply else '可改'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
