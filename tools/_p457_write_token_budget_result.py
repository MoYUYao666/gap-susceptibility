# -*- coding: utf-8 -*-
r"""把"论文操作点 576 token 的直接测量"写进 P3（2026-10-13）。

## 依据（`outputs/analysis/p3d_e0_vs_token_budget_train_sel_n16.json`，device=cuda，n=16）

| max_pixels | tokens | `E0_real` | `E0_blank` | gap |
|---|---|---|---|---|
| 16384 | 15.3 | **21751.8** | 22400.1 | **+2.98%** |
| 50176 | 54.6 | **14717.8** | 22313.2 | **+51.61%** |
| 156800 | 188.4 | **9149.9** | 22696.9 | **+148.06%** |
| **802816** | **595.2** | **7472.3** | **23117.5** | **+209.37%** |

**⇒ $E_0^{\\text{real}}$ 单调降 66%（21752→7472）；$E_0^{\\text{blank}}$ 全域 <5%（22400→23118）**
**⇒ 论文操作点（595≈576 token）blank/real = 23117.5 / 7472.3 = 3.09×**

## 必须同时写的两条边界（成员已留档，含一条**负例**）

1. **绝对百分比依样本集而定**：15 token 下 train_sel（n=16）**+2.98%** vs held-out test（n=4）**+18.55%**（差 6 倍）
   ⇒ **只引"同批样本的趋势"，不引单一百分比**
2. **子样本会翻转趋势（负例留档）**：同一 test 划分取 **n=2** 时，gap 15 tok **+122.25%** → 54 tok **+103.71%（不升反降）**
   （`p3d_e0_vs_token_budget_test_n2.json`）⇒ **n 太小时连方向都不可信**

## 校准口径（成员自查更正，我采纳）

"逐位一致"**只在同一设备内成立**：CPU @15 tok = 21771.7 ↔ 归档冻结基线 21771.6993（CPU）；
**GPU @15 tok = 21751.8 ↔ 训练档 21751.8（GPU）**；**CPU 与 GPU 差 0.09%**（bf16 设备舍入）
⇒ **"管线已校准（同设备）"与"结论对预算/样本集敏感"必须严格分开写**

    python tools\_p457_write_token_budget_result.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
EX = REPO / "paper3" / "paper_ieee" / "sections" / "experiments.tex"

ANCHOR = "\\textbf{Blank images are not a neutral probe.}"

BLOCK = (
    "\\textbf{The probe measured at the paper's own operating point.} The comparison above\n"
    "is a statement about a probe measured at a particular visual budget, so we measured the\n"
    "budget dependence directly. This requires no training---the initialization energy is a\n"
    "single forward pass and is therefore deterministic for a given input, with no seed\n"
    "noise---so we could sweep the budget to the paper's own operating point rather than\n"
    "extrapolate to it. On one fixed set of $16$ samples, with every other setting held,\n"
    "$E_0$ for real images falls monotonically as the budget grows: $21{,}752$ at $15$\n"
    "tokens, $14{,}718$ at $55$, $9{,}150$ at $188$ and $7{,}472$ at $595$---a fall of\n"
    "$66\\%$. Over the same range $E_0$ for blank images barely moves ($22{,}400$, $22{,}313$,\n"
    "$22{,}697$, $23{,}118$; a spread under $5\\%$). At the paper's operating point\n"
    "($595$ tokens here against the paper's $576$) a blank image therefore sits at\n"
    "$3.09\\times$ the initialization energy of a real one ($23{,}118$ against $7{,}472$).\n"
    "This is the sharpest form of the objection. A blank image is not a neutral stand-in\n"
    "for an uninformative one: at a realistic budget it is a \\emph{different} input whose\n"
    "alignment energy is three times larger, and the $\\Delta E$ this paper reports is\n"
    "measured against that inflated baseline. The objective being optimised is therefore\n"
    "not the objective a real multimodal input induces, and the gap between them grows\n"
    "with the visual budget rather than shrinking. Two boundaries belong with this result.\n"
    "The absolute percentage is sample-dependent---at $15$ tokens the same measurement\n"
    "gives $3.0\\%$ on this sample set and $18.6\\%$ on a held-out one---so we report the\n"
    "trend within a fixed sample set and not a single number. And the trend itself is not\n"
    "robust to very small samples: drawing only two held-out samples reverses it at one\n"
    "budget ($+122\\%$ at $15$ tokens against $+104\\%$ at $55$), which is why we report the\n"
    "$n = 16$ curve and flag the counter-example rather than quote a percentage.\n"
    "\n")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(EX, encoding="utf-8", errors="replace").read()
    if "measured at the paper's own operating point" in t:
        print("  已写入")
        return 0
    n = t.count(ANCHOR)
    print(f"  锚点命中 {n}")
    if n != 1:
        print("  🔴 锚点未命中")
        return 1
    if not a.apply:
        print("  （预演）")
        return 0
    bak = EX.with_suffix(".tex.bak_p457")
    if not bak.exists():
        shutil.copy2(EX, bak)
    io.open(EX, "w", encoding="utf-8", newline="").write(t.replace(ANCHOR, BLOCK + ANCHOR, 1))
    t2 = io.open(EX, encoding="utf-8", errors="replace").read()
    checks = {
        "含 4 点曲线": "$21{,}752$" in t2 and "$7{,}472$" in t2,
        "含 66% 下降": "$66\\%$" in t2,
        "含 blank 不变（<5%）": "under $5\\%$" in t2,
        "含论文操作点 3.09×": "$3.09\\times$" in t2,
        "含'不是中性替代'": "not a neutral stand-in" in t2,
        "含样本集依赖边界": "$18.6\\%$" in t2,
        "含 n=2 负例": "reverses it at one" in t2,
        "声明无需训练/无 seed 噪声": "no seed\nnoise" in t2,
    }
    ok = True
    for k, v in checks.items():
        print(f"  {'✅' if v else '🔴'} {k}")
        ok = ok and v
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
