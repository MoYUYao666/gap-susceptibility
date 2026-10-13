# -*- coding: utf-8 -*-
r"""修零样本绝对否定（用逐字锚点，`_p427` 未命中）（2026-10-12）。

`experiments.tex` 逐字（注意换行）：
```
\textbf{Zero-shot constraint.} No $\Gamma$ measurement, gradient alignment,
or calibration is performed on LLaVA or Qwen-VL before training; all
predictions derive from the CLIP structural law~\cite{wan2026gap}.
```

    python tools\_p428_fix_zeroshot2.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
EX = REPO / "paper3" / "paper_ieee" / "sections" / "experiments.tex"

OLD = (
    "\\textbf{Zero-shot constraint.} No $\\Gamma$ measurement, gradient alignment,\n"
    "or calibration is performed on LLaVA or Qwen-VL before training; all\n"
    "predictions derive from the CLIP structural law~\\cite{wan2026gap}.")

NEW = (
    "\\textbf{Zero-shot constraint.} No target-model gradient enters an allocation\n"
    "\\emph{decision}: every rank we assign is derived from the CLIP structural\n"
    "law~\\cite{wan2026gap} and from quantities computable before training the target.\n"
    "We do compute $\\Gamma_k$ on the target models, but only \\emph{after} the fact and\n"
    "only for diagnosis---to check whether the ordering the CLIP law predicts is the\n"
    "ordering the target exhibits (Appendix~D; the per-block values for Qwen2-VL appear\n"
    "in Finding~4 below). Those measurements are never used to choose an allocation,\n"
    "which is why the predictions can be evaluated on LLaVA and Qwen2-VL without the\n"
    "circularity that a gradient-informed decision would imply.")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(EX, encoding="utf-8", errors="replace").read()
    n = t.count(OLD)
    print(f"  锚点命中 {n}")
    if n != 1:
        return 1
    if not a.apply:
        print("  （预演）")
        return 0
    bak = EX.with_suffix(".tex.bak_p428")
    if not bak.exists():
        shutil.copy2(EX, bak)
    io.open(EX, "w", encoding="utf-8", newline="").write(t.replace(OLD, NEW))
    t2 = io.open(EX, encoding="utf-8", errors="replace").read()
    checks = {
        "删除绝对否定": "No $\\Gamma$ measurement, gradient alignment" not in t2,
        "改为分配决策不含梯度": "No target-model gradient enters an allocation" in t2,
        "声明 Γ 是事后诊断": "only \\emph{after} the fact" in t2,
        "引用附录 D 与 Finding 4": "Appendix~D; the per-block values" in t2,
        "声明不用 Γ 选分配": "never used to choose an allocation" in t2,
    }
    ok = True
    for k, v in checks.items():
        print(f"  {'✅' if v else '🔴'} {k}")
        ok = ok and v
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
