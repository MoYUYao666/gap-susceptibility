# -*- coding: utf-8 -*-
r"""按 task-5（PR R1.6）改写全量微调的表述（2026-10-12）。

## 原句

> *"Full fine-tuning increases CG by 24\% and collapses zero-shot accuracy to near-chance
> levels (mean $2.6\%$ over 3 retrained seeds), while text-only LoRA …"*

## task-5 查实（`docs/PR_FAIRNESS_FIX.md` §5）

**这句话把两次不同的运行拼在了一起**：

| 数字 | 实际出处 | 那次运行的真实状态 |
|---|---|---|
| **+24%** | `outputs/imagenet_zs/full_ft/results.json`（CG 0.8185→1.0072 = **+0.1887 = +23.1%**；同值见 `master_results.json::cg_delta 0.188708`） | **没崩**：`final_val_loss = 0.5323`、`final_task_metrics.R@1 = 0.6470` |
| **2.6%** | `outputs/imagenet_zs_rerun/full_ft*`（2026-08 重跑，lr=1e-4） | **发散**：val loss 7.88、R@1 0.002、zero-shot 0.13/4.12/3.39% |

**且**：原始运行的 `R@1 = 0.647` **超过该指标理论上限**（每图 5 条 caption，对角口径上限 = 1/5 = 0.2）
→ 它用的是**另一套评测协议**；原始运行**未记录 lr，脚本已丢失** → 无法精确重建。

**新扫描（9 run，5 个 lr）**：

| lr | n | zero-shot top-1 | ΔCG | 崩塌 |
|---|---|---|---|---|
| **1e-6** | 3 | **60.87 ± 0.21%** | **−0.0016 ± 0.0052** | 0/3 |
| 1e-5 | 3 | 52.18 ± 1.03% | +0.1860 ± 0.0047 | 0/3 |
| 3e-5 | 1 | 31.44% | +0.2498 | 0/1 |
| 1e-4 | 1 | 0.14% | +0.7969 | 1/1 |
| 3e-4 | 1 | 0.08% | +0.8001 | 1/1 |

→ **损伤随 lr 在三个数量级上单调**；**在最优 lr（1e-6）下"全量微调破坏对齐"不成立**。

    python tools\_p283_fix_fullft_claim.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

OLD = (r"Full fine-tuning increases CG by 24\% and collapses zero-shot accuracy to "
       r"near-chance levels (mean $2.6\%$ over 3 retrained seeds), while text-only LoRA")

NEW = (r"Full fine-tuning is far more learning-rate sensitive than the adapter methods, and "
       r"at the rate we had been using for every method it fails outright: at $\mathrm{lr}="
       r"10^{-4}$ it collapses zero-shot accuracy to near-chance (mean $2.6\%$ over three "
       r"reruns) and inflates the Centroid Gap by $+0.80$. Sweeping the rate shows that this "
       r"is a property of the shared rate rather than of full fine-tuning: over "
       r"$\mathrm{lr}\in\{10^{-6},\dots,3\times10^{-4}\}$ the damage is monotone, with "
       r"zero-shot accuracy falling from $60.9\pm0.2\%$ at $10^{-6}$ to $0.1\%$ at "
       r"$10^{-4}$, and $\Delta\mathrm{CG}$ going from $-0.002\pm0.005$ to $+0.80$. At "
       r"$10^{-6}$ full fine-tuning is therefore indistinguishable from the frozen model in "
       r"alignment, slightly better in zero-shot accuracy, and better in-domain "
       r"($R@1 = 0.181$ against $0.156$ frozen), while text-only LoRA")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    import glob
    files = sorted(glob.glob(str(REPO / "paper合" / "sections" / "*.tex"))) + \
        sorted(glob.glob(str(REPO / "paper合" / "main*.tex")))
    hit = 0
    for f in files:
        t = io.open(f, encoding="utf-8", errors="replace").read()
        n = t.count(OLD)
        if not n:
            continue
        print(f"  {Path(f).name}: 命中 {n}")
        hit += n
        if not a.apply:
            continue
        bak = Path(f).with_suffix(Path(f).suffix + ".bak_p283")
        if not bak.exists():
            shutil.copy2(f, bak)
        io.open(f, "w", encoding="utf-8", newline="").write(t.replace(OLD, NEW))
    if not a.apply:
        print("  （预演）")
        return 0
    print(f"\n  → 共改 {hit} 处")
    left = 0
    for f in files:
        t = io.open(f, encoding="utf-8", errors="replace").read()
        left += t.count("increases CG by 24")
    print(f"  残留 'increases CG by 24': {left}（应 0）")
    return 0 if left == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
