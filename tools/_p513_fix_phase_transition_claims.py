# -*- coding: utf-8 -*-
r"""修 `Alignment Phase Transition` 节内的旧主张 + 压缩（2026-10-13）。

## 与已修订结论冲突的三处（我的扫描器没抓到 —— 特征串不同）

| 位置 | 旧主张 | 冲突对象 |
|---|---|---|
| **L113-136** | *"LLaVA exhibits a **sharp phase transition** at $r_c\in[5,6]$"* + *"**establishing** $r_c\in[5,6]$ as a **statistically supported** transition"* | 同节 L529-530 已改为 *"bracketed … **not a sharply localised one**"* |
| **L167-169** | *"This **explains** why the transition appears in LLaVA but not Qwen-VL: **architectural differences** … determine the critical threshold"* | Finding 2（L149-160）已撤回架构依赖（**54 token 下 Qwen 的 real 也转负**） |
| **L76-80** | 图注 *"critical rank $r_c \in [5, 6]$ where $\Delta E$ flips sign"* | 同上 |

**⇒ 扫描器漏抓的原因**：我用的特征串是 `sharp alignment phase transition` / `phase transition at`，
**这两处用的是 `sharp phase transition` / `appears in LLaVA but not`** ⇒ **判据不全。**
**已把新特征串补进 `_p497`。**

    python tools\_p513_fix_phase_transition_claims.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
EX = REPO / "paper3" / "paper_ieee" / "sections" / "experiments.tex"
SCAN = REPO / "tools" / "_p497_scan_contradictions.py"

# ① Finding 1：sharp + statistically supported → bracketed
F1_START = "\\textbf{Finding 1: Critical rank threshold.}"
F1_END = "rather than a three-seed fluctuation."

F1_NEW = (
    r"\textbf{Finding 1: the crossing, and how far we can localise it.} On LLaVA the sign of"
    "\n"
    r"$\Delta E$ changes between $r=5$ and $r=6$: below it alignment improves, above it is"
    "\n"
    r"damaged, and at $r \geq 24$ the evaluation-time energy becomes non-finite. We describe"
    "\n"
    r"this as a crossing bracketed by two ranks rather than as a sharp transition, and the"
    "\n"
    r"distinction is quantitative. At $r=5$ the energy is indistinguishable from zero on both"
    "\n"
    r"datasets (LLaVA $-21$, $95\%$ CI $[-101,+59]$, $p=0.37$; ShareGPT $+2.7$, CI $[-93,+99]$,"
    "\n"
    r"$p=0.92$), so the interval spans both signs---the signature of a boundary, but not of a"
    "\n"
    r"localised one. The rise across the crossing is real on ShareGPT (Welch $t=4.81$,"
    "\n"
    r"$p=0.011$) and on pooled LLaVA ranks (pooled $r \in \{4,5\}$ at $-63 \pm 53$ against"
    "\n"
    r"$r \in \{6,7\}$ at $+127 \pm 85$, $n=6$ each, $t=4.65$, $p=0.0014$), and the ordering"
    "\n"
    r"$\Delta E(r{=}6) > \Delta E(r{=}5)$ holds in all six independent configurations we ran"
    "\n"
    r"($p = 2^{-5} \approx 0.031$ under random signs). What we cannot do is place $r_c$ on a"
    "\n"
    r"rank. With three seeds the smallest effect we could detect exceeds the one we observe,"
    "\n"
    r"and an exact permutation test between $r=5$ and $r=6$ gives $p = 0.100$; the crossing is"
    "\n"
    r"therefore bracketed, and its location is a property of the measurement protocol rather"
    "\n"
    r"than a constant of the model."
)

# ② Finding 3：架构依赖 → token 预算
F3_START = "\\textbf{Finding 3: Mechanism -- text dominance.}"
F3_END = "architectural differences in cross-modal\nattention balancing determine the critical threshold."

F3_NEW = (
    r"\textbf{Finding 3: a mechanism we can state only as a hypothesis.} A natural account of"
    "\n"
    r"the crossing is the LLM backbone's dual role in decoder-based VLMs: low-rank adapters"
    "\n"
    r"lack the capacity to develop modality-specific biases, while high-rank adapters amplify"
    "\n"
    r"language-token processing at the expense of visual"
    "\n"
    r"tokens~\cite{wu2025language}, flipping the sign of $\Gamma_k$. The account predicts that"
    "\n"
    r"the crossing point should track the model's modality balance, and we were unable to"
    "\n"
    r"confirm that prediction: the apparent difference between the two models tracked the"
    "\n"
    r"visual token budget rather than the architecture (Finding~2). We therefore state the"
    "\n"
    r"mechanism as a hypothesis consistent with the data rather than as the explanation of it."
)

# ③ 图注
CAP_OLD = ("LLaVA exhibits a critical rank $r_c \\in [5, 6]$ where $\\Delta E$ flips sign from\n"
           "alignment-improving to alignment-damaging, followed by representation collapse")
CAP_NEW = ("On LLaVA the sign of $\\Delta E$ changes between $r=5$ and $r=6$---a crossing\n"
           "bracketed by those two ranks rather than a sharp threshold---followed by collapse")

# ④ 扫描器判据补充
SCAN_ADD = ('''    ("phase transition 应降级", [r"phase transition at", r"sharp phase transition"]),''',
            '''    ("phase transition 应降级", [r"phase transition at", r"sharp phase transition",
                                r"sharp phase transition", r"\\bsharp phase\\b",
                                r"statistically supported\\\\s+transition",
                                r"appears in LLaVA but not"]),''')


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(EX, encoding="utf-8", errors="replace").read()
    items = []
    for start, end, new, label in ((F1_START, F1_END, F1_NEW, "Finding 1"),
                                   (F3_START, F3_END, F3_NEW, "Finding 3")):
        i = t.find(start)
        j = t.find(end, i) if i >= 0 else -1
        print(f"  {label}: 锚点 i={i}, j={j}")
        if i >= 0 and j >= 0:
            items.append((i, j + len(end), new, label))
    n_cap = t.count(CAP_OLD)
    print(f"  图注锚点命中 {n_cap}")
    if len(items) != 2 or n_cap != 1:
        print("  🔴 锚点不全")
        return 1
    if not a.apply:
        print("  （预演）")
        return 0
    bak = EX.with_suffix(".tex.bak_p513")
    if not bak.exists():
        shutil.copy2(EX, bak)
    for i, e, new, label in sorted(items, reverse=True):
        print(f"  {label}: {e - i:,} → {len(new):,} 字符")
        t = t[:i] + new + t[e:]
    t = t.replace(CAP_OLD, CAP_NEW)
    io.open(EX, "w", encoding="utf-8", newline="").write(t)

    # 扫描器判据补充
    s = io.open(SCAN, encoding="utf-8", errors="replace").read()
    if SCAN_ADD[1] not in s:
        if SCAN_ADD[0] in s:
            io.open(SCAN, "w", encoding="utf-8", newline="").write(s.replace(*SCAN_ADD))
            print("  ✅ 扫描判据已补（sharp phase / statistically supported transition / appears in LLaVA but not）")
        else:
            print("  ⚠️ 扫描判据锚点未命中")
    else:
        print("  扫描判据已含")

    t2 = io.open(EX, encoding="utf-8", errors="replace").read()
    checks = {
        "无'sharp phase transition'": "sharp phase\ntransition" not in t2 and "sharp phase transition" not in t2,
        "无'statistically supported'": "statistically supported" not in t2,
        "无'appears in LLaVA but not'": "appears in LLaVA but not" not in t2,
        "含'bracketed'": "bracketed by two ranks" in t2,
        "含置换 p=0.100": "$p = 0.100$" in t2,
        "含 MDE 表述": "smallest effect we could detect exceeds" in t2,
        "机制降级为 hypothesis": "only as a hypothesis" in t2,
        "图注已改": "bracketed by those two ranks rather than a sharp threshold" in t2,
        "字符数下降": len(t2) < len(io.open(bak, encoding="utf-8", errors="replace").read()),
    }
    ok = True
    for k, v in checks.items():
        print(f"  {'✅' if v else '🔴'} {k}")
        ok = ok and v
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
