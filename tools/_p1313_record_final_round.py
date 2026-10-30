# -*- coding: utf-8 -*-
r"""Record the final round: characterization theorem, statistic showdown, robustness appendix, abstract rewrite.

E (trimming the body to 45-48 pages) is deferred by decision: the body is 56 pages in total including the appendix, the
venue has no page limit, and every candidate move (two more tables into the appendix) would not change the total.

    python tools/_p1313_record_final_round.py [--apply]
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

## 第 16 步（2026-10-18 23:30）：最后一轮全面提升 —— 主定理 + 统计量对决 + 稳健性 + 摘要重写，A1 **56 页**

### A. 一条主定理（Theorem 1，特征化）

| 部分 | 内容 | 出处 |
|---|---|---|
| (i) | top-1 只依赖行序；**任何只依赖两嵌入均值的统计量**对文本侧公共平移不变 ⇒ 不可能充分 | Prop 1 + Prop 3 |
| (ii) | 干涉的类内散布 $\\le\\varepsilon$ 时，仅 $m_i\\le2\\varepsilon$ 的行可翻转；**可翻转比例 = margin 质量 $M(\\varepsilon)$** | Prop 4（margin 条件）|
| (iii) | 下界可达：存在**零均值**扰动使 CG 完全不变、top-1 变化 $M(cL)$ | Prop 5（下界）|

⇒ 一句话结论：**一阶矩只对"类中性"干涉有效；一般情形下的正确证书是 margin 质量，不是矩。**

### B. 统计量对决（Table showdown）

同一冻结模型、同一评测数据、同一批 17 个配置，两个任务域：

| 统计量 | 分类 $r$ | 检索 $r$ |
|---|---|---|
| CG | −0.154 | −0.223 |
| τ₅ | **+0.832** | **−0.143**（失效）|
| $M(0.01)$ | **−0.996** | **−0.970** |
| $M(0.02)$ | −0.988 | −0.921 |

⇒ τ 只在分类有效、检索失效；**margin 质量两域都最强**——正好补上 τ 在 retrieval 负结果的缺口。

### C. 稳健性附录

- **半样本**：2,500 图两半的匹配 gap spread = **32.7 / 32.6**（全样本 32.7）；
- **真实配对显著性**：6.64 点、SE 0.99、95% CI **[4.70, 8.58]**、$z=6.7$；
- **τ 的模板依赖**：跨 10 模板最低 0.54，而精度变化 <5 点；
- **margin 质量的尺度依赖**：$\\varepsilon\\ge0.05$ 饱和，按曲线报告。

### D. 摘要/引言重写（摘要 **243 词**，上限 250）

摘要从"τ 跟踪精度"改为"**证明 gap 何时不可能成为指标，并给出可用证书**"；引言把"three model families"改为**五骨干**，
并把主定理与对决表前置。台账同步更新（**127/127**）。

### E. 减长（**决定不做**）

总页数 56（含附录），PAA 无页数上限；把两张表再移入附录不改变总页数、只增加维护风险，故按计划"视页数决定"不做。
"""

ENT = """> **🏁 2026-10-18 23:30 —— 最后一轮：主定理 + 统计量对决 + 稳健性 + 摘要重写（A1 **56 页**，台账 **127/127**，审计 READY/A）**
>
> **A. Theorem 1（特征化）**：合并四个命题——(i) 一阶矩统计量不可能充分；(ii) 可翻转比例 = margin 质量 $M(\\varepsilon)$；
> (iii) 下界可达（零均值扰动使 CG 恒等于不变）。一句话：**一阶矩只对类中性干涉有效，一般情形的正确证书是 margin 质量**。
>
> **B. 统计量对决（新表）**：同批 17 配置、两个任务域——CG −0.154/−0.223；**τ₅ +0.832/−0.143（检索失效）**；
> **$M(0.01)$ −0.996/−0.970**。margin 质量两域都最强，正好补上 τ 在 retrieval 的缺口。
>
> **C. 稳健性附录**：半样本 spread **32.7/32.6**（全样本 32.7）；真实配对 **6.64 [4.70, 8.58]，z=6.7**；
> τ 模板依赖（最低 0.54 vs 精度 <5 点）；margin 质量的尺度依赖（$\\varepsilon\\ge0.05$ 饱和）。
>
> **D. 摘要/引言重写**：摘要 **243 词**（≤250），叙事从"提出 τ"改为"**证明何时不可能 + 给出证书**"；引言改五骨干 + 主定理前置。
>
> **E. 减长：决定不做**（56 页含附录，PAA 无上限；移表不减少总页数）。
> 三台账 **127/127、96/96、76/76**；审计 **READY grade A：pass=61 fail=0 warn=0**。
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
    if "第 16 步" not in n:
        io.open(NOVDOC, "w", encoding="utf-8", newline="").write(n.rstrip("\n") + NOVSEC)
        print("  novelty doc appended")
    h = io.open(HANDOFF, encoding="utf-8").read()
    if "最后一轮：主定理" not in h:
        i = h.find("# 项目交接文档")
        j = h.find("\n", i)
        io.open(HANDOFF, "w", encoding="utf-8", newline="").write(h[: j + 1] + "\n" + ENT.replace("\\n", "\n") + h[j + 1:])
        print("  handoff added")
    w = io.open(WHICH, encoding="utf-8").read()
    old = "下界 + margin 质量** | 54 + 1 title page |"
    new = "下界 + margin 质量 + 主定理 + 对决表** | 56 + 1 title page |"
    print(f"  which row: {w.count(old)}")
    if w.count(old) == 1:
        io.open(WHICH, "w", encoding="utf-8", newline="").write(w.replace(old, new, 1))
    au = io.open(AUTO, encoding="utf-8").read()
    au2 = au.replace("（**54 页** + 1 页 title page + 揭示函 + 图摘要）", "（**56 页** + 1 页 title page + 揭示函 + 图摘要）")
    au2 = au2.replace("**A1 claim ledger 112/112**", "**A1 claim ledger 127/127**")
    if au2 != au:
        io.open(AUTO, "w", encoding="utf-8", newline="").write(au2)
        print("  automation handover updated")
    m = io.open(MAP, encoding="utf-8").read()
    row = ("94. 🏁 **最后一轮提升（2026-10-18 23:30）** —— **Theorem 1 特征化**（一阶矩只对类中性干涉有效；证书 = margin 质量）；"
           "**统计量对决表**：CG −0.154/−0.223、τ +0.832/−0.143、$M(0.01)$ **−0.996/−0.970**；**稳健性附录**"
           "（半样本 32.7/32.6、真实配对 CI [4.70,8.58] z=6.7）；摘要重写 **243 词**、引言改五骨干。A1 **56 页**、"
           "台账 **127/127**、审计 READY/A。E（减长）决定不做。\\n")
    if "最后一轮提升" not in m:
        anchor = "93. 🔎 **全链路一致性总检"
        idx = m.find(anchor)
        if idx >= 0:
            end = m.find("\n", idx)
            io.open(MAP, "w", encoding="utf-8", newline="").write(m[: end + 1] + row + m[end + 1:])
            print("  map row added")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
