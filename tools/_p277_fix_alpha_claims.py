# -*- coding: utf-8 -*-
r"""修 `paper合` 三处"α 普适/一致为负"（与归档矛盾）（2026-10-12）。

## 归档证据（`tools/_p276_alpha_sign.py` 实测）

| 归档 | n | 负 | 非负 | 最大 |
|---|---|---|---|---|
| `outputs/analysis/ode_ledger.json` | 103 | 99 | **4** | **+0.010505** |
| `outputs/analysis/ode_loco.json` | 33 | 32 | **1** | +0.004032 |
| `outputs/theory/adapter/adapter_all_results.json` | 50 | 40 | **10** | **+0.060828** |
| `outputs/theory/bitfit/bitfit_results.json` | 3 | 0 | **3** | **+0.000443** |
| **合计** | **222** | 203 | **19** | |

→ 不能写 *universally / consistently negative*。

    python tools\_p277_fix_alpha_claims.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

PAIRS = [
    # conclusion.tex:9
    ("paper合/sections/conclusion.tex",
     r"and $\alpha$ is negative on both datasets. $\alpha$ is universally negative for PEFT, "
     r"and $\beta$ is stable",
     r"and $\alpha$ is negative on both datasets. Across the $222$ fits we archived, "
     r"$\alpha < 0$ in $203$; the $19$ exceptions are ten of the fifty Adapter fits "
     r"(largest $+0.061$), four LoRA fits (largest $+0.011$) and all three CLIP BitFit fits "
     r"($\alpha \approx +4\times10^{-4}$, i.e.\ numerically zero), so we state the protective "
     r"bound as the dominant rather than a universal regime, and $\beta$ is stable"),
    # validation.tex:73
    ("paper合/sections/validation.tex",
     r"First, $\alpha$ is consistently negative for all PEFT configurations, confirming the "
     r"protective bound.",
     r"First, $\alpha$ is negative for the large majority of PEFT configurations "
     r"($203$ of the $222$ fits we archived), which supports the protective bound while "
     r"leaving a minority of counter-examples that we report in Section~\ref{sec:discussion} "
     r"(ten Adapter fits up to $+0.061$, four LoRA fits up to $+0.011$, and the three CLIP "
     r"BitFit fits at $\alpha \approx +4\times10^{-4}$)."),
    # validation.tex:109
    ("paper合/sections/validation.tex",
     r"$\alpha$ is consistently negative for all PEFT configurations on both Flickr30k and "
     r"COCO, confirming that the protective bound generalizes across datasets.",
     r"$\alpha$ is negative for $203$ of the $222$ archived fits on both Flickr30k and "
     r"COCO, so the protective bound holds across datasets as a dominant tendency rather "
     r"than without exception; the exceptions are enumerated in "
     r"Section~\ref{sec:discussion}."),
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
        print(f"  {rel}: 命中 {n}")
        if n == 0:
            continue
        if not a.apply:
            continue
        bak = p.with_suffix(p.suffix + ".bak_p277")
        if not bak.exists():
            shutil.copy2(p, bak)
        io.open(p, "w", encoding="utf-8", newline="").write(t.replace(old, new))
        total += n
    if not a.apply:
        print("  （预演）")
        return 0
    print(f"\n  → 共改 {total} 处")
    # 核对
    import glob
    bad = []
    for f in glob.glob(str(REPO / "paper合" / "sections" / "*.tex")) + \
            glob.glob(str(REPO / "paper合" / "main*.tex")):
        t = io.open(f, encoding="utf-8", errors="replace").read()
        if "universally negative" in t or "consistently negative" in t:
            bad.append(Path(f).name)
    print(f"  残留 'universally/consistently negative': {bad if bad else '✅ 无'}")
    return 0 if not bad else 2


if __name__ == "__main__":
    raise SystemExit(main())
