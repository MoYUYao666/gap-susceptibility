# -*- coding: utf-8 -*-
r"""修两处：① 零样本的绝对否定（与附录 D 矛盾）② 我在 `_p425` 引入的不准确措辞（2026-10-12）。

## ① 绝对否定与附录直接冲突（我已逐字核实三处）

- `experiments.tex:31-33`：*"**No Γ measurement, gradient alignment, or calibration is
  performed on LLaVA or Qwen-VL before training**; all predictions derive from the CLIP
  structural law"* ← **绝对否定**
- `appendix.tex:59`：*"We **illustrate the Γ-based allocation pipeline on LLaVA-1.5-7B** …"*
  ← **就在目标上算 Γ**（`compute_gamma_llava.py`）
- `experiments.tex:135`（Finding 4）：**自己给出 Qwen2-VL 的逐块 Γ 数值**
  （vis $-3.7\times10^8$、merger $-2.1\times10^4$、shallow $-9.0\times10^2$、mid $-2.1\times10^3$、deep $-7.2\times10^3$）

⇒ **"no Γ measurement on the target" 被稿件自己否证。** 修法：把绝对否定收窄为
**"分配决策不含目标模型梯度"**，并**明说附录的 Γ 属事后诊断**。

## ② 我在 `_p425` 引入的不准确（第 16 个错）

我写了 *"A **capacity-matched** random control … is reported in the revised version"*。
**但 Theory 组内部本身就跨容量**——`experiments.tex:343` 自己写着
*"all $|\Gamma_k|$ grow monotonically with rank (**$16$–$26\times$** from $r=4$ to $r=64$)"*，
说明稿件**另有**一组 r=4…64 的扫描。⇒ **"同容量 random 对照"不能解决整个问题**，
**不能这样承诺**。改为**如实说两个层面**：
(i) 三组容量不等（16×）；(ii) 稿件内部另有跨容量的 rank 扫描 →
**"分配 vs 容量"的解耦需要在两个层面都做**，**尚未做**。

    python tools\_p427_fix_zeroshot_and_promise.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
EX = REPO / "paper3" / "paper_ieee" / "sections" / "experiments.tex"

# ---------- ① 零样本绝对否定 ----------
ZS_OLD = (
    "\\textbf{Zero-shot constraint.} No $\\Gamma$ measurement, gradient alignment, or\n"
    "calibration is performed on LLaVA or Qwen-VL before training; all predictions\n"
    "derive from the CLIP structural law~\\cite{wan2026gap}.")
ZS_NEW = (
    "\\textbf{Zero-shot constraint.} No target-model gradient enters an allocation\n"
    "\\emph{decision}: every rank we assign is derived from the CLIP structural\n"
    "law~\\cite{wan2026gap} and from quantities computable before training the target.\n"
    "We do compute $\\Gamma_k$ on the target models, but only \\emph{after} the fact and\n"
    "only for diagnosis---to check whether the ordering the CLIP law predicts is the\n"
    "ordering the target exhibits (Appendix~D). Those measurements are never used to\n"
    "choose an allocation, which is why the predictions can be evaluated on LLaVA and\n"
    "Qwen2-VL without the circularity that a gradient-informed decision would imply.")

# ---------- ② 我引入的不准确承诺 ----------
PROM_OLD = (
    "A capacity-matched random control---drawing only from the integer\n"
    "allocations that satisfy $\\sum_k c_k\\,\\mathrm{rank}_k = 7{,}237{,}632$\n"
    "exactly---is reported in the revised version, and it is that control, not the\n"
    "original Random group, that isolates the allocation variable.")
PROM_NEW = (
    "Decoupling allocation from capacity therefore has to be done at two levels, and we\n"
    "report both in the revised version: a Random group drawn only from the integer\n"
    "allocations that satisfy $\\sum_k c_k\\,\\mathrm{rank}_k = 7{,}237{,}632$ exactly,\n"
    "which holds the parameter count fixed across arms; and a rank sweep at matched\n"
    "allocation, which holds the allocation fixed while rank---and hence capacity---\n"
    "varies, isolating the effect that the $16$--$26\\times$ growth of $|\\Gamma_k|$\n"
    "across $r \\in [4,64]$ (Section~IV-D) would otherwise confound.")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(EX, encoding="utf-8", errors="replace").read()
    total = 0
    for old, new, label in ((ZS_OLD, ZS_NEW, "零样本绝对否定"),
                            (PROM_OLD, PROM_NEW, "capacity-matched 承诺")):
        n = t.count(old)
        print(f"  {'✅' if n == 1 else '⚠️ '} {label} 命中 {n}")
        if n == 1:
            t = t.replace(old, new)
            total += 1
    if not a.apply:
        print("  （预演）")
        return 0
    bak = EX.with_suffix(".tex.bak_p427")
    if not bak.exists():
        shutil.copy2(EX, bak)
    io.open(EX, "w", encoding="utf-8", newline="").write(t)
    print(f"\n  → 共改 {total} 处")
    t2 = io.open(EX, encoding="utf-8", errors="replace").read()
    checks = {
        "已删除 'No Γ measurement ... is performed'": "No $\\Gamma$ measurement, gradient alignment" not in t2,
        "改为 'No target-model gradient enters an allocation decision'":
            "No target-model gradient enters an allocation" in t2,
        "声明附录 Γ 是事后诊断": "only \\emph{after} the fact" in t2,
        "不再承诺单一 capacity-matched 对照": "A capacity-matched random control" not in t2,
        "改为两个层面解耦": "at two levels" in t2 and "Rank sweep at matched" not in t2,
        "含 16--26× 的容量混淆": "$16$--$26\\times$" in t2,
    }
    ok = True
    for k, v in checks.items():
        print(f"  {'✅' if v else '🔴'} {k}")
        ok = ok and v
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
