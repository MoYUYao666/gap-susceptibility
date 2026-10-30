# -*- coding: utf-8 -*-
r"""落账：task-9 完成 + P3 的四处因果/最优主张已改 + 排补实验（2026-10-13 02:40）。

    python tools\_p443_record_p3_round5.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **⚖️ 2026-10-13 02:40 —— task-9 完成：Γ 引导分配**胜过 uniform、但输给随机**；P3 四处因果/最优主张已改**
>
> ### 一、task-9 结果（`outputs/analysis/p3_alloc_results.json`，我已核）
>
> **15 run 全部成功、0 失败**；**实测可训参数量唯一值 = 7,237,632**，`same_budget_assert_passed = true`
> （**R3.21 的"equivalent effective parameter budget"已彻底解决**）
>
> | 方案 | rank 向量 | ΔE（3 seed 原始） | 均值 ± 样本 sd | vs uniform |
> |---|---|---|---|---|
> | `uniform`（论文现 Theory 组） | {4,4,4,4} | +5543.6 / +5491.0 / +8205.7 | **+6413.4 ± 1552.3** | — |
> | **`exp`（Γ-guided，Eq.5 字面）** | **{4,2,2,9}** | +3234.9 / +2705.5 / +782.4 | **+2241.0 ± 1290.6** | t=−3.58，**p=0.024** |
> | `inverse`（**反序** sanity check） | {4,15,1,1} | +893.3 / +4225.1 / +1557.3 | **+2225.2 ± 1763.5** | t=−3.09，p=0.037 |
> | **`random_00`（同预算随机）** | {4,6,2,6} | +83.8 / +1056.8 / +2168.6 | **+1103.1 ± 1043.2** | **均值最低** |
> | `corner`（线性目标角点） | {4,1,3,8} | +4159.4 / +3518.4 / +3143.9 | +3607.2 ± 513.6 | t=−2.97，p=0.076 |
>
> ### 二、⚠️ 三条对论文不利的判读（成员主动照报）
>
> 1. ✅ **Γ-guided 3/3 seed 优于 uniform（p=0.024）** → **正面答复 R2.2**"请提供真正的逐块 Γ 引导实验"
> 2. ⚠️ **反序与正序几乎不可区分**（+2225 vs +2241）⇒ **方向性主张未获支持**
> 3. ⚠️ **同预算随机均值最低**（+1103）⇒ **Γ-guided 未胜过随机**
> 4. ⚠️ **`corner`（理论最优）劣于 `exp`** ⇒ **线性目标不是实测 ΔE 的好代理**
> 5. 功效：**n=3**、p=0.024 **未过 Bonferroni×3 的 0.0167** ⇒ 只能说"方向一致、需更多 seed"
>
> ### 三、已改的四处稿件主张（`tools/_p441`+`_p442`；**其中一处是我自己的自相矛盾**）
>
> | # | 位置 | 原主张 | 已改为 |
> |---|---|---|---|
> | **A** | `experiments.tex` §IV-E | *"…**demonstrating that Γ-based prediction eliminates allocation uncertainty**"* | **删**。改为**如实报告容量匹配比较**：$+2241\\pm1291$ vs uniform $+6413\\pm1552$（p=0.024，**未过 Bonferroni**）、**未胜随机**（$+1103\\pm1043$）、**反序同样**（$+2225\\pm1763$）⇒ **"directionally consistent，不是 dominating"** |
> | **B** | `experiments.tex` §IV-E | *"The Violation group as **causal evidence** … establishes Γ as **causal**"* | 降级为 **"consistency evidence"**；明说**不称因果**，因容量匹配对照不支持方向性解读 |
> | **C** | `experiments.tex` + `theory.tex` | *"**hard-protection configuration**"*（称该配置最优） | 改为 *"drives the **linear surrogate** to a corner"*，并**补一句**：该角点在实测能量下 $+3607\\pm514$，**劣于** Γ-guided 内点 $+2241\\pm1291$ ⇒ **是线性代理的性质，不是实测能量的性质** |
> | **D** | `experiments.tex` §IV-E | *"The rank **predicted to minimize** alignment degradation"* | 加限定：**uniform rank ≠ uniform capacity**（逐块参数差 2.65×）⇒ 该臂是 **uniform-rank 基线，不是等参数基线** |
>
> ⚠️ **A 处还有我自己 `_p426` 留下的自相矛盾**：前半句刚写 *"we do not read the ratio as
> evidence of allocation"*，后半句又写 *"demonstrating only that Γ-based prediction eliminates
> allocation uncertainty"* —— **已一并删除**（**本阶段我的第 19 个错**）。
>
> ### 四、R3.12 完整逐块 Γ 表（Qwen2-VL-2B **实测**，`p3_alloc_gamma_qwen2vl2b.json`）
>
> | 块 | $\\Gamma_k$ | 跨 seed sd | 符号一致性 | cost/rank | exp(β=.137) |
> |---|---|---|---|---|---|
> | `vision` | **−871.4** | 217.5 | **3/3 负** | 655,360 | 4 |
> | `llm_shallow` | **+5058.5** | 2040.0 | **3/3 正** | 247,296 | 2 |
> | `llm_mid` | **+4249.1** | 277.4 | **3/3 正** | 577,024 | 2 |
> | `llm_deep` | **−361.7** | 1529.0 | **1/3 正（不稳）** | 329,728 | 9 |
>
> - ⚠️ **稿件 Finding 4 称 Qwen 的逐块 Γ "uniformly negative"，2B 上实测符号混合**。
>   成员**措辞谨慎**：稿件那组数含 `merger` 块、跨 6 个数量级，**像 7B 或另一分块口径**，
>   故写作"**2B 上未复现**"而**不是**"稿件有误"——**这个处理是对的**。
> - ⚠️ 块间 $|\\Gamma|$ **只差 14.0×**，不是 $10^2$–$10^8$。
> - **CLIP 与 LLaVA 引自既有归档**（CLIP 只有 2 块非零且 LoRA 用非标准 $B\\neq0$ 初始化；LLaVA 本机 bf16 不可行）
>   ⇒ **"三者同口径逐格比较"做不到**，按各架构各自口径给全表并标注限定。
>
> ### 五、成员明确未做成（照收）
>
> 1. **AdaLoRA 训练未跑**（配置**已精确对齐** $7{,}237{,}632$，`budget_exact_match_by_cost_model = true`）
>    → **R2.4/R3.9 只完成一半**
> 2. **HALoRA / IGU-LoRA / ShapLoRA / NTK-based 全部未实现**（`peft 0.20.0` tuner 列表无 `halora`）
>    → **R3.9 点名的 5 个方法一个都没比**（**不编造数字**）
> 3. **LLaVA 未验证**（bf16 13.157 GiB > 8 GB）→ 结论仅在 **2B** 上
> 4. **只跑 5 个方案**（原计划 30），**随机分配只有 1 个抽样**
> 5. 每方案仅 **3 seed**
>
> **它的性价比排序**：① 加 3 seed（≈1.4 h）② **加 2–3 个同预算随机方案（最关键，当前只有 1 个）** ③ AdaLoRA 训练 ④ LLaVA 需云端
>
> ### 六、过程要点（成员自报）
>
> 三层预算断言（成本模型/方案/运行层）**逐位通过**；分配数学**单测 0 失败**；
> **修掉 3 个真 bug**（float32 上溢、rank 上界算错、度量非尺度无关）；
> `patch_embed` Conv3d 误伤 **+19,648 参数已剔除**；
> **batch=2 峰值 10.28 GiB、全序列 CE 17.82 GiB ⇒ 唯一可行配置 batch=1**（7.48 GiB / 1.31 s 步），
> 端到端仍溢至 9.08 GiB；**全程单进程串行，未与任何人并发**。
>
> ### 七、状态
>
> - **P3**：**13 页**（投稿时 11 页）/ 0 错误 / 0 未定义；**累计修 19 处**
> - **task-9 / task-10 / task-11 全部 complete**
> - **`p3-downstream`** 正在跑**解码器 VLM 的 rank sweep**（GPU 5.3 GiB / 39%）——R3.13/R3.14 唯一还缺的那一档
> - **待决定**：是否补跑 ① 多随机方案 ② AdaLoRA 训练 ③ 加 seed（需连续 2 h+ GPU 窗口）
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
    if "Γ 引导分配**胜过 uniform、但输给随机**" in t:
        print("  已记录")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("胜过 uniform、但输给随机", "7,237,632", "+1103", "+2225", "累计修 19 处"):
        print(f"  {'✅' if k in t2 else '🔴'} {k}")
    print(f"  HANDOFF 行数 = {len(t2.splitlines())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
