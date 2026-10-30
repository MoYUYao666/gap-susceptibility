# -*- coding: utf-8 -*-
r"""落账：随机对照的重复分配问题 + 新流程规则（2026-10-13）。

    python tools\_p448_record_random_confound.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **🎯 2026-10-13 02:54 —— 发现"随机对照"被污染：14 个随机抽样里 4 个是规则解；`random_00`（"最低"那个）是 Γ 规则变体**
>
> ### 一、我怎么发现的（成员先发现一处，我扩成全量）
>
> `p3-allocation` 主动报：**`random_04` 与 `corner` 是同一 rank 向量**（避免重复计数）。
> 我**把全部 30 个方案按 rank 向量分组**（`tools/_p445`）：
>
> **30 个方案 → 只有 15 个不同 rank 向量、5 组重复**
>
> | rank 向量 | 重复的方案 | family | linear_obj |
> |---|---|---|---|
> | `(4,1,3,8)` | `corner` / `exact_opt` / **`random_04`** | corner / linear_true_opt / random | 24,184.6 |
> | `(4,2,2,9)` | `exp_beta_1e3` / `1e9` / `3e-4` / **`paper_0.137`** / `exp_ca_1e9` / `exp_ca_paper_0.137` / **`random_13`** | exp(×6) / random | 25,355.7 |
> | `(4,4,4,4)` | `exp_beta_0` / `1e-4` / `1e-6` / `inverse_beta_1e-4` / `uniform` | exp / uniform | 42,162.4 |
> | **`(4,6,2,6)`** | **`exp_ca_beta_1e-4`** / **`random_00`** | `exponential_eq5_cost_aware` / random | 44,504.6 |
> | `(4,15,1,1)` | `inverse_beta_1e9` / **`inverse_beta_paper_0.137`** / **`random_12`** | inverse / random | 83,973.4 |
>
> ⇒ **14 个"随机"里只有 10 个是独立的**（`random_01,02,03,05–11`）。
> ⇒ **`random_00`——那个"均值最低、说明 Γ-guided 未胜随机"的样本——其实是 `exp_ca_beta_1e-4`，
> 即 Γ 的 `cost-aware` 变体**（对应我在 `theory.tex` 新写的 `rank*_k \\propto \\exp(-\\beta|\\Gamma_k|)/c_k`）。
> ⇒ **"未胜随机"这条判据被污染了**（成员已自行把该条改写为"待独立样本重算"，
> 并**同时禁止反向翻案**——不能用它说"Γ 规则族能达到 +1103"，因为那需要 $\\beta=10^{-4}$）。
>
> ### 二、我又核了 obj 分布（`tools/_p446`），发现一条关键事实
>
> | 样本 | obj |
> |---|---|
> | `corner` | 24,185 |
> | **`exp`（Γ-guided，$\\beta=0.137$）** | **25,356** |
> | **`random_05`** | **26,527**（最接近，**高 4.6%**） |
> | `random_03/10/11/08/01` | 38,649 / 39,820 / 40,991 / 43,333 / 45,676 |
> | ~~`random_00`~~（**非随机**） | **44,505** = **10 个独立样本的中位数（44,505）** |
> | `random_09/06/02/07` | 61,311 / 62,482 / 63,653 / 64,825 |
>
> ⇒ ① **没有独立随机样本的 obj 低于 Γ-guided**；
> ② **`random_00` 恰好等于独立随机分布的中位数** ⇒ **它不是特殊样本**；
> ③ 独立随机 obj 跨度 **26.5k–64.8k**，**均值 48,727**。
>
> **⇒ 更简单的解释**：`random_00` 的 +1103 之所以突出，是因为**一个规则解正好落在随机分布的正中间**；
> **"随机分配"的合适代表是那 10 个样本的整体分布，不是 `random_00` 的单点。**
>
> ### 三、已改稿（`tools/_p447`，P3 编译 **13 页 / 0 错 / 0 未定义**）
>
> 把 *"it does not beat a random allocation of the same budget ($+1103$)"* 改为
> **标注为 provisional**，并写明：**可行集只有 15 个不同分配**、**4 个抽样与规则解重合**、
> **最低那个与规则自身的 cost-aware 变体（$\\beta=10^{-4}$）重合**、
> **另一个与 Eq.5 在论文 $\\beta=0.137$ 的解重合**、**其余 10 个才是真随机样本**（obj 26,527–64,825）、
> **被排除那个恰在样本中位数（44,505）**、**不从被污染对照下结论**。
>
> ### 四、⭐ 新增流程规则
>
> > **构造"随机对照"时，必须先验证每个随机样本与**被检验规则的所有解**不重合；
> > 并报告「可行集大小 / 抽样数 / 独立样本数 / 被排除者及其原因」。**
>
> **依据**：本阶段"把统计量当成它不成立的解释"类错误已第五次——
> ① 我"88 of 94 无归档" ② 我"2 格无来源" ③ 队友"No interior minimum"
> ④ 我与队友各一次"整体相关当单调关系" ⑤ **本次"把规则解当随机样本"**。
> **共性：对照/判据本身没有先被检验。**
>
> ### 五、进度与决定
>
> - **排期决定（我下的）**：**砍 P2、保留 P1 与 P3**
>   - **P1**（10 个独立随机样本 × 3 seed = **30 run**，≈4 h）：**能改变结论方向** → 最高优先
>   - **P3**（AdaLoRA，配置已精确对齐 $7{,}237{,}632$，≈20 min）：**R2.4/R3.9 明确点名且当前完全缺失**（**有 vs 无**的差别）
>   - **P2**（6-seed，15 run ≈2 h）：**只是让 p 值更稳**（同一结论、精度差别）→ **砍**
> - 成员**拒绝了我"挑 2 个 obj 接近的随机样本"的建议**，改为**跑全部 10 个**，
>   理由是**挑样本本身就是选择偏倚** —— **这个判断比我强，我采纳**
> - 成员的 `_p458` 判据**预先写死在 docstring**（位置：Welch + Mann-Whitney；分位；
>   方差：Levene；自动判定三档 `GAMMA_NOT_BETTER_THAN_RANDOM` /
>   `INDISTINGUISHABLE_BUT_LOWER_VARIANCE` / `INDISTINGUISHABLE`）→ **避免事后挑结论**
> - 它另修一处自身问题：`_p458` 曾把**未跑**的方案打印成 `n=0`（易误读为"跑了但没数"）
>
> ### 六、状态
>
> - **P3**：**13 页**（投稿 11）/ 0 错误 / 0 未定义；**累计修 20 处**
> - **task-9/10/11** 全部 complete｜**GPU**：`p3-downstream` 解码器 VLM sweep → 之后 `pwsh-456`（P1→P3）
> - **在 P1 回来之前**：稿中"未胜随机"保持 **provisional** 标注（**不作为结论，也不反向翻案**）
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
    if "随机对照" in t and "被污染" in t and "44,505" in t:
        print("  已记录")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("被污染", "44,505", "provisional", "可行集大小", "累计修 20 处"):
        print(f"  {'✅' if k in t2 else '🔴'} {k}")
    print(f"  HANDOFF 行数 = {len(t2.splitlines())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
