# -*- coding: utf-8 -*-
r"""把 task-6 的结论加入摘要（空白容忍；守 250 词上限）（2026-10-12）。

**task-6**：各自调优后 LoRA（60.69 ± 0.05%）与 full-FT（60.87 ± 0.21%）**不可区分**。

    python tools\_p305_abstract_peft_lr.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import re
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

PAT = re.compile(r"so the text-only advantage is a property of the\s+architecture rather than "
                 r"a universal default\.")
ADD = (r"so the text-only advantage is a property of the architecture rather than a universal "
       r"default. Tuning each method to its own learning rate removes the adapter methods' "
       r"apparent advantage: LoRA and full fine-tuning then agree on zero-shot accuracy "
       r"($60.69\%$ against $60.87\%$).")

# 为腾出词数而压缩的从句
TRIM = [
    (re.compile(r"with the alignment energy as a state variable, the\s+rate of gap change is "
                r"the projection of the task gradient onto the alignment gradient,\s+"
                r"which yields a first-order ODE whose restoring coefficient is stable "
                r"within PEFT\."),
     r"with the alignment energy as the state variable, the rate of gap change is the task "
     r"gradient projected onto the alignment gradient, yielding a first-order ODE whose "
     r"restoring coefficient is stable within PEFT."),
    (re.compile(r"at mean \$R\^2 = 0\.949\$ over LoRA\s*\(\$0\.953\$ on Flickr30k, "
                r"\$0\.903\$ on MS-COCO\), against \$0\.00\$ for a constant baseline\."),
     r"at mean \$R^2 = 0.949\$ over LoRA, against \$0.00\$ for a constant baseline."),
    (re.compile(r"the family-clustered bootstrap\s+interval is \$\[-0\.89,-0\.62\]\$"),
     r"the family-clustered bootstrap interval is \$[-0.89,-0.62]\$"),
    (re.compile(r"Validation spans 383 experiments over six backbones and three PEFT methods\."),
     r"Validation spans 383 experiments over six backbones and three PEFT methods."),
    (re.compile(r"Fine-tuning a vision-language model on a small corpus often widens the gap "
                r"between its\s+image and text embeddings\."),
     r"Fine-tuning a vision-language model on a small corpus often widens the image--text gap."),
]

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
        n = len(PAT.findall(t))
        if n == 0:
            print(f"  ⚠️ {Path(rel).name}: 锚点 0")
            continue
        t2 = PAT.sub(lambda _m: ADD, t)
        for tp, tr in TRIM:
            if tp.search(t2):
                t2 = tp.sub(lambda _m, r=tr: r, t2)
                print(f"      （已压缩一个从句以腾出词数）")
        w = count_words(t2)
        flag = "✅" if 0 < w <= 250 else "🔴"
        print(f"  {flag} {Path(rel).name}: 锚点 {n} ｜ 改后 {w} 词")
        if w > 250:
            print("      🔴 超限，未写入")
            continue
        if a.apply:
            bak = p.with_suffix(p.suffix + ".bak_p305")
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
