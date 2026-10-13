# -*- coding: utf-8 -*-
r"""修 `discussion.tex` 与正文的三处矛盾（2026-10-13）。

## 我核出的矛盾（`discussion.tex` 未被更新）

| 行 | discussion 仍写 | 正文（已改） |
|---|---|---|
| **L5** | *"the five requirements (R1--R5) constrain the space of admissible statistics to **exactly one**"* + *"Allocation statistics are **not designed, they are forced**"* | **R3 不足以推出唯一性**；需**显式新增 R3′**；给了**反例 $\\|\\nabla E\\|^2$** |
| **L11** | *"The alignment **phase transition** at $r_c\\in[5,6]$ on LLaVA"* | **降级为 "bracketed"**；且**该阈值属协议（blank + 16 样本 + 4-bit）而非模型常数** |
| **L11** | *"the first to show it is **architecture-dependent**"* | 正文已把"架构相关"撤回为**token 预算伪影**（54 token 下 Qwen 的 real 也变负） |
| **L15** | *"Text-only is not an empirical heuristic; it is a **necessary consequence**"* | 与"分配规则未胜随机、AdaLoRA 更优"冲突 ⇒ 需**降级为"与耦合结构一致"** |
| **L23** | 只列 6 条 limitation | 正文有 **12 条**（含 Adapter `up.bias`、画廊噪声、both-vs-vision_only 未决、$\\beta$ 来源、rank-vs-参数记账…） |

**⇒ 这是"改了正文没改讨论"—— 与摘要那次同型。本轮修订的核心结论被判为矛盾。**

    python tools\_p496_fix_discussion_contradictions.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DI = REPO / "paper3" / "paper_ieee" / "sections" / "discussion.tex"

PAIRS = [
    # ① L5：唯一性主张 → 需额外假设
    (
        r"The central contribution is not the exponential allocation formula, but the identification of $\Gamma$ as a \emph{necessary} quantity for any PEFT allocation problem: the five requirements (R1--R5) constrain the space of admissible statistics to exactly one, $\Gamma = \langle \nabla E, u \rangle$. Allocation statistics are not designed, they are forced.",
        r"The central contribution is not the exponential allocation formula, but the identification of $\Gamma$ as a privileged quantity for PEFT allocation: the requirements (R1)--(R5), \emph{together with the additivity assumption (R3$'$) that we state explicitly rather than derive}, single out $\Gamma = \langle \nabla E, u \rangle$ up to positive scaling. It matters that the assumption is explicit, because (R3) alone does not give it---$\|\nabla E\|^2$ is block-decomposable and fails only additivity---so the honest statement is that the allocation problem admits a canonical statistic once one accepts additivity, not that it admits exactly one unconditionally.",
    ),
    # ② L11：phase transition → bracketed + 协议归属 + 撤回"架构相关"
    (
        r"The alignment phase transition at $r_c \in [5,6]$ on LLaVA connects to a growing body of work on LoRA phase transitions (efficiency~\cite{hu2025loralimits}, landscape convexity~\cite{loraconvex2025}). Our finding is the first to identify a phase transition in \emph{cross-modal alignment}, and the first to show it is architecture-dependent---present in LLaVA (MDI $=10.23$) but absent in Qwen-VL (MDI $=33.10$). This architecture-dependence traces to text dominance: higher-rank LoRA provides sufficient capacity for the LLM backbone to develop modality-specific biases, amplifying text-token processing at the expense of visual tokens. The different thresholds suggest that $r_c$ is determined by the interplay between LoRA capacity and the pretrained model's inherent modality balance.",
        r"The crossing we observe on LLaVA sits in $r \in [5,6]$, and it connects to a growing body of work on LoRA phase transitions (efficiency~\cite{hu2025loralimits}, landscape convexity~\cite{loraconvex2025}). Two qualifications matter more than the connection. First, we describe the crossing as bracketed by two ranks rather than as sharp: at $r=5$ the bootstrap interval spans zero, an exact permutation test between $r=5$ and $r=6$ gives $p = 0.100$, and with three seeds the smallest detectable effect exceeds the one observed. Second, the location is a property of the measurement protocol. It appears under blank images at $16$ training samples with 4-bit QLoRA; it does not reappear under real image--text pairs at the scales we could run, and the apparent architecture dependence we had reported did not survive a change of visual budget---at $54$ tokens the decoder's real-image runs also turn negative, so that contrast was an artefact of the token budget rather than of the architecture.",
    ),
    # ③ L15：text-only 的"必然推论" → 降级
    (
        r"Text-only is not an empirical heuristic; it is a necessary consequence of the gradient coupling structure.",
        r"Text-only is therefore \emph{consistent} with the gradient coupling structure rather than derived from it: our own capacity-matched controls show that allocations consistent with that structure are not reliably better than random ones, so we read this as an explanation of an empirical regularity, not as a necessity.",
    ),
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(DI, encoding="utf-8", errors="replace").read()
    total = 0
    for i, (old, new) in enumerate(PAIRS, 1):
        n = t.count(old)
        print(f"  改动 {i}: 命中 {n}（{len(old)} → {len(new)} 字符）")
        if n == 1 and a.apply:
            t = t.replace(old, new)
            total += 1
    if not a.apply:
        print("  （预演）")
        return 0
    if total:
        bak = DI.with_suffix(".tex.bak_p496")
        if not bak.exists():
            shutil.copy2(DI, bak)
        io.open(DI, "w", encoding="utf-8", newline="").write(t)
    t2 = io.open(DI, encoding="utf-8", errors="replace").read()
    checks = {
        "删掉'exactly one'": "to exactly one" not in t2,
        "删掉'not designed, they are forced'": "they are forced" not in t2,
        "含 R3′ 显式假设": "(R3$'$)" in t2,
        "含反例 ‖∇E‖²": "$\\|\\nabla E\\|^2$" in t2,
        "phase transition 改为 bracketed": "bracketed by two ranks" in t2,
        "含协议归属": "property of the measurement protocol" in t2,
        "撤回架构相关": "artefact of the token budget" in t2,
        "text-only 降级为 consistent": "\\emph{consistent} with the gradient coupling" in t2,
        "删掉'necessary consequence'": "necessary consequence of the gradient coupling structure" not in t2,
    }
    ok = True
    for k, v in checks.items():
        print(f"  {'✅' if v else '🔴'} {k}")
        ok = ok and v
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
