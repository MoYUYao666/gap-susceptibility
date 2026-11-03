# -*- coding: utf-8 -*-
r"""落账：摘要重写（清掉与正文矛盾的主张）（2026-10-13 13:20）。

    python tools\_p489_record_abstract.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **🚨 2026-10-13 13:20 —— 开做页数压缩时**先抓到一个更严重的问题**：摘要仍含 6 处与正文矛盾/已被撤回的主张**
>
> ### 一、我核出的摘要-正文矛盾（全都源于"正文改了 26 处、摘要没跟着改"）
>
> | # | 摘要现状 | 正文现状 | 严重度 |
> |---|---|---|---|
> | 1 | *"reduces uncertainty by **$30\\times$**"* | **正文已删**：*"the $30\\times$ ratio **must not** be read as $\\Gamma$ reducing allocation uncertainty"*（$\\eta^2=0.989$、同秩 sd 比 0.98、Welch $p=0.47$） | 🔴 **直接矛盾** |
> | 2 | *"the **unique** scalar (up to positive scaling) satisfying the axioms"* | 正文：**R3 不足以推出唯一性**，需**新增 R3′**，且**给了反例 $\\|x\\|^2$** | 🔴 |
> | 3 | *"an alignment **phase transition** at critical rank $r_c\\in[5,6]$"* | 正文：**降级为 "location is bracketed"**（CI 跨零、置换 $p=0.100$、MDE $d=2.95$ vs 实测 $1.95$） | 🔴 |
> | 4 | *"190 runs (181 sweep + 9 counterfactual) across 2 architectures and 4 sample sizes"* | 实验协议已换；现有计数 **79 + 43 + 4 = 126**，旧 190 含 $E_2$/`extra`/`sweep` | 🔴 |
> | 5 | 未提 **blank 非中性**、**AdaLoRA 更优**、**"分配不含目标模型梯度"的定位** | 正文已有三个新增小节 | ⚠️ 缺失 |
> | 6 | 未提 **$\\beta$ 来源更正**、**rank-vs-参数记账** | 正文已改 | ⚠️ 缺失 |
>
> **⇒ 这是"改了正文没改摘要"——本项目"数字随数据更新、旧值必须被替换而非留在别处"的又一次实例。**
> **⇒ 若提交，审稿人只需对比摘要与正文就能发现我们自己的结论已被推翻而未更新。**
>
> ### 二、✅ 摘要**三轮重写**（334 → 291 → 281 → **243 词**，PRL 上限 **250**）
>
> | 轮 | 词数 | 做了什么 |
> |---|---|---|
> | `_p485` | **334** | 清掉 $30\\times$ 等矛盾主张 + **写入对我方不利的三条结论** |
> | `_p486` | **291** | 压措辞 |
> | `_p487` | **281** | 五项要求只留关键词 |
> | **`_p488`** | **243** | 删可移入正文的解释性从句；**不动任何实质结论** |
> | `_p489`（本轮） | **243** | 把 `Section~III` 交叉引用改为自含表述（摘要不宜引用章节号） |
>
> **必须保留且已保留的五条（本轮修订的核心价值）**：
> ① **优势随 lr 反转 / 匹配 loss 后消失**（*"we report a zero-shot heuristic, not an optimum"*）；
> ② **与同预算随机不可区分**；③ **AdaLoRA 更优**（*"reaches lower alignment energy than any of our arms"*）；
> ④ **$r_c$ 属协议而非模型**；⑤ **blank 非中性（论文操作点 3×）**。
>
> **并写入两处理论限定**：**additivity 是**假设**而非推论**（反例 $\\|\\nabla E\\|^2$）、
> **$\\Gamma$ 在给定该假设下唯一 up to 正缩放**。
>
> **编译**：P3 `main.pdf` = **14 页 / 0 错误 / 0 未定义**。
>
> ### 三、下一步：页数压缩（PRL 硬约束 **双栏 ≤7 页**）
>
> **量化方案（`tools/_p473`，合计 77,139 字符 ⇒ 目标 ≈38,500，约减半）**：
>
> | 节 | 字符 | 动作 |
> |---|---|---|
> | **appendix** | 8,520 | **整节移入 Supplementary** |
> | **experiments** | **35,068** | 保留主表与结论；逐 run 表 / 分辨率曲线 / $E_0$ 预算曲线 / 功效算式移出 |
> | **theory** | 17,737 | 保留定理与 Corollary 陈述；**证明移入补充** |
> | discussion | 5,021 | 12 条限制**表格化** |
> | introduction / related_work / conclusion | 4,706 / 3,387 / 2,700 | 标准压缩 |
>
> **⇒ 需要新建 `supplementary.tex`（Guide 明确鼓励补充材料，并要求正文引用）。**
>
> ### 四、状态
>
> - **三个实验组全部收口**（task-9 / task-10 / task-11）
> - **P3 稿件**：**14 页** / 0 错 / 0 未定义；**累计修 27 处**（本轮摘要为第 27 处）
> - **摘要**：**243 词 ≤ 250** ✅
> - **PRL 硬约束**：**双栏 ≤7 页** ⇒ **压缩 + 新建 Supplementary（进行中）**
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not a.apply:
        print("  （预演）")
        return 0
    hp = REPO / "HANDOFF.md"
    t = io.open(hp, encoding="utf-8").read()
    if "摘要仍含 6 处与正文矛盾" in t:
        print("  已记录")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("摘要仍含 6 处与正文矛盾", "334 → 291 → 281 → **243", "zero-shot heuristic, not an optimum", "累计修 27 处", "新建 `supplementary.tex`"):
        print(f"  {'✅' if k in t2 else '🔴'} {k}")
    print(f"  HANDOFF 行数 = {len(t2.splitlines())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
