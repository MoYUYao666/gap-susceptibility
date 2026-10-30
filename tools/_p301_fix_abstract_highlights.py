# -*- coding: utf-8 -*-
r"""统一摘要计数 + 修 highlights 的 R²（2026-10-12）。

## 查出

| 位置 | 问题 | 归档 |
|---|---|---|
| 摘要 | *"383 experiments over **five architectures**"* 与 conclusion 的 "six backbones" 不一致 | — |
| 摘要 | *"three consequences follow: … the **dominant perturbation source**"* 与 task-5 的发现张力 | `docs/PR_FAIRNESS_FIX.md` |
| highlights | *"An ODE predicts gap trajectories at **median R2 of 0.97**"* | `ode_ledger.json::subsets.lora.median = **0.9565**` → 应为 **0.96** |

    python tools\_p301_fix_abstract_highlights.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

PAIRS = [
    # 摘要：架构计数统一
    ("paper合/main_nc.tex",
     r"Validation spans 383 experiments over five architectures, three PEFT methods and "
     r"two retrieval datasets.",
     r"Validation spans 383 experiments over six backbones (CLIP ViT-B/32, CLIP ViT-B/16, "
     r"CLIP ViT-L/14, OpenCLIP laion2B, SigLIP and BLIP-1), three PEFT methods and two "
     r"retrieval datasets."),
    ("paper合/NC_submission/latex_source/main_nc.tex",
     r"Validation spans 383 experiments over five architectures, three PEFT methods and "
     r"two retrieval datasets.",
     r"Validation spans 383 experiments over six backbones (CLIP ViT-B/32, CLIP ViT-B/16, "
     r"CLIP ViT-L/14, OpenCLIP laion2B, SigLIP and BLIP-1), three PEFT methods and two "
     r"retrieval datasets."),
    ("paper合/main_springer.tex",
     r"Validation spans 383 experiments over five architectures, three PEFT methods and "
     r"two retrieval datasets.",
     r"Validation spans 383 experiments over six backbones (CLIP ViT-B/32, CLIP ViT-B/16, "
     r"CLIP ViT-L/14, OpenCLIP laion2B, SigLIP and BLIP-1), three PEFT methods and two "
     r"retrieval datasets."),
    # 摘要：dominant perturbation source 加限定（与 task-5 一致）
    ("paper合/main_nc.tex",
     r"adaptation position, since removing the visual gradient term removes the dominant "
     r"perturbation source;",
     r"adaptation position, since removing the visual gradient term removes the dominant "
     r"perturbation source in the regime we swept;"),
    # highlights：R² 0.97 → 0.96
    ("paper合/highlights_nc.tex",
     r"\item An ODE predicts gap trajectories at median R2 of 0.97",
     r"\item An ODE predicts gap trajectories at median R2 of 0.96"),
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    total = 0
    for rel, old, new in PAIRS:
        p = REPO / rel
        if not p.exists():
            print(f"  ❌ 缺 {rel}")
            continue
        t = io.open(p, encoding="utf-8", errors="replace").read()
        n = t.count(old)
        print(f"  {'✅' if n >= 1 else '⚠️ '} {Path(rel).name}: {n} ｜ "
              f"{old[:50].replace(chr(10), ' ')}…")
        if n == 0:
            continue
        if a.apply:
            bak = p.with_suffix(p.suffix + ".bak_p301")
            if not bak.exists():
                shutil.copy2(p, bak)
            io.open(p, "w", encoding="utf-8", newline="").write(t.replace(old, new))
            total += n
    if not a.apply:
        print("\n  （预演）")
        return 0
    print(f"\n  → 共改 {total} 处")
    # 核对
    import glob
    bad = 0
    for f in glob.glob(str(REPO / "paper合" / "main*.tex")) + \
            glob.glob(str(REPO / "paper合" / "highlights*.tex")) + \
            glob.glob(str(REPO / "paper合" / "NC_submission" / "latex_source" / "main*.tex")):
        t = io.open(f, encoding="utf-8", errors="replace").read()
        for pat in ("five architectures", "median R2 of 0.97"):
            if pat in t:
                print(f"  🔴 残留 '{pat}' in {Path(f).name}")
                bad += 1
    print(f"  残留检查: {'✅ 干净' if bad == 0 else f'{bad} 处'}")
    return 0 if bad == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
