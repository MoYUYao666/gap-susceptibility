# -*- coding: utf-8 -*-
r"""落账：AdaLoRA lr 实验排队 + 方差判据预先写死 + 规则转达（2026-10-13 08:08）。

    python tools\_p468_record_variance_criterion.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **📏 2026-10-13 08:08 —— AdaLoRA lr 实验已排队；**方差判据预先写死**（避免事后协商）；"只增不改"规则已转达两成员**
>
> ### 一、AdaLoRA lr 实验：已挂到 P2 之后的链上
>
> **队列**：`P2（进行中）→ AdaLoRA lr ∈ {1e-3, 3e-4} × seed42 → 报告`
> **判据（预先写死，避免事后挑结论）**：**`loss_last < 0.9 × loss_first`（降幅 >10%，与 GFAP 侧同量级）视为"真训练"**；
> - 某 lr 达到 ⇒ **再补 seed**，并作为 R2.4/R3.9 的**真正对比**
> - **3 个 lr 都达不到 ⇒ 如实报"AdaLoRA 在我们协议下未能有效训练"，并把它作为**结论**而非借口**
>
> **成本 ≈18 min**（2 lr × 1 seed × 9 min）；**独立 tag**（`p3_alloc_runs/adalora_lr<lr>__seed42.json`），
> **不污染已有 5e-5 的结果**。
>
> ### 二、⭐ 方差判据**预先写死**（我下的，避免 P2 回来后纠缠）
>
> > **只有当 `Levene p < 0.05` 且 Γ-guided 的 sd 点估计小于池 sd 时，才允许写"方差更小"**；
> > 否则一律写"**不可区分**"，**不得提及方差**。
>
> **三条理由（都要写进报告）**：
> 1. **随机池 sd 是混合量**：池 = **10 方案 × 3 seed**，其 sd **同时含组间与组内**；
>    而 `exp` 的 sd 是**单一方案的组内 sd** —— **两者不是同一个量，直接比大小没有意义。**
>    ⇒ **必须同时给出「池的组间 sd（10 个方案均值之间的 sd）」与「组内 sd（方案内 seed sd 的中位数）」，
>    并说清比的是哪一个。**
> 2. **池内 7/30 负值 ⇒ 近似双峰** ⇒ **方差齐性检验对双峰分布不适用**（Levene 假设大致单峰/同形）
> 3. **Γ-guided 仅 n=3（P2 后 n=6）** ⇒ **6 点 sd 仍不稳**（本项目已两次踩到"小数样本 sd 不可信"）
>
> **⇒ 已要求 P2 的表额外给两列**：**池的组间 sd** 与 **池的组内 sd 中位数**。
>
> ### 三、成员的前瞻提醒（我采纳并加严）
>
> 它主动说：*"若 6-seed 的 `exp` sd 明显小于当前的 1290.6，那'方差'那条仍不能算结论
> （因为随机池 sd 是 4771，且池内 7/30 负值 ⇒ 双峰），**我不会因为 σ 变小就改口说'方差更小'**
> —— 除非 Levene 显著且你同意。"*
> **⇒ 我补充的理由**：即使 `exp` 的组内 sd 真的小，**池的组间 sd 可能才是该比的量**，
> **而那个值可能并不大**。
>
> ### 四、✅ "只增不改"规则已转达（我发给 `p3-downstream`）
>
> 要求它**自查 `p3d_summary.json` / `p3d_manifest.json` 是否会被后续调用重写**；
> 若是，**报告引用改指逐 run 的 `p3d_clip_ranksweep.json :: runs[*]`**，或注明"该 summary 生成于某时刻、后续会重写"。
> 并提醒：它此前**已删掉一个"无后缀的重复归档"**（那次判断正确）⇒ **同类"多份产物指向同一事实"请一并梳理**。
> 引用纪律：**必须带 `split` 名与 n**（它已做到）。
>
> ### 五、转达两处互相纠正的结论（我确认）
>
> - `p3-allocation` 说 `p3-downstream` 的归档"中文乱码" → **按字节核是合法 UTF-8**，是**读侧 GBK** 问题。**后者对。**
> - 说 `E_train_epochs`(4) vs `loss_epochs`(3) 不一致 → **设计如此**。**后者对。**
> **两条都是"用字节/结构证据纠正对方"，视为正面贡献**；`p3-allocation` 也已把两条记成自我更正。
>
> ### 六、我给 `p3-downstream` 的一条归属纪律（关于 3.09×）
>
> 报告里必须写明：**谁测的**（它，`tools/_p472`）｜**什么预算**（`max_pixels=802816`，
> 实测 **595.25 token**，≈论文 576）｜**哪批样本**（`train_sel`，**n=16**，与训练档同批）｜
> **哪个口径**（`mean||mean(h_vis)−mean(h_lang)||²` 最后一层）｜
> **论文自己未报该差值**（它只跑 blank）⇒ **不得写成"论文的 gap 是 3.09×"**
>
> **并明确告诉它：576 档不需要补 seed** —— 因为 **$E_0$ 前向是确定性的、无 seed 噪声**（它自己的关键洞察），
> **单次测量即为精确值**。**这条洞察的价值正是"省掉了重复"。**
>
> ### 七、状态
>
> - **P1 ✅ 完成（30/30）**｜**P3（AdaLoRA）✅ 跑完**（不可比）｜**P2 🔄 07:57 起，≈09:50 结束**（12 个新 run）
> - 随后 **AdaLoRA lr 两跑 ≈18 min**
> - **P3 稿件**：**14 页** / 0 错 / 0 未定义；**累计修 23 处**
> - **修订包**：`SUBMISSION/P3_PRL_revision/`（12 文件 / 754 KB）
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
    if "方差判据**预先写死**" in t:
        print("  已记录")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("方差判据", "Levene p < 0.05", "只增不改", "组间 sd", "0.9 × loss_first"):
        print(f"  {'✅' if k in t2 else '🔴'} {k}")
    print(f"  HANDOFF 行数 = {len(t2.splitlines())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
