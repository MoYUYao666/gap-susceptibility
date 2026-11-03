# -*- coding: utf-8 -*-
r"""修摘要里的计数与加限定（空白容忍正则版）（2026-10-12）。

上一次因摘要**跨行**导致字面锚点未命中（`\s+` 容忍换行）。

    python tools\_p302_fix_abstract_counts.py [--apply]
"""
from __future__ import annotations

import argparse
import glob
import io
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

# (正则, 替换, 说明)
SUBS = [
    (re.compile(r"Validation\s+spans\s+383\s+experiments\s+over\s+five\s+architectures,\s+"
                r"three\s+PEFT\s+methods\s+and\s+two\s+retrieval\s+datasets\."),
     r"Validation spans 383 experiments over six backbones (CLIP ViT-B/32, CLIP ViT-B/16, "
     r"CLIP ViT-L/14, OpenCLIP laion2B, SigLIP and BLIP-1), three PEFT methods and two "
     r"retrieval datasets.",
     "架构计数 five → six backbones（列名）"),
    (re.compile(r"removes\s+the\s+dominant\s+perturbation\s+source;"),
     r"removes the dominant perturbation source in the regime we swept;",
     "dominant perturbation source 加范围限定"),
]

TARGETS = ["paper合/main_nc.tex",
           "paper合/NC_submission/latex_source/main_nc.tex",
           "paper合/main_springer.tex"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    total = 0
    for rel in TARGETS:
        p = REPO / rel
        if not p.exists():
            print(f"  ❌ 缺 {rel}")
            continue
        t = io.open(p, encoding="utf-8", errors="replace").read()
        t2 = t
        for pat, rep, desc in SUBS:
            ms = list(pat.finditer(t2))
            print(f"  {Path(rel).name}: {desc} → 命中 {len(ms)}")
            if ms:
                t2 = pat.sub(lambda _m, r=rep: r, t2)
                total += len(ms)
        if a.apply and t2 != t:
            bak = p.with_suffix(p.suffix + ".bak_p302")
            if not bak.exists():
                io.open(bak, "w", encoding="utf-8", newline="").write(t)
            io.open(p, "w", encoding="utf-8", newline="").write(t2)
    if not a.apply:
        print("  （预演）")
        return 0
    print(f"\n  → 共改 {total} 处")
    bad = 0
    for f in glob.glob(str(REPO / "paper合" / "main*.tex")) + \
            glob.glob(str(REPO / "paper合" / "NC_submission" / "latex_source" / "main*.tex")) + \
            glob.glob(str(REPO / "paper合" / "highlights*.tex")):
        t = io.open(f, encoding="utf-8", errors="replace").read()
        for pat in ("five architectures", "median R2 of 0.97"):
            if pat in t:
                print(f"  🔴 '{pat}' 仍在 {Path(f).name}")
                bad += 1
    print(f"  残留检查: {'✅ 干净' if bad == 0 else f'{bad} 处'}")
    return 0 if bad == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
