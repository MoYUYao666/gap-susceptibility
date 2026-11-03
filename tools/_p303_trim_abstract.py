# -*- coding: utf-8 -*-
r"""压缩 `paper合` 摘要到 ≤250 词（Neurocomputing 限 250）（2026-10-12）。

## 现状

PR 改稿中我往摘要里加了两段（聚类稳健统计、full-FT 的 lr 结果），
从 333 词涨到 **361 词**，**超 Neurocomputing 的 250 词上限**。

## 压缩策略（保主要发现与诚实限制，删冗余）

| 段 | 处置 |
|---|---|
| 经验刻画 | 保留，压缩措辞 |
| ODE 推导 | 保留，压缩 |
| three consequences | 压成一句 |
| 验证/严格冻结 | 保留 |
| **聚类稳健统计**（新加） | **保留但压到 2 句**（这是回应审稿人的关键） |
| full-FT 的 lr 细节 | **摘要里删掉**（正文有专段；摘要只需不提崩塌） |

    python tools\_p303_trim_abstract.py [--apply]
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
    "Fine-tuning a vision-language model on a small corpus often widens the gap between its\n"
    "image and text embeddings. We first characterise when this happens. Across $n=204$\n"
    "archived runs drawn from six dataset $\\times$ backbone cells, the Distribution Gap\n"
    "predicts retrieval degradation ($r=-0.71$) more strongly than the Centroid Gap\n"
    "($r=-0.59$), and which part of the model\n"
    "is adapted matters more than how its adapters are configured. We then derive \\emph{Gap\n"
    "Susceptibility} from gradient flow: with the alignment energy as a state variable, the\n"
    "rate of gap change is the projection of the task gradient onto the alignment gradient,\n"
    "which yields a first-order ODE whose restoring coefficient is stable within PEFT. Fitted\n"
    "per run, the ODE reproduces the gap trajectory at mean $R^2 = 0.949$ over LoRA\n"
    "($0.953$ on Flickr30k, $0.903$ on MS-COCO), against $0.00$ for a constant baseline.\n"
    "Validation spans 383 experiments over six backbones and three PEFT methods. A\n"
    "strict-freezing control that trains only adapter matrices confirms the predicted ordering\n"
    "on CLIP and reverses it on SigLIP, so the text-only advantage is a property of the\n"
    "architecture rather than a universal default. Because the runs are nested rather than\n"
    "independent, we report the gap--retrieval association with cluster-robust inference: the\n"
    "slope is $-1.05$ (CR1 standard error $0.29$, $p=0.016$) and the family-clustered bootstrap\n"
    "interval is $[-0.89,-0.62]$---an order of magnitude less precision than $204$\n"
    "independent runs would give.\n")

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
        # Elsevier: \begin{abstract}...\end{abstract}
        m = re.search(r"(\\begin\{abstract\}\n)(.*?)(\n\\end\{abstract\})", t, re.S)
        if m:
            t2 = t[:m.start(2)] + NEW_ABS.rstrip("\n") + t[m.end(2):]
        else:
            m2 = re.search(r"(\\abstract\{)(.*?)(\n\})", t, re.S)
            if not m2:
                print(f"  🔴 {Path(rel).name}: 找不到摘要环境")
                continue
            t2 = t[:m2.start(2)] + NEW_ABS.rstrip("\n") + t[m2.end(2):]
        after = count_words(t2)
        flag = "✅" if 0 < after <= 250 else "🔴"
        print(f"  {flag} {Path(rel).name}: {before} → {after} 词")
        if after > 250:
            print("      🔴 仍超限，未写入")
            continue
        if a.apply:
            bak = p.with_suffix(p.suffix + ".bak_p303")
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
            print(f"  复核 {Path(rel).name}: {count_words(io.open(p, encoding='utf-8', errors='replace').read())} 词")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
