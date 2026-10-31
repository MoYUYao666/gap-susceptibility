# -*- coding: utf-8 -*-
r"""Record novelty round (b): lower bound, margin mass, dense sweep, real-checkpoint pairs.

    python tools/_p1304_record_novelty_round_b.py [--apply]
"""
from __future__ import annotations

import argparse
import io
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HANDOFF = REPO / "HANDOFF.md"
MAP = REPO / "文件地图.md"
WHICH = REPO / "哪篇是哪篇.md"
NOVDOC = REPO / "docs" / "A1_NOVELTY_STEP1_2026-10-18.md"

NOVSEC = """

---

## 第 15 步（2026-10-18 22:30）：新颖性 (a) 下界 + (b) margin 质量统计量；证据两处加强，A1 **54 页**

### (a) 下界：一阶矩统计量不可能"充分"

新增 **Proposition（一阶矩统计量的下界）**：设 $A$ 为 margin 满足 $m_i\\le2cL$ 的正确样本集（$L=\\max_c\\|t_c-\\bar t\\|$ 为类散布常数），
则存在**零均值**、范数 $\\le c$ 的图像扰动，使 **CG 完全不变**、而 $A$ 中每一行的 top-1 翻转 ⇒ top-1 至少变化 $|A|/n$。
证明用逐行方向 $u_i=(t_{\\hat y_i}-t_{y_i})/\\|\\cdot\\|$（$A$ 内推 $+c'u_i$ 越过 margin，$A$ 外反向推且只增大 margin），
并用 $\\sum w_i=0$ 保证均值不变。

**量化**：冻结 ImageNet-5k 上 $L=1.013$，margin 低于 $2\\varepsilon$ 的比例为 **0.681**（$\\varepsilon=0.01$）、**0.875**（$\\varepsilon=0.02$）
⇒ 在匹配 gap 族的位移尺度（$\\varepsilon\\approx0.03$）上，**至少 87.5% 的行可被"藏起来"**，即 gap 可被构造为恒等于零而 top-1 崩塌 87.5 点；
实测家族只实现了其中一部分（稀疏 32.7、加密 50.6–62.0），与下界一致。

### (b) 正例：margin 质量 $M(\\varepsilon)$

由 Prop 5（翻转要求 $m_i\\le2\\varepsilon_i$）直接给出可用统计量：$M(\\varepsilon)=n^{-1}\\#\\{i:m_i\\le2\\varepsilon\\}$。
同一批 19 个配置上：**CG 与 top-1 相关 $r=-0.154$**，而 **$M(0.01)$ 为 $r=-0.996$**、$M(0.02)$ 为 $r=-0.988$。
必须按 margin 尺度取 $\\varepsilon$（$\\varepsilon\\ge0.05$ 时饱和），文中按曲线报告。这把论文从"只否证"变成"否证 + 给出替代量"。

### 证据加强 1：五骨干同容差

加密 λ 网格（19 个 λ × 5 个 α × 4 个 σ），$|\\Delta\\mathrm{CG}|\\le0.03$ 下各骨干最大 spread：
**CLIP B/32 50.6**（$\\Delta$CG=0.006）、**B/16 54.4**（0.004）、**OpenCLIP 48.0**（0.029）、**SigLIP 7.7**（0.029；0.05 时 46.0）、**L/14 62.0**（0.009）。
原文稀疏网格的 32.7 是保守值。

### 证据加强 2：真实 checkpoint 匹配对

11 个同时有 CG 与 top-1 的真实微调 checkpoint 中，31 对满足 $|\\Delta\\mathrm{CG}|\\le0.03$；最宽一对
**$\\Delta$CG=0.0024 而 top-1 差 6.64 点**（COCO ep1 60.14% vs DTD ep10 53.50%）；同数据集内最宽 $\\Delta$CG=0.0013、差 **2.24 点**（DTD seed43/44）。
⇒ 不依赖合成扰动的同向证据。

**归档**：`a1_matched_gap_dense.json`、`a1_real_checkpoint_pairs.json`、`a1_lower_bound_constants.json`、`a1_margin_mass.json`；
**脚本** `_p1299`–`_p1304`。A1 **54 页**、0/0/0；**A1 claim ledger 112/112**；审计 `a1_paa` READY/A。
"""

ENT = """> **🧭 2026-10-18 22:30 —— 新颖性 (a) 下界 + (b) margin 质量统计量落地；五骨干加密、真实 checkpoint 匹配对，A1 **54 页**，台账 **112/112**
>
> **(a) 下界（Proposition）**：margin 满足 $m_i\\le2cL$ 的正确样本集，必存在**零均值**扰动使 **CG 完全不变**而 top-1 至少变化 $|A|/n$；
> 冻结模型上 $L=1.013$、margin 比例 0.681（$\\varepsilon$=0.01）/0.875（0.02）⇒ 在匹配 gap 尺度上 **≥87.5% 的行可被藏起来**，
> 实测 32.7–62.0 点落在下界之内。
> **(b) 正例**：margin 质量 $M(\\varepsilon)$ —— 同批配置 **CG 相关 −0.154**，**$M(0.01)$ 相关 −0.996**、$M(0.02)$ −0.988。
> 论文因此从"只否证"变为"否证 + 给出替代量"。
>
> **证据加强**：① 加密网格五骨干同容差（$|\\Delta CG|\\le0.03$）：**50.6 / 54.4 / 48.0 / 7.7 / 62.0**（稀疏网格 32.7 为保守值）；
> ② **真实 checkpoint 匹配对**：31 对满足 $|\\Delta CG|\\le0.03$，最宽 **6.64 点 @ $\\Delta$CG=0.0024**（同数据集 2.24 点 @ 0.0013）。
> A1 **54 页**、0/0/0；三台账 **112/112、96/96、76/76**；审计 **READY grade A：pass=61 fail=0 warn=0**。
>

"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not a.apply:
        print("  (dry run)")
        return 0
    n = io.open(NOVDOC, encoding="utf-8").read()
    if "第 15 步" not in n:
        io.open(NOVDOC, "w", encoding="utf-8", newline="").write(n.rstrip("\n") + NOVSEC)
        print("  novelty doc appended")
    h = io.open(HANDOFF, encoding="utf-8").read()
    if "新颖性 (a) 下界 + (b) margin" not in h:
        i = h.find("# 项目交接文档")
        j = h.find("\n", i)
        io.open(HANDOFF, "w", encoding="utf-8", newline="").write(h[: j + 1] + "\n" + ENT.replace("\\n", "\n") + h[j + 1:])
        print("  handoff added")
    w = io.open(WHICH, encoding="utf-8").read()
    old = "五骨干匹配 gap + 排版修正** | 53 + 1 title page |"
    new = "五骨干匹配 gap + 下界 + margin 质量** | 54 + 1 title page |"
    print(f"  which row: {w.count(old)}")
    if w.count(old) == 1:
        io.open(WHICH, "w", encoding="utf-8", newline="").write(w.replace(old, new, 1))
    m = io.open(MAP, encoding="utf-8").read()
    row = ("92. 🧭 **新颖性 (a) 下界 + (b) margin 质量（2026-10-18 22:30）** —— Prop：零均值扰动可保持 CG 不变而翻转 "
           "margin≤2cL 的行（≥87.5% 可藏）；$M(0.01)$ 与 top-1 相关 **−0.996**（CG 仅 −0.154）；加密网格五骨干 spread "
           "**50.6/54.4/48.0/7.7/62.0**；真实 checkpoint 匹配对 **6.64 点 @ ΔCG=0.0024**。A1 **54 页**、台账 **112/112**、审计 READY/A。\\n")
    if "新颖性 (a) 下界 + (b) margin" not in m:
        anchor = "91. 👁️ **A1 全页目视检查"
        idx = m.find(anchor)
        if idx >= 0:
            end = m.find("\n", idx)
            io.open(MAP, "w", encoding="utf-8", newline="").write(m[: end + 1] + row + m[end + 1:])
            print("  map row added")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
