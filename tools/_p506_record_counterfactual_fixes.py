# -*- coding: utf-8 -*-
r"""落账：counterfactual 节的三处严重问题（重复 / 过度主张 / 因果自相矛盾）（2026-10-13 15:20）。

    python tools\_p506_record_counterfactual_fixes.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **🔴 2026-10-13 15:20 —— `Counterfactual Validation` 一节查出**三处严重问题**（重复 / 过度主张 / 因果自相矛盾）**
>
> ### 一、🔴 文本重复（我的 `_p480` 锚点选错）
>
> `experiments.tex` 结果段**两版并存**：旧版残留在前（含 *"and we report both **in the revised version**"*
> —— **投稿文本里不该出现"修订版"这种话**），紧接新版开头。**一个段落同时说两套数字。**
>
> ### 二、🔴 "最坏情况保护"是**过度主张**（正文自己的数据不支持）
>
> 原文称：*"$\\Gamma$ therefore **removes the catastrophic tail** of the distribution that random
> allocation cannot avoid---a **stronger guarantee** than mean improvement."*
>
> **但同稿数据反驳它**：
> | 事实 | 出处 |
> |---|---|
> | 同预算随机池（30 run）**mean +3347**，Γ-guided **+1478** | `p3_alloc_runs/main/*` |
> | **`random_03`（−1450.3）比 Γ-guided（+1477.5）更好**（差 −2928） | 同上 |
> | Γ 最坏 **+3235**（n=6）vs 池最坏 **+18575**（n=30）⇒ **小样本极值比较不可靠** | 同上 |
> | `uniform` 均值 +5047 是池中**较差者** ⇒ "最坏情况"叙事建在同预算比较之上，**而该比较已判"不可区分"** | `tools/_p474` |
>
> **⇒ 已改为**（`tools/_p505`）：
> > *"Within the six $\\Gamma$-guided runs we report, the spread is narrower than in the thirty-run
> > random pool and every run improves alignment, whereas the pool contains a run at $+18{,}575$.
> > **We deliberately stop there.** Comparing a six-run sample against a thirty-run pool makes an
> > extreme-value argument unreliable, the pool's \\emph{mean} is not worse than the rule's, and two
> > of the ten random allocations beat it outright. **A claim that the rule removes a catastrophic
> > tail is therefore not something our design can support, and we do not make it.**"*
>
> ### 三、🔴 因果自相矛盾（同节内两处冲突）
>
> - 一处：*"we **stop short of calling** the relation causal, because the capacity-matched control does
>   not support the directional reading"*
> - 另一处：*"This monotonic dose-response relationship … **establishes $\\Gamma$ as a causal factor**
>   in alignment degradation, not merely a correlated biomarker."*
>
> **⇒ 已统一为"一致性"口径**：*"is consistent with $\\Gamma$ locating where damage occurs. **We stop at
> consistency** … so **we do not claim causation**."*
>
> ### 四、✅ 现状
>
> - **编译**：**13 页 / 0 错误 / 0 未定义**
> - **复核**：`In a capacity-matched comparison` **0** ｜ `in the revised version` **0** ｜
>   `removes the catastrophic tail` **0** ｜ `establishes $\\Gamma$ as a causal factor` **0**
> - `experiments.tex` 38,214 → **37,527** 字符
>
> ### 五、⭐ 本条的意义：**过度主张往往在同一节里就能被自己的数据反驳**
>
> 本轮已修的过度主张（全部由"读数据"而非"读文字"发现）：
> 1. *"reduces allocation uncertainty by $30\\times$"* → **$\\eta^2=0.989$、同秩 sd 比 0.98**
> 2. *"equal parameter budget"* → **Random 跨 16× 容量**
> 3. *"$\Gamma$-guided beats uniform"* → **3e-4 反转、matched-loss 后落后**
> 4. *"architecture-dependent"* → **54 token 下同样转负**
> 5. *"phase transition"* → **CI 跨零、置换 $p=0.100$**
> 6. *"removes the catastrophic tail"* → **池均值优于 Γ、2/10 随机分配更好**
> 7. *"establishes $\\Gamma$ as a causal factor"* → **与同节"we stop short of causal"冲突**
>
> **共性**：**主张的强度超过了设计的判别力**（$n=6$ vs $n=30$、3 档 lr、单一协议）。
> **⇒ 与既有三条规则并列的判据**：
> > **凡写"消除/保证/建立因果/显著优于"，先问：这个设计能区分该主张与其反面吗？**
> > **若不能，改写为"一致性"或"未检出差异"。**
>
> ### 六、状态
>
> - **P3 稿件**：**13 页** / 0 错 / 0 未定义；**累计修 42 处**
> - **摘要**：243 词 ≤ 250 ✅
> - **PRL 硬约束**：双栏 ≤7 页 ⇒ **仍需从 13 页压缩**（`experiments` 散文仍是最大块）
> - **剩余**：① 压到 ≤7 页 ② **33 条回复信正式文本** ③ 修订包重新生成
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
    if "removes the catastrophic tail" in t:
        print("  已记录")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("removes the catastrophic tail", "in the revised version", "do not claim causation",
              "主张的强度超过了设计的判别力", "累计修 42 处"):
        print(f"  {'✅' if k in t2 else '🔴'} {k}")
    print(f"  HANDOFF 行数 = {len(t2.splitlines())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
