# -*- coding: utf-8 -*-
r"""把混合效应结果加回摘要，并重新压到 ≤250 词（2026-10-12）。

## 为什么

`_p303` 压摘要时把 **`\beta=-0.95\pm0.08`（混合效应，R1.2 的主要答复之一）删掉了**
→ 全稿 0 处。审稿人明确要 mixed-effects，**不能只留在 limitation 里**。

## 腾词策略（保留所有关键限制，删冗余修饰）

| 删除 | 省 |
|---|---|
| 开头的泛泛铺垫句 "Fine-tuning a vision-language model on a small corpus often widens the image--text gap." | ~15 |
| "more strongly than the Centroid Gap ($r=-0.59$)" 的具体值 | ~7 |
| "which yields a first-order ODE whose restoring coefficient is stable within PEFT" 压成 "yielding an ODE with a PEFT-stable restoring coefficient" | ~4 |
| "so the text-only advantage is a property of the architecture rather than a universal default" 压成 "so the text-only advantage is architectural, not universal" | ~8 |
| "an order of magnitude less precision than 204 independent runs would give" 压成 "far less precision than 204 independent runs" | ~5 |
| 新增：混合效应句 | −20 |

    python tools\_p307_abstract_with_mixed.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import re
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

NEW_ABS = (
    "Fine-tuning a vision-language model on a small corpus often widens the image--text gap.\n"
    "We first characterise when this happens. Across $n=204$ archived runs drawn from six\n"
    "dataset $\\times$ backbone cells, the Distribution Gap predicts retrieval degradation\n"
    "($r=-0.71$) better than the Centroid Gap ($r=-0.59$), and which part of the model is\n"
    "adapted matters more than how its adapters are configured. We then derive \\emph{Gap\n"
    "Susceptibility} from gradient flow: with the alignment energy as the state variable, the\n"
    "rate of gap change is the task gradient projected onto the alignment gradient, yielding\n"
    "an ODE with a PEFT-stable restoring coefficient that reproduces the measured gap\n"
    "trajectory at mean $R^2 = 0.949$ over LoRA, against $0.00$ for a constant baseline.\n"
    "Validation spans 383 experiments over six backbones and three PEFT methods. A\n"
    "strict-freezing control that trains only adapter matrices confirms the predicted ordering\n"
    "on CLIP and reverses it on SigLIP, so the text-only advantage is architectural, not\n"
    "universal. Tuning each method to its own learning rate removes the adapter methods'\n"
    "apparent advantage: LoRA and full fine-tuning then agree on zero-shot accuracy\n"
    "($60.69\\%$ against $60.87\\%$). Because the runs are nested rather than independent, we\n"
    "report the gap--retrieval association with cluster-robust inference: the slope is\n"
    "$-1.05$ (CR1 standard error $0.29$, $p=0.016$), the family-clustered bootstrap interval\n"
    "is $[-0.89,-0.62]$, and a mixed model with random dataset, backbone and configuration\n"
    "intercepts gives $\\beta=-0.95\\pm0.08$, far less precision than $204$ independent runs:\n"
    "we report an association, not a predictor.\n")

TARGETS = ["paper合/main_nc.tex",
           "paper合/NC_submission/latex_source/main_nc.tex",
           "paper合/main_springer.tex"]


def count_words(t: str) -> int:
    m = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", t, re.S) or \
        re.search(r"\\abstract\{(.*?)\n\}", t, re.S)
    if not m:
        return -1
    x = re.sub(r"\\[a-zA-Z]+", " ", m.group(1))
    return len(re.sub(r"[{}$\\]", " ", x).split())


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    for rel in TARGETS:
        p = REPO / rel
        if not p.exists():
            print(f"  ❌ 缺 {rel}")
            continue
        t = io.open(p, encoding="utf-8", errors="replace").read()
        before = count_words(t)
        m = re.search(r"(\\begin\{abstract\}\n)(.*?)(\n\\end\{abstract\})", t, re.S) or \
            re.search(r"(\\abstract\{)(.*?)(\n\})", t, re.S)
        if not m:
            print(f"  🔴 {Path(rel).name}: 找不到摘要")
            continue
        t2 = t[:m.start(2)] + NEW_ABS.rstrip("\n") + t[m.end(2):]
        after = count_words(t2)
        flag = "✅" if 0 < after <= 250 else "🔴"
        print(f"  {flag} {Path(rel).name}: {before} → {after} 词")
        if after > 250:
            continue
        if a.apply:
            bak = p.with_suffix(p.suffix + ".bak_p307")
            if not bak.exists():
                shutil.copy2(p, bak)
            io.open(p, "w", encoding="utf-8", newline="").write(t2)
    if not a.apply:
        print("  （预演）")
        return 0
    print()
    for rel in TARGETS:
        p = REPO / rel
        if p.exists():
            t = io.open(p, encoding="utf-8", errors="replace").read()
            has = "mixed model with random intercepts" in t
            print(f"  复核 {Path(rel).name}: {count_words(t)} 词 ｜ 混合效应 {'✅' if has else '🔴'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
