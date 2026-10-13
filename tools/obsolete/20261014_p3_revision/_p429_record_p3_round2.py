# -*- coding: utf-8 -*-
r"""落账：P3 已修 7 处 + 页数规定核实（2026-10-12）。

    python tools\_p429_record_p3_round2.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **🛠️ 2026-10-12（续 2）—— P3 累计修 7 处实质问题；页数规定已核实**
>
> ### 本轮新增修的 3 处（接上一条的 4 处）
>
> | # | 意见 | 病处 | 修法 | 脚本 |
> |---|---|---|---|---|
> | 5 | **R3.21（真症结）** | 稿件把 Random 组 `{4,16,32,64}` 与 Theory 组 `r=4` 直接比较，把 $\\sigma$ 808 vs 27（30×）归于"分配不确定性"。**但组的可训参数量 = $C\\cdot\\Sigma_k c_k$，$C$ 跨 16×** → **分配与容量两因素同时变** | 如实说明三组**容量不匹配**（$\\Sigma_k c_k = 1{,}809{,}408$；$C=4$→$7{,}237{,}632$，$C=64$→$115{,}802{,}112$，**16×**），并说明**方差不能归因于分配本身** | `_p425` |
> | 5b | **R3.20** | 图注与结果段无保留地写 *"$30\\times$ larger sd … demonstrating"* | 图注点明**与容量混淆**；结果段说明 **rank 解释其中几乎全部**（$\\eta^2(\\mathrm{rank})=0.989$）并**声明不把该比值当分配证据** | `_p426` |
> | 6 | **R2.1 / R3.10** | 正文绝对否定 *"**No $\\Gamma$ measurement, gradient alignment, or calibration is performed on LLaVA or Qwen-VL before training**"*，与 **附录 D**（*"we illustrate the $\\Gamma$-based allocation pipeline on LLaVA-1.5-7B"*）**及 Finding 4（自己给了 Qwen2-VL 逐块 Γ 数值）直接冲突** | 收窄为 **"No target-model gradient enters an allocation decision"**，并**明说 Γ 是事后诊断、从不用于选择分配**；引用附录 D 与 Finding 4 | `_p428` |
>
> ### ⚠️ 我在这一轮自己犯的 2 个错（第 15、16 个）
>
> 1. **`_p421` 引入事实错误**：我把标题句从 *"equal **parameter** budget"* 改成
>    *"equal **rank** budget ($\\Sigma_k\\mathrm{rank}_k = C = 64$)"* —— **但三组并非同一 rank 预算**
>    （稿件自己写着 Random 从 $\\{4,16,32,64\\}$ 抽）⇒ **换上的这句是另一种错**。已由 `_p425` 删除并改为如实描述。
> 2. **`_p425` 引入不准确的承诺**：我写 *"A **capacity-matched** random control … is reported in the revised version"*，
>    但 **Theory 组内部本身就跨容量**（`experiments.tex:343` 自己写着 $|\\Gamma_k|$ 从 $r=4$ 到 $r=64$
>    增长 **$16$–$26\\times$**）⇒ **"同容量 random 对照"解决不了整个问题**。已由 `_p427` 改为
>    **两个层面分别解耦**（同参数量随机分配 + 匹配分配的 rank 扫描），**且未谎称已补做**。
>
> ### 页数规定核实（穷举后的结论）
>
> 本地 **无 PRL 的 Guide for authors**（只有 Neural Networks / Neurocomputing 两份）。
> 查到 PRL 提交指南（[SIGMM Records 转载的特刊 CFP](https://records.sigmm.org/?cfp=prl-2)）：
>
> > *"The maximal length of a paper is **7 pages in the PRLetters layout** and may become
> > **8 in the revised version** if referees explicitly request significant additions."*
>
> **两点判断**：
> 1. 该条款出自**特刊** CFP，且是 **PRLetters 版面页**（`elsarticle` 双栏），**不是 IEEEtran 页**；
> 2. **实际证据**：投稿时 `manuscript.pdf` = **11 页 IEEEtran**，**已进入外审并拿到 Revise**
>    → 说明**未被因篇幅退稿**。
>
> **当前**：11 → **12 页**。增长**全部来自我的修改**（`introduction` / `related_work` / `discussion` /
> `conclusion` **零变化**；`theory` **+15.0%**、`experiments` **+13.8%**、`appendix` **+7.3%**）。
> **待办**：若后续补实验继续增页，考虑把扩充内容移入 **Supplementary Material**（当前稿件**无** supplementary 机制）。
>
> ### P3 当前状态
>
> - 编译：**12 页 / 0 错误 / 0 未定义**
> - 已修：**7 处**（理论缺口、记账口径、β 来源、容量混淆、30× 主张、零样本绝对否定、我自己的两处引入错误）
> - **待办**：`theory.tex` 两处 (A3) 同名不同义 → 需改编号
> - **待办**：33 条回复的正式文本（工作文档已就绪，待补实验数据）
> - 三成员：`p3-allocation`（**链式任务已挂 `pwsh-244`，23:45 自动起**）｜`p3-downstream`（跑 CLIP sweep，100% GPU）｜`p3-stats`（CPU 部分完成 4/6，**不抢卡**）
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
    if "P3 累计修 7 处实质问题" in t:
        print("  已记录")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("P3 累计修 7 处", "1{,}809{,}408", "No target-model gradient enters", "7 pages in the PRLetters layout", "16$–$26"):
        print(f"  {'✅' if k in t2 else '🔴'} {k}")
    print(f"  HANDOFF 行数 = {len(t2.splitlines())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
