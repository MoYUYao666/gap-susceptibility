# -*- coding: utf-8 -*-
r"""按 task-6（LoRA/Adapter 的 lr 扫描）改稿（2026-10-12）。

## 结论（`outputs/analysis/pr_peft_lr_sweep.json`，24 run / 2 seed / 0 失败）

| 配置 @ lr | zero-shot top-1 | ΔCG |
|---|---|---|
| frozen | 59.91% | — |
| **LoRA-both @ 1e-5（其最优）** | **60.69 ± 0.05%** | **−0.0054** |
| **full-FT @ 1e-6（其最优）** | **60.87 ± 0.21%** | −0.0016 |
| LoRA-text @ 3e-4 | 51.48 ± 1.08% | **−0.0469**（代价 8.4 点） |
| Adapter-both @ 1e-5 | **0.13%** | +0.411 |
| Adapter-both @ 3e-4 | 23.38% | +0.071 |

**→ 各自调优后 LoRA 与 full-FT 在 zero-shot（−0.18 点，落在 full-FT 自身 seed 波动内）与
ΔCG（−0.004）上**不可区分**。**
**→ 三族对 lr 的响应方向相反**（full-FT 最优在最低端、LoRA 在低端、Adapter 只在 ≥1e-4 可用）
→ **单一共享 lr 不可能对三者公平**。

    python tools\_p304_apply_peft_lr.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

# (文件, 旧, 新, 标签)
PAIRS = [
    # ① 摘要里的 three consequences 之一：加"各自调优后不可区分"的限定
    ("paper合/main_nc.tex",
     r"adaptation position, since removing the visual gradient term removes the dominant "
     r"perturbation source in the regime we swept;",
     r"adaptation position, since removing the visual gradient term removes the dominant "
     r"perturbation source in the regime we swept, though once every method is tuned to its "
     r"own learning rate LoRA and full fine-tuning become indistinguishable;"),
    ("paper合/NC_submission/latex_source/main_nc.tex",
     r"adaptation position, since removing the visual gradient term removes the dominant "
     r"perturbation source in the regime we swept;",
     r"adaptation position, since removing the visual gradient term removes the dominant "
     r"perturbation source in the regime we swept, though once every method is tuned to its "
     r"own learning rate LoRA and full fine-tuning become indistinguishable;"),
    ("paper合/main_springer.tex",
     r"adaptation position, since removing the visual gradient term removes the dominant "
     r"perturbation source in the regime we swept;",
     r"adaptation position, since removing the visual gradient term removes the dominant "
     r"perturbation source in the regime we swept, though once every method is tuned to its "
     r"own learning rate LoRA and full fine-tuning become indistinguishable;"),

    # ② discussion 的 Tenth limitation：换成 task-6 给的版本
    ("paper合/sections/discussion.tex",
     r"Tenth, our full-fine-tuning comparison is made at one shared learning rate rather than "
     r"at each method's optimum.",
     r"Tenth, our cross-method comparison is made at one shared learning rate rather than at "
     r"each method's optimum, and no single rate can be fair to all three families because "
     r"they respond to it in opposite directions: full fine-tuning is optimal at "
     r"$10^{-6}$, LoRA at $10^{-5}$, and the both-position bottleneck Adapter only becomes "
     r"functional from $10^{-4}$ upwards (it collapses to $0.13\%$ zero-shot at $10^{-5}$). "
     r"Tuning each to its own optimum removes the apparent advantage of adapter methods over "
     r"full fine-tuning: LoRA at $10^{-5}$ reaches $60.69\pm0.05\%$ zero-shot at "
     r"$\Delta\mathrm{CG} = -0.0054$, against $60.87\pm0.21\%$ and $-0.0016$ for full "
     r"fine-tuning at $10^{-6}$---a difference of $0.18$ points, inside full fine-tuning's "
     r"own seed spread. The only configuration that clearly narrows the gap is text-only "
     r"LoRA at $3\times10^{-4}$ ($\Delta\mathrm{CG} = -0.047$), and it pays $8.4$ percentage "
     r"points of zero-shot accuracy for that. The practical recommendation therefore "
     r"concerns cost and retrieval rather than alignment: adapter methods are far cheaper "
     r"and far less rate-sensitive, but they do not preserve the gap better than a "
     r"correctly tuned full fine-tune."),
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
        print(f"  {'✅' if n >= 1 else '⚠️ '} {Path(rel).name}: {n}")
        if n == 0:
            continue
        if a.apply:
            bak = p.with_suffix(p.suffix + ".bak_p304")
            if not bak.exists():
                shutil.copy2(p, bak)
            io.open(p, "w", encoding="utf-8", newline="").write(t.replace(old, new))
            total += n
    if not a.apply:
        print("\n  （预演）")
        return 0
    print(f"\n  → 共改 {total} 处")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
