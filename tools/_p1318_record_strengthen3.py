# -*- coding: utf-8 -*-
r"""Record strengthening round 3 (items 1-4): Williams tests, theorem assumptions, retrieval analogue, selection rule.

    python tools/_p1318_record_strengthen3.py [--apply]
"""
from __future__ import annotations

import argparse
import io
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HANDOFF = REPO / "HANDOFF.md"
MAP = REPO / "文件地图.md"
WHICH = REPO / "哪篇是哪篇.md"
AUTO = REPO / "AUTOMATION_HANDOVER.md"
NOVDOC = REPO / "docs" / "A1_NOVELTY_STEP1_2026-10-18.md"

NOVSEC = """

---

## 第 17 步（2026-10-19 00:20）：四项强化落地，A1 **58 页**，台账 **139/139**

| 项 | 内容 | 归档 |
|---|---|---|
| **1. 相关差异显著性（Williams 检验）** | 两统计量与同一精度向量相关 ⇒ 依赖样本；分类：CG vs $M(0.01)$ $t=7.2$（$p=4.7\\times10^{-6}$）、$\\tau$ vs $M$ $t=14.7$（$p=6.6\\times10^{-10}$）；检索：$t=6.1$（$2.6\\times10^{-5}$）、$t=7.5$（$2.8\\times10^{-6}$）。CG vs $\\tau$ 在分类显著（$t=-5.5$，$p=7.2\\times10^{-5}$），**在检索不显著（$t=-0.3$，$p=0.75$）**——与两者在检索上都弱一致 | `a1_williams_tests.json` |
| **2. Theorem 1 的假设说明** | 明确三点：精确陈述用未归一化算式（归一化下平移只差二阶项，故实测族确实会改变精度）；零均值构造要求至少一个 $A$ 外行与足够维度（$A$ 为全集时改用逐行幅度）；$L$ 由模型自身文本嵌入**实测**（CLIP B/32：$L=1.013$），非假设 | 正文 Remark |
| **3. retrieval 版下界** | 新 Proposition：配对 margin $m_i=s_i(i)-\\max_{j\\ne i}s_i(j)$、配对质量 $M_R(\\varepsilon)$；同一构造使 CG 不变而 R@1 变化 $M_R(cL)$。536 对冻结集上 $M_R(0.01)=0.578$、$M_R(0.02)=0.723$，与 R@1 相关 $-0.970$ | 正文 §retrieval |
| **4. $M(\\varepsilon)$ 作为选择规则** | 合成 17 配置：按 **min $M(0.01)$ 选择 = 精确命中 oracle（regret 0）**，而按 min CG 选择亏 **44.4 点**；10 模板 × 5 骨干：候选间精度差 ≤2 点，min-M 与默认模板 regret 都在 1.7 点内（CLIP B/32：1.7 vs 1.0），骨干内 Spearman($M$,top-1) −0.58…−0.94 | `a1_selection_rule.json` |

**顺带修复**：p 值曾被格式化成 "0.0"（一位小数），已改为科学计数法；A1 台账的比较改为**容差式**（避免 2.6e-05 这类浮点在
小数舍入下误判），并新增 20 条断言 → **139/139**。

A1 **58 页**、0/0/0；三台账 139/139、96/96、76/76；审计 `a1_paa` READY/A。
"""

ENT = """> **➕ 2026-10-19 00:20 —— 四项强化：Williams 检验、定理假设说明、retrieval 版下界、$M(\\varepsilon)$ 作为选择规则（A1 **58 页**，台账 **139/139**）
>
> 1. **Williams 检验**：分类 CG vs $M$ $t=7.2$、$\\tau$ vs $M$ $t=14.7$（p<10⁻⁵）；检索 $t=6.1$、$t=7.5$；
>    **CG vs $\\tau$ 在检索不显著（p=0.75）**——两者检索上都弱，与对决表一致。
> 2. **定理假设**：未归一化/归一化差异、零均值构造的存在条件、$L$ 实测（1.013）三点写明。
> 3. **retrieval 版命题**：配对 margin 与 $M_R(\\varepsilon)$，$M_R(0.01)=0.578$，与 R@1 相关 −0.970。
> 4. **选择规则**：合成配置上 **min $M$ = oracle（regret 0）**、min CG 亏 **44.4 点**；模板选择上候选几乎等价，min-M 与默认差 ≤1.7 点。
>
> 顺带修：p 值格式化（曾显示 0.0）与台账浮点比较（改为容差式），新增 20 条断言 → **139/139**。
> A1 **58 页**、0/0/0；三台账 139/96/76 全过；审计 **READY grade A：pass=61 fail=0 warn=0**。
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
    if "第 17 步" not in n:
        io.open(NOVDOC, "w", encoding="utf-8", newline="").write(n.rstrip("\n") + NOVSEC)
        print("  novelty doc appended")
    h = io.open(HANDOFF, encoding="utf-8").read()
    if "四项强化：Williams 检验" not in h:
        i = h.find("# 项目交接文档")
        j = h.find("\n", i)
        io.open(HANDOFF, "w", encoding="utf-8", newline="").write(h[: j + 1] + "\n" + ENT.replace("\\n", "\n") + h[j + 1:])
        print("  handoff added")
    w = io.open(WHICH, encoding="utf-8").read()
    old = "主定理 + 对决表** | 56 + 1 title page |"
    new = "主定理 + 对决表 + 选择规则** | 58 + 1 title page |"
    print(f"  which row: {w.count(old)}")
    if w.count(old) == 1:
        io.open(WHICH, "w", encoding="utf-8", newline="").write(w.replace(old, new, 1))
    au = io.open(AUTO, encoding="utf-8").read()
    au2 = au.replace("（**56 页** + 1 页 title page + 揭示函 + 图摘要）", "（**58 页** + 1 页 title page + 揭示函 + 图摘要）")
    au2 = au2.replace("**A1 claim ledger 127/127**", "**A1 claim ledger 139/139**")
    if au2 != au:
        io.open(AUTO, "w", encoding="utf-8", newline="").write(au2)
        print("  automation updated")
    m = io.open(MAP, encoding="utf-8").read()
    row = ("95. ➕ **四项强化（2026-10-19 00:20）** —— Williams 检验（分类 t=7.2/14.7，检索 t=6.1/7.5；CG vs τ 检索 p=0.75 不显著）；"
           "定理假设说明（归一化差异/构造条件/L=1.013 实测）；**retrieval 版命题**（$M_R(0.01)=0.578$，r=−0.970）；"
           "**选择规则**（合成配置 min-M=oracle，min-CG 亏 44.4 点；模板上近乎等价）。A1 **58 页**、台账 **139/139**、审计 READY/A。\\n")
    if "四项强化（2026-10-19" not in m:
        anchor = "94. 🏁 **最后一轮提升"
        idx = m.find(anchor)
        if idx >= 0:
            end = m.find("\n", idx)
            io.open(MAP, "w", encoding="utf-8", newline="").write(m[: end + 1] + row + m[end + 1:])
            print("  map row added")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
