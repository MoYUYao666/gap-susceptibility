# -*- coding: utf-8 -*-
r"""落账：P2 完成 + 分配比较段定稿 + 两条翻转 + PRL 7 页硬约束（2026-10-13 10:03）。

    python tools\_p476_record_p2_done.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **📐 2026-10-13 10:03 —— P2 完成（6 seed）：两条判读**翻转**；分配比较段**定稿**；并确认 **PRL 7 页硬约束****
>
> ### 一、🔴 收到 PRL 官方 Guide（操作者提供）—— 确认一条硬约束
>
> **`docs/guides/Guide for authors - Pattern Recognition Letters - ISSN 0167-8655.pdf`**
> （提取文本 `docs/guides/_prl_guide.txt`，穷举检索 `page/length/word` 关键词）
>
> > **Mandatory Submission Requirements 第 1 条**：
> > *"The manuscript should be in **double column format** and should **not exceed 7 pages**.
> > The 7 pages limit includes **all materials** e.g. narrative, figures, tables, references, etc."*
> >
> > 第 4 条：Authorship Confirmation 必须上传，**否则 AUTOMATIC REJECTION**
> > 补充材料：*"We **encourage** the use of supplementary materials…"*
> > 格式：**Word 单栏；LaTeX 允许双栏**
>
> **⇒ 我此前引用的 [SIGMM 转载的特刊 CFP]**（"7 pages in the PRLetters layout"）**方向对、出处错**；
> **现在是官方强制条款且无例外。**
>
> **⚠️ 现状：`main.pdf` = 14 页（投稿时 11 页，也已超限但仍进了外审 ⇒ 实际执行可能较宽）。**
>
> **压缩方案（`tools/_p473` 量化，合计 77,139 字符 ⇒ 目标 ≈38,500，约减半）**：
>
> | 节 | 字符 | 动作 |
> |---|---|---|
> | **appendix** | 8,520 | **整节移入 Supplementary** |
> | **experiments** | **35,068** | 保留主表与结论；逐 run 表 / 分辨率曲线 / $E_0$ 预算曲线 / 功效算式移出 |
> | **theory** | 17,737 | 保留定理与 Corollary 陈述；**证明移入补充** |
> | discussion | 5,021 | 12 条限制**表格化** |
> | introduction / related_work / conclusion | 4,706 / 3,387 / 2,700 | 标准压缩 |
>
> **⇒ 最后阶段的工作是"新建 Supplementary + 重排正文"，不是单纯压缩。截止 Nov 02，时间足够。**
>
> ### 二、P2 完成（57 run，全部逐位同预算 7,237,632，0 失败）
>
> | 方案 | n | 均值 | sd | 3-seed → 6-seed |
> |---|---|---|---|---|
> | **`exp`（Γ-guided）** | 6 | **+1477.5** | 1563.3 | +2241.0 → **+1477.5** |
> | `uniform` | 6 | **+5047.5** | 1899.9 | +6413.4 → **+5047.5** |
> | `corner` | 6 | +2343.9 | 2426.1 | +3607.2 → +2343.9 |
> | `inverse`（反序） | 6 | +2470.2 | **4111.2** | +2225.2 → +2470.2 |
> | 独立随机池 | 30 | +3347.4 | 4771.2 | 不变 |
>
> **Welch 检验（我**独立实现 t 分布双侧 p**，非采信）**：
> - **`exp` vs `uniform`：t=−3.554, df=9.6, p=0.0055** ✅ **过 Bonferroni×3（0.0167）**
> - `corner` vs `uniform`：p=0.0587 ❌
> - **`inverse` vs `uniform`：p=0.2057** ❌ ← **3-seed 时是 0.037**
>
> ### 三、⭐ 两条判读**翻转**
>
> 1. **"Γ-guided 优于 uniform" 变**更强**：p 从 0.024 → **0.0055**，**且这次过了多重比较校正**
> 2. **"反序也优于 uniform" 被推翻**（p=0.037 → **0.2057**）⇒ **那是小样本假象**
>    ⇒ **削弱了我先前"方向性主张未获支持"的证据基础** —— 现在只能说
>    **反序与正序的差别未检出**，**不能说"反序同样有效"**
>
> ### 四、⭐ 噪声结构的决定性表述（我核出且成员采纳）
>
> | 量 | 值 |
> |---|---|
> | 池的**组间 sd**（10 个方案均值之间） | **3,010.1** |
> | 池的**组内 sd 中位数**（方案内 seed sd） | **3,196.6** |
> | 混合池 sd（**不应直接比**） | 4,771.2 |
> | **Levene（Γ-guided vs 组内残差）** | W=1.916, **p=0.1753** |
>
> **⇒ 组内(3197) > 组间(3010)** ⇒ **噪声主要来自"同一分配内的 seed 波动"，而非"不同分配之间"。**
> **⇒ 按我**预先写定**的判据（`Levene p < 0.05` 且 sd 更小才允许写"方差更小"），
> 判据不满足 ⇒ 一律写"不可区分"、不提方差 ✅ 成员已照此执行。**
>
> ### 五、所需 n 更新为 **11–28**（σ 与 Δ 都变了）
>
> `K = 2(z+z)² = 15.6978`，`Δ = 3570.1`（6-seed `exp` vs `uniform`）：
> σ=3010→**11.2**；σ=3197→**12.6**；σ=4111→**20.8**；σ=4771→**28.0**
> **⇒ 6 seed 仍不足（离 11–28 差约 2–5 倍）⇒ 判定不变。** 出处改为**逐 run glob**。
>
> ### 六、✅ 分配比较段**已定稿**（`tools/_p475`，P3 编译 **14 页 / 0 错 / 0 未定义**）
>
> 替换了先前的 provisional 段，写入：
> - **6-seed 的 `exp` vs `uniform`：$+1478\\pm1563$ vs $+5048\\pm1900$，Welch $p=0.0055$，过 Bonferroni**
> - **随机池不分离**：池 $+3347\\pm4771$，Γ-guided 在 **47 分位**，**10 个随机分配里 3 个均值更低**
> - **反序不再显著**（$+2470\\pm4111$，$p=0.21$），并**显式记录"3-seed 时的 $p=0.037$ 是小样本假象"**
> - **诚实的窄结论**：*"**this** allocation beats the uniform-rank baseline, but we cannot show that it
>   is the **ordering** that does the work"*
> - **功效上限**：*"would need roughly $11$ to $28$ seeds per arm, of which we report six"*
> - **可无条件主张的那一条**：*"the noise … is dominated by seed-to-seed variation **within** a fixed
>   allocation rather than by differences **between** allocations"*
>
> ### 七、状态
>
> - **P1 ✅ / P2 ✅ / P3(AdaLoRA) ✅**（AdaLoRA **lr 实验**进行中，判据 `loss_last < 0.9×loss_first`）
> - **P3 稿件**：**14 页** / 0 错 / 0 未定义；**累计修 24 处**
> - **剩余两块**：**① 新建 Supplementary + 压到 ≤7 页**（PRL 硬约束）**② 33 条回复信正式文本**
> - **修订包**：`SUBMISSION/P3_PRL_revision/`（12 文件 / 754 KB，**待压缩后重新生成**）
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
    if "PRL 7 页硬约束" in t:
        print("  已记录")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("PRL 7 页硬约束", "0.0055", "0.2057", "3,196.6", "不是单纯压缩"):
        print(f"  {'✅' if k in t2 else '🔴'} {k}")
    print(f"  HANDOFF 行数 = {len(t2.splitlines())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
