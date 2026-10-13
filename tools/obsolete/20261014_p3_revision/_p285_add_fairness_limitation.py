# -*- coding: utf-8 -*-
r"""把 task-5 建议的 R1.6 limitation 句写进 `discussion.tex`（2026-10-12）。

**task-5 给的句子**（`docs/PR_FAIRNESS_FIX.md` §6.2）：
> Full fine-tuning is far more learning-rate sensitive than the adapter methods, so our
> full-fine-tuning comparison is a comparison at one shared learning rate rather than at
> each method's optimum: over lr ∈ {1e-6 … 3e-4} its zero-shot accuracy spans 60.9 % to
> 0.1 % and its ΔCG spans −0.002 to +0.80, and the collapse we report is the behaviour of
> the shared rate (1e-4), not of full fine-tuning as such.

    python tools\_p285_add_fairness_limitation.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "paper合" / "sections" / "discussion.tex"

LIM = (
    r"\item \textbf{Our full-fine-tuning comparison is made at one shared learning rate, "
    r"not at each method's optimum.} Full fine-tuning is far more learning-rate sensitive "
    r"than the adapter methods: over $\mathrm{lr}\in\{10^{-6},\dots,3\times10^{-4}\}$ its "
    r"zero-shot accuracy spans $60.9\%$ to $0.1\%$ and its $\Delta\mathrm{CG}$ spans "
    r"$-0.002$ to $+0.80$, monotonically. The collapse we report is therefore the behaviour "
    r"of the shared rate ($10^{-4}$) rather than of full fine-tuning as such, and at "
    r"$10^{-6}$ full fine-tuning matches the frozen model in alignment. Three caveats "
    r"travel with this: the best rate we found is the boundary of our grid, so lower rates "
    r"are untested; only one seed was run at $3\times10^{-5}$, $10^{-4}$ and "
    r"$3\times10^{-4}$; and we did not sweep the learning rate of the LoRA and Adapter "
    r"methods, so the stronger test of tuning every method to its own optimum remains open."
    "\n")

# 插在 Limitations 小节第一条之后（作为新的一条）
ANCHOR = r"\subsection{Limitations and Future Work}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(F, encoding="utf-8", errors="replace").read()
    if "shared learning rate, not at each method's optimum" in t:
        print("  已存在，跳过")
        return 0
    n = t.count(ANCHOR)
    print(f"  锚点 {ANCHOR} 命中 {n}")
    if n != 1:
        return 1
    t2 = t.replace(ANCHOR, ANCHOR + "\n\n" + LIM, 1)
    if not a.apply:
        print("  （预演）")
        return 0
    bak = F.with_suffix(".tex.bak_p285")
    if not bak.exists():
        shutil.copy2(F, bak)
    io.open(F, "w", encoding="utf-8", newline="").write(t2)
    t3 = io.open(F, encoding="utf-8", errors="replace").read()
    ok = ("shared learning rate, not at each method's optimum" in t3
          and "60.9\\%" in t3)
    print(f"  {'✅ 已插入' if ok else '🔴 失败'}")
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
