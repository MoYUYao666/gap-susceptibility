# -*- coding: utf-8 -*-
r"""把 SigLIP 严格冻结对照的新结果写进正文（2026-10-02）。

## 新实验结果（5 seeds，配对，同预算同协议）

`outputs/siglip_strict/`（本次运行，可重跑 `tools/_run_siglip_strict.py`；统计见
`tools/_siglip_strict_stats.py`）：

| 臂 | 可训参数 | ΔCG（5 seeds） | 均值 ± sd | R@1 |
|---|---|---|---|---|
| text_only | 294,912（视觉侧可训 **0**） | +0.0565 +0.0678 +0.0719 +0.0661 +0.0698 | **+0.0664 ± 0.0060** | 0.432 |
| both | 589,824 | −0.0180 −0.0125 −0.0020 −0.0136 −0.0108 | **−0.0114 ± 0.0059** | **0.619** |

配对差 −0.0778（sd 0.0033），**配对 t = −52.7**，方向 5/5 一致（text_only 全正、both 全负）。

## 与 CLIP 严格冻结对照（`outputs/strict_freeze/`）

| 架构 | text_only | both | 方向 |
|---|---|---|---|
| **CLIP**（InfoNCE） | **−0.0465** ± 0.0030 | −0.0258 ± 0.0035 | **text_only 更优** |
| **SigLIP**（sigmoid） | +0.0664 ± 0.0060 | **−0.0114** ± 0.0059 | **both 更优** ← 相反 |

**结论：text-only 的"位置优势"是架构依赖的，不是普适默认。**

## 顺带得出的第二点

两架构下 **both 的检索都更强**（CLIP 0.6932 vs 0.6238；SigLIP 0.619 vs 0.432）
→ **"降间隙"与"提检索"是两个不同目标**，与正文既有表述一致，且现在有跨架构证据。

## ⚠️ 诚实标注的边界

- **CLIP 严格冻结是 3 epochs**（`outputs/strict_freeze/`：`epochs: 10` 字段但训练步数对应短协议），
  而 **SigLIP 本次是 10 epochs / 5000 样本** → **两架构的对照不是同预算**，
  故"方向相反"是**观察到的现象**，其"是否由损失函数形状导致"**属推测，本轮未检验**。
- 归档 SigLIP run（legacy 约定）**未记录训练预算**，且 gap_history 只有 4 点（本次 7 点）
  → **归档值与本次值不可直接相减**。

    python tools\_pa_write_siglip_result.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
S = REPO / "paper合" / "sections"

EDITS: list[tuple[str, str, str, str]] = [
    # ① 设计模式第 (1) 条：去掉"跨架构普适"的声称
    ("empirical.tex",
     "(1) \\textbf{Text-only is the safest default}---across architectures, methods, and datasets, "
     "training only the text encoder minimizes alignment degradation;",
     "(1) \\textbf{Adaptation position dominates, but its direction is architecture-dependent}---for the "
     "InfoNCE-based encoders studied here, training only the text encoder minimises alignment "
     "degradation, whereas the strict-freezing control on SigLIP reverses that ordering "
     "(Section~\\ref{sec:validation});",
     "design pattern (1)：去掉跨架构普适声称"),
    # ② validation 段：写入已核实的 SigLIP 严格冻结结果
    ("validation.tex",
     "The gap-level predictions of the framework extend to additional architectures and PEFT methods "
     "measured in Section~\\ref{sec:empirical}: on SigLIP the text-only arm changes CG by $+0.067$ against "
     "$+0.058$ for the both-position arm, and on Adapter the corresponding figures are $+0.064$ and "
     "$+0.058$ at $d{=}64$. Both sets of runs come from the earlier adaptation convention, in which the "
     "LoRA backbone was not frozen: the SigLIP text-only arm trained $1.89\\times10^{8}$ parameters "
     "against $1.75\\times10^{8}$ for the both-position arm, so as with the CLIP comparison in "
     "Section~\\ref{sec:empirical} these two arms do not isolate a choice about which encoder to touch. "
     "Their gap values remain reported because they are measured, but they carry no claim about the "
     "text-only advantage for those architectures; establishing that on SigLIP requires the strict-freezing "
     "control used for CLIP.",
     "The gap-level predictions of the framework extend to additional architectures and PEFT methods. "
     "Under the CLIP strict-freezing control of Section~\\ref{sec:empirical}, the text-only arm reduces the "
     "gap by more than the both-position arm ($-0.046 \\pm 0.003$ against $-0.026 \\pm 0.004$ over five "
     "seeds). We repeated that control on SigLIP, an architecture whose pairwise sigmoid objective differs "
     "from CLIP's InfoNCE, using identical budgets for both arms and five seeds each "
     "($294{,}912$ trainable parameters for text-only, with the vision side registering zero, against "
     "$589{,}824$ for both-position). \\textbf{The ordering reverses}: text-only \\emph{increases} the gap "
     "($+0.066 \\pm 0.006$) whereas both-position \\emph{reduces} it ($-0.011 \\pm 0.006$), a paired "
     "difference of $-0.078$ ($t = -52.7$, consistent in sign across all five seeds). The both-position arm "
     "also retrieves far better ($R@1 = 0.62$ against $0.43$). Two consequences follow. First, the "
     "text-only advantage is a property of the architecture rather than a universal default, so it should "
     "not be transferred to a new encoder without this control. Second, the two objectives come apart: "
     "both-position retrieves better on \\emph{both} architectures ($0.69$ against $0.62$ on CLIP) even "
     "though it reduces the gap more on only one of them, so minimising centroid or distribution gap is "
     "not a proxy for retrieval quality. We note that the CLIP and SigLIP controls were run at different "
     "epoch budgets, so the reversal is an observation rather than an established consequence of the loss "
     "function; the earlier non-frozen SigLIP runs are not used as evidence here, since they trained "
     "$1.89\\times10^{8}$ and $1.75\\times10^{8}$ parameters respectively and therefore did not isolate "
     "the adaptation site.",
     "validation：写入已核实的 SigLIP 严格冻结反例"),
]


def main() -> int:
    apply = "--apply" in sys.argv
    n = 0
    for fname, old, new, why in EDITS:
        p = S / fname
        t = io.open(p, encoding="utf-8").read()
        c = t.count(old)
        if c == 1:
            print(f"  ✅ {fname}: {why}")
            if apply:
                io.open(p, "w", encoding="utf-8", newline="").write(t.replace(old, new, 1))
            n += 1
        elif c == 0:
            print(f"  ⚠ {fname}: 未命中（{why}）")
        else:
            print(f"  ⚠ {fname}: 命中 {c} 次，拒绝改动（{why}）")
    print(f"\n{n}/{len(EDITS)} 处{'已改' if apply else '可改'}")
    if apply:
        bad = []
        for f in S.glob("*.tex"):
            tt = io.open(f, encoding="utf-8").read()
            if "across architectures, methods, and datasets" in tt:
                bad.append(f.name)
        assert not bad, f"仍含普适声称：{bad}"
        print("✅ 断言通过：跨架构普适声称已消除")
        assert "reverses" in io.open(S / "validation.tex", encoding="utf-8").read()
        print("✅ 断言通过：SigLIP 反例已写入")
    else:
        print("（预演，加 --apply 生效）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
